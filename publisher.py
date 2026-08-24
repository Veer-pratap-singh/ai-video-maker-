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
# 3. Instagram Direct Publishing (using instagrapi)
# ==========================================
def publish_to_instagram(video_path: str, caption: str, username: str, password: str, status_callback=None):
    """
    Publishes a video to Instagram Reels using instagrapi (username/password).
    """
    if not username or not password:
        raise ValueError("Instagram Username and Password are required.")
        
    if status_callback:
        status_callback("Initializing Instagram Client...")
        
    try:
        from instagrapi import Client
    except ImportError:
        raise ImportError("instagrapi library not found. Please run 'pip install instagrapi'.")
        
    cl = Client()
    
    # Optional: Cache login session locally to avoid logging in on every run
    session_file = "instagram_session.json"
    session_loaded = False
    if os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            cl.login(username, password)
            session_loaded = True
            if status_callback:
                status_callback("Logged in using cached session settings.")
        except Exception as e:
            if status_callback:
                status_callback(f"Cached session expired or invalid: {e}. Logging in fresh...")
                
    if not session_loaded:
        if status_callback:
            status_callback(f"Logging in to Instagram as {username}...")
        try:
            cl.login(username, password)
            cl.dump_settings(session_file)
        except Exception as e:
            raise RuntimeError(f"Instagram Login Failed: {e}")
            
    if status_callback:
        status_callback("Uploading Reel video to Instagram (this might take a few moments)...")
        
    try:
        # instagrapi handles video processing/uploading internally
        media = cl.video_upload(
            video_path,
            caption=caption,
            reel=True
        )
        media_id = media.id
        if status_callback:
            status_callback(f"Successfully uploaded Reel! Media ID: {media_id}")
        return f"https://www.instagram.com/reel/{media.code}/"
    except Exception as e:
        raise RuntimeError(f"Reels upload failed: {e}")
