import os
import time
import json
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# YouTube OAuth scopes
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# ==========================================
# 1. YouTube Data API Publishing
# ==========================================
def get_youtube_service(client_secrets_path: str = "client_secrets.json", token_path: str = "youtube_oauth_token.json"):
    """
    Sets up OAuth2 flow to authenticate with YouTube API.
    Loads existing tokens or runs local auth server to get credentials.
    """
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, YOUTUBE_SCOPES)
        except Exception as e:
            print(f"Error loading saved token: {e}")
            creds = None

    # If credentials don't exist, are invalid, or expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh YouTube token: {e}")
                creds = None
        
        # If refreshing fails or no creds exist
        if not creds:
            if not os.path.exists(client_secrets_path):
                raise FileNotFoundError(
                    f"Google client_secrets.json was not found at {client_secrets_path}.\n"
                    "Please download it from Google Cloud Console under APIs & Services -> Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, YOUTUBE_SCOPES)
            creds = flow.run_local_server(
                port=0, 
                authorization_prompt_message="Please visit this URL to authorize the app:",
                success_message="Authorization complete! You can close this window."
            )
            
        # Save token for subsequent runs
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_path: str, title: str, description: str, 
                      privacy_status: str = "private", 
                      client_secrets_path: str = "client_secrets.json",
                      token_path: str = "youtube_oauth_token.json",
                      status_callback=None):
    """
    Uploads a local video to YouTube as a Short/Standard video.
    """
    if status_callback:
        status_callback("Authenticating with Google OAuth...")
    
    youtube_service = get_youtube_service(client_secrets_path, token_path)
    
    body = {
        "snippet": {
            "title": title[:100],  # Title max limit is 100 characters
            "description": description,
            "categoryId": "27"  # Education category
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(
        video_path, 
        mimetype="video/mp4", 
        chunksize=1024*1024*5,  # 5MB chunks
        resumable=True
    )
    
    request = youtube_service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    if status_callback:
        status_callback("Starting video upload...")
        
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and status_callback:
            progress = int(status.progress() * 100)
            status_callback(f"Uploading to YouTube: {progress}% complete...")
            
    video_id = response.get("id")
    if status_callback:
        status_callback(f"Successfully uploaded to YouTube! Video ID: {video_id}")
        
    return f"https://www.youtube.com/watch?v={video_id}"

# ==========================================
# 2. Temporary Video Hosting (for Instagram)
# ==========================================
def upload_video_to_temp_host(video_path: str, status_callback=None) -> str:
    """
    Uploads video to tmpfiles.org to generate a public download URL
    needed by Instagram's Graph API.
    """
    if status_callback:
        status_callback("Uploading video to temporary hosting (tmpfiles.org) for Instagram access...")
        
    url = "https://tmpfiles.org/api/v1/upload"
    
    with open(video_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files, timeout=120)
        
    if response.status_code == 200:
        res_json = response.json()
        view_url = res_json.get("data", {}).get("url")
        if not view_url:
            raise KeyError("No URL found in tmpfiles response.")
        # Translate the view URL into a direct file download URL
        # e.g., https://tmpfiles.org/12345/file.mp4 -> https://tmpfiles.org/dl/12345/file.mp4
        direct_url = view_url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
        if status_callback:
            status_callback(f"Direct temp URL generated: {direct_url}")
        return direct_url
    else:
        raise RuntimeError(f"Temporary file upload failed: {response.status_code} - {response.text}")

# ==========================================
# 3. Instagram Graph API Publishing
# ==========================================
def publish_to_instagram(video_path: str, caption: str, ig_user_id: str, access_token: str, status_callback=None):
    """
    Publishes a video to Instagram Reels.
    
    Steps:
    1. Upload video to tmpfiles.org.
    2. Request Instagram container creation using public video URL.
    3. Poll Instagram API until video finishes processing.
    4. Trigger publish command for the media container.
    """
    if not ig_user_id or not access_token:
        raise ValueError("Instagram User ID and Page Access Token are required.")
        
    # Step 1: Upload to temp public hosting
    public_url = upload_video_to_temp_host(video_path, status_callback)
    
    # Step 2: Initialize media container creation
    if status_callback:
        status_callback("Creating Instagram Reels media container...")
        
    container_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": public_url,
        "caption": caption,
        "access_token": access_token
    }
    
    response = requests.post(container_url, data=payload, timeout=30)
    res_data = response.json()
    
    if response.status_code != 200 or "id" not in res_data:
        raise RuntimeError(f"Instagram Container Creation failed: {res_data}")
        
    container_id = res_data["id"]
    if status_callback:
        status_callback(f"Container created (ID: {container_id}). Waiting for Instagram to process the video...")
        
    # Step 3: Poll Container status
    check_url = f"https://graph.facebook.com/v19.0/{container_id}"
    params = {
        "fields": "status_code,status",
        "access_token": access_token
    }
    
    # Instagram encoding and fetching can take 30 to 120 seconds
    max_retries = 30
    retry_delay = 10
    
    for i in range(max_retries):
        time.sleep(retry_delay)
        poll_response = requests.get(check_url, params=params, timeout=15)
        poll_data = poll_response.json()
        
        status_code = poll_data.get("status_code")
        status_text = poll_data.get("status", "Unknown")
        
        if status_callback:
            status_callback(f"Check status: {status_code} ({status_text}) - Attempt {i+1}/{max_retries}")
            
        if status_code == "FINISHED":
            break
        elif status_code == "ERROR":
            raise RuntimeError(f"Instagram video processing failed: {poll_data}")
    else:
        raise TimeoutError("Instagram video processing timed out on the Graph API side.")
        
    # Step 4: Publish the container
    if status_callback:
        status_callback("Instagram processing finished! Publishing Reel now...")
        
    publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": access_token
    }
    
    pub_response = requests.post(publish_url, data=publish_payload, timeout=30)
    pub_data = pub_response.json()
    
    if pub_response.status_code != 200 or "id" not in pub_data:
        raise RuntimeError(f"Reel publishing failed: {pub_data}")
        
    post_id = pub_data["id"]
    if status_callback:
        status_callback(f"Successfully published Reel! Reel ID: {post_id}")
        
    # We return the direct post link format if possible, otherwise just confirmation
    return f"https://www.instagram.com/p/{post_id}"
