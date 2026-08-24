import os
import requests
import video_compiler as compiler

def run_test():
    print("🚀 Starting End-to-End Video Compiler Verification Test...")
    
    # 1. Setup Directories
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    test_video_path = os.path.join("downloads", "test_scene.mp4")
    test_output_path = os.path.join("output", "test_output.mp4")
    
    # 2. Download sample footage from GitHub
    fallback_url = "https://github.com/intel-iot-devkit/sample-videos/raw/master/classroom.mp4"
    if not os.path.exists(test_video_path):
        print(f"📥 Downloading test stock video from: {fallback_url}...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(fallback_url, headers=headers, stream=True, timeout=30)
            r.raise_for_status()
            with open(test_video_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("✅ Test stock video downloaded successfully.")
        except Exception as e:
            print(f"❌ Failed to download test video: {e}")
            return False
    else:
        print("✅ Test stock video already exists. Skipping download.")
        
    # 3. Create test scenes payload
    scenes = [
        {
            "text": "Imagine a world where every student has a personal AI tutor, and learning feels like magic.",
            "video_path": test_video_path
        }
    ]
    
    # 4. Trigger video compilation
    print("⚙️ Compiling test video (running Edge-TTS, Crop/Resize, and Subtitle burners)...")
    try:
        def status_logger(msg):
            print(f"  [Compiler Log]: {msg}")
            
        compiled_file = compiler.compile_video(
            scenes=scenes,
            bg_music_path="",  # No background music for faster testing
            output_name="test_output.mp4",
            voice="en-US-EmmaMultilingualNeural",
            status_callback=status_logger
        )
        
        if os.path.exists(compiled_file) and os.path.getsize(compiled_file) > 0:
            print(f"\n🎉 SUCCESS! Test video compiled successfully.")
            print(f"📍 Output saved to: {compiled_file}")
            print(f"💾 File size: {os.path.getsize(compiled_file)} bytes")
            return True
        else:
            print("\n❌ Error: Output file was not created or is empty.")
            return False
            
    except Exception as e:
        print(f"\n❌ Compilation verification test failed with exception:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    if success:
        print("\n✅ Verification complete. Environment is fully ready for Streamlit execution!")
    else:
        print("\n❌ Verification failed. Please check the logs above for details.")
