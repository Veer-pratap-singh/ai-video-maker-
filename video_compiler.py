import os
import re
import urllib.request
import requests
import asyncio
import edge_tts
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
# Monkey-patch PIL.Image.ANTIALIAS for compatibility of MoviePy 1.0.3 with Pillow 10+
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import numpy as np
from moviepy.editor import (
    VideoFileClip, 
    AudioFileClip, 
    CompositeAudioClip, 
    concatenate_videoclips,
    vfx
)

# Ensure directories exist
os.makedirs("temp", exist_ok=True)
os.makedirs("downloads", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Font caching URL (Montserrat-Bold) for premium visuals
FONT_PATH = os.path.join("temp", "Montserrat-Bold.ttf")
FONT_URL = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf"

def download_font_if_needed():
    """Downloads a premium Montserrat font for text styling if not locally cached."""
    if not os.path.exists(FONT_PATH):
        try:
            print("Downloading premium Montserrat font...")
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(FONT_URL, headers=headers, timeout=20)
            response.raise_for_status()
            with open(FONT_PATH, "wb") as f:
                f.write(response.content)
            print("Font downloaded successfully.")
        except Exception as e:
            print(f"Error downloading font, will fallback to system fonts: {e}")

# Call font downloader
download_font_if_needed()

# ==========================================
# 1. TTS Generation
# ==========================================
async def _async_generate_edge_tts(text: str, voice: str, output_path: str):
    """Internal helper to generate TTS using edge-tts."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_tts(text: str, output_path: str, voice: str = "en-US-EmmaMultilingualNeural"):
    """
    Generates realistic speech narration from text.
    Uses edge-tts (free Microsoft voices) and falls back to gTTS if it fails.
    """
    # Clean text of markdown and brackets
    clean_text = re.sub(r'\[.*?\]', '', text).strip()
    try:
        asyncio.run(_async_generate_edge_tts(clean_text, voice, output_path))
        print(f"Generated TTS (Edge-TTS) -> {output_path}")
    except Exception as e:
        print(f"Edge-TTS failed ({e}). Falling back to gTTS...")
        try:
            tts = gTTS(text=clean_text, lang='en', slow=False)
            tts.save(output_path)
            print(f"Generated TTS (gTTS Fallback) -> {output_path}")
        except Exception as ge:
            raise RuntimeError(f"All TTS generation methods failed: {ge}")

# ==========================================
# 2. Pexels Stock Media Fetcher
# ==========================================
def search_pexels_videos(query: str, api_key: str, limit: int = 5):
    """
    Searches Pexels for vertical or high-quality landscape videos matching a query.
    """
    if not api_key:
        print("No Pexels API Key provided.")
        return []
    
    headers = {"Authorization": api_key}
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page={limit}&orientation=portrait"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            videos = response.json().get("videos", [])
            # If no portrait videos, search standard layout
            if not videos:
                url_any = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page={limit}"
                response_any = requests.get(url_any, headers=headers, timeout=15)
                if response_any.status_code == 200:
                    videos = response_any.json().get("videos", [])
            return videos
        else:
            print(f"Pexels API Error ({response.status_code}): {response.text}")
            return []
    except Exception as e:
        print(f"Pexels Search Exception: {e}")
        return []

def download_video_asset(video_data: dict, filename: str) -> str:
    """
    Extracts the best MP4 resolution file from a Pexels video payload and downloads it.
    """
    video_files = video_data.get("video_files", [])
    if not video_files:
        raise ValueError("No video files found in stock data payload.")
    
    # Sort files to find best matches: prefer HD (1920x1080 or 1080x1920) or Mobile versions
    selected_file = None
    
    # Try to find a vertical version first
    for f in video_files:
        w, h = f.get("width") or 0, f.get("height") or 0
        if w == 1080 and h == 1920:
            selected_file = f
            break
            
    # Try finding typical full HD landscape
    if not selected_file:
        for f in video_files:
            w, h = f.get("width") or 0, f.get("height") or 0
            if (w == 1920 and h == 1080) or (f.get("quality") == "hd"):
                selected_file = f
                break
                
    # Fallback to the first video file with link
    if not selected_file and video_files:
        selected_file = video_files[0]
        
    if not selected_file or not selected_file.get("link"):
        raise ValueError("No valid video link found in stock assets.")
        
    download_url = selected_file["link"]
    output_path = os.path.join("downloads", filename)
    
    print(f"Downloading stock footage from: {download_url} -> {output_path}")
    response = requests.get(download_url, stream=True, timeout=30)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    return output_path

# ==========================================
# 3. Subtitle Engine (PIL text overlay)
# ==========================================
def draw_subtitle_on_frame(frame: np.ndarray, text: str, width: int = 1080, height: int = 1920) -> np.ndarray:
    """
    Draws text overlay on a video frame using PIL.
    Designed for maximum legibility with thick stroke outlines.
    Runs self-contained without needing ImageMagick.
    """
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    
    # Load Font
    try:
        font = ImageFont.truetype(FONT_PATH, 55)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", 55)
        except Exception:
            font = ImageFont.load_default()
            
    # Wrap text to fit 9:16 layout (within 900px width limit)
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        line_text = " ".join(current_line)
        bbox = draw.textbbox((0, 0), line_text, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width > width - 180:  # 90px padding on each side
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
        
    # Draw Subtitle lines in lower third (around 65% height)
    y_start = int(height * 0.65)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        x_pos = (width - line_width) // 2
        
        # Draw stroke outline for contrast
        stroke = 4
        for dx in range(-stroke, stroke + 1):
            for dy in range(-stroke, stroke + 1):
                if dx != 0 or dy != 0:
                    draw.text((x_pos + dx, y_start + dy), line, font=font, fill=(0, 0, 0))
                    
        # Draw primary text (Vibrant yellow)
        draw.text((x_pos, y_start), line, font=font, fill=(255, 223, 0))
        y_start += line_height + 20
        
    return np.array(img)

# ==========================================
# 4. Video Compiler Pipeline
# ==========================================
def compile_video(scenes: list, bg_music_path: str, output_name: str, 
                  voice: str = "en-US-EmmaMultilingualNeural", bg_music_volume: float = 0.15,
                  status_callback=None):
    """
    Stitches TTS audio, stock assets, and background music into a polished vertical (9:16) MP4 video.
    
    scenes: list of dicts: [
        {"text": "Subtitles to show/narrate", "video_path": "local_path_or_downloaded.mp4"}
    ]
    """
    clips = []
    temp_files = []
    
    try:
        for idx, scene in enumerate(scenes):
            if status_callback:
                status_callback(f"Processing scene {idx + 1}/{len(scenes)}...")
                
            text = scene.get("text", "")
            video_path = scene.get("video_path")
            
            if not video_path or not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found or empty for scene {idx + 1}.")
                
            # Generate narration audio
            tts_path = os.path.join("temp", f"tts_scene_{idx}.mp3")
            generate_tts(text, tts_path, voice=voice)
            temp_files.append(tts_path)
            
            # Load assets into MoviePy
            audio_clip = AudioFileClip(tts_path)
            video_clip = VideoFileClip(video_path)
            
            # Setup duration matching
            duration = audio_clip.duration
            
            # Crop/Resize video to vertical 9:16 layout
            orig_w, orig_h = video_clip.size
            target_w, target_h = 1080, 1920
            
            # Compute scaling factor to fill height
            scale_factor = target_h / orig_h
            resized_clip = video_clip.resize(scale_factor)
            new_w, new_h = resized_clip.size
            
            # Center crop to 1080 width
            x1 = (new_w - target_w) / 2
            cropped_clip = resized_clip.crop(x1=x1, y1=0, x2=x1 + target_w, y2=target_h)
            
            # Loop clip if stock footage is shorter than audio narration
            if cropped_clip.duration < duration:
                # Loop video
                loop_factor = int(np.ceil(duration / cropped_clip.duration))
                loop_clip = cropped_clip.loop(n=loop_factor)
                cropped_clip = loop_clip.subclip(0, duration)
            else:
                cropped_clip = cropped_clip.subclip(0, duration)
                
            # Attach audio to the trimmed video scene
            scene_clip = cropped_clip.set_audio(audio_clip)
            
            # Burn subtitles on the frame
            burned_clip = scene_clip.fl_image(lambda f, t=text: draw_subtitle_on_frame(f, t))
            
            clips.append(burned_clip)
            
        if status_callback:
            status_callback("Concatenating scenes...")
            
        # Join all sub-clips together
        final_video = concatenate_videoclips(clips, method="compose")
        total_duration = final_video.duration
        
        # Stitch Background Music if provided
        if bg_music_path and os.path.exists(bg_music_path):
            if status_callback:
                status_callback("Mixing background music...")
            bg_music = AudioFileClip(bg_music_path)
            
            # Loop music if it is shorter than the final video
            if bg_music.duration < total_duration:
                bg_music_loop_factor = int(np.ceil(total_duration / bg_music.duration))
                bg_music = bg_music.loop(n=bg_music_loop_factor).subclip(0, total_duration)
            else:
                bg_music = bg_music.subclip(0, total_duration)
                
            # Lower background music volume and composite it with narrative audio
            bg_music = bg_music.volumex(bg_music_volume)
            composite_audio = CompositeAudioClip([final_video.audio, bg_music])
            final_video = final_video.set_audio(composite_audio)
            
        # Output paths
        final_output_path = os.path.join("output", output_name)
        if status_callback:
            status_callback(f"Rendering final MP4 to {final_output_path}... (This might take a moment)")
            
        # Write final video
        final_video.write_videofile(
            final_output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            threads=4,
            temp_audiofile=os.path.join("temp", "render_temp_audio.m4a"),
            remove_temp=True
        )
        
        # Close everything to prevent file locks
        for c in clips:
            c.close()
        final_video.close()
        
        if status_callback:
            status_callback("Video compilation complete!")
            
        return final_output_path
        
    except Exception as e:
        if status_callback:
            status_callback(f"Compilation Failed: {e}")
        raise e
    finally:
        # Cleanup temporary files (without crashing if delete fails due to Windows file locking)
        for tf in temp_files:
            try:
                if os.path.exists(tf):
                    os.remove(tf)
            except Exception:
                pass
