import os
import json
import streamlit as st
from dotenv import load_dotenv

# Load existing environment variables
load_dotenv()

# Import core engine modules
import video_compiler as compiler
import publisher

# Page Configuration
st.set_page_config(
    page_title="Antigravity AI Video Automation",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Glassmorphic Design
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Headers styling */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    .gradient-header {
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    
    .gradient-subtitle {
        color: #94a3b8;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }

    /* Cards */
    .scene-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .scene-card:hover {
        border-color: rgba(129, 140, 248, 0.4);
        box-shadow: 0 10px 30px rgba(129, 140, 248, 0.15);
        transform: translateY(-2px);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 8px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: transparent;
        border-radius: 10px;
        color: #94a3b8;
        font-weight: 600;
        padding: 0px 20px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background-color: rgba(255, 255, 255, 0.04);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
    }
    
    /* Input formatting */
    div[data-baseweb="input"] {
        background-color: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #4338ca 0%, #4f46e5 100%);
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(79, 70, 229, 0.35);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR: CONFIG & KEYS MANAGER
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/youtube-play.png", width=64)
    st.markdown("## Antigravity Studio\n**v1.0.0**")
    st.markdown("---")
    
    # 1. API Keys & Credentials
    with st.expander("🔑 API Credentials", expanded=True):
        pexels_key = st.text_input(
            "Pexels API Key", 
            value=os.getenv("PEXELS_API_KEY", ""), 
            type="password",
            help="Free key from Pexels API developer console."
        )
        gemini_key = st.text_input(
            "Gemini API Key", 
            value=os.getenv("GEMINI_API_KEY", ""), 
            type="password",
            help="Required for auto-generating scripts."
        )
        instagram_uid = st.text_input(
            "Instagram User ID", 
            value=os.getenv("INSTAGRAM_USER_ID", ""), 
            help="Facebook Graph ID associated with your business account."
        )
        instagram_token = st.text_input(
            "Instagram Access Token", 
            value=os.getenv("INSTAGRAM_ACCESS_TOKEN", ""), 
            type="password",
            help="Permanent page access token with publish scopes."
        )
        
        if st.button("Save Keys to .env"):
            with open(".env", "w") as env_file:
                env_file.write(f"PEXELS_API_KEY={pexels_key}\n")
                env_file.write(f"GEMINI_API_KEY={gemini_key}\n")
                env_file.write(f"INSTAGRAM_USER_ID={instagram_uid}\n")
                env_file.write(f"INSTAGRAM_ACCESS_TOKEN={instagram_token}\n")
            st.success("Credentials saved to .env file!")
            
    # 2. YouTube client_secrets.json Upload
    with st.expander("📺 YouTube OAuth client_secrets.json", expanded=False):
        secrets_file = st.file_uploader("Upload client_secrets.json", type=["json"])
        if secrets_file is not None:
            try:
                secrets_data = json.load(secrets_file)
                with open("client_secrets.json", "w") as f:
                    json.dump(secrets_data, f)
                st.success("Saved client_secrets.json to workspace!")
            except Exception as e:
                st.error(f"Error saving file: {e}")
                
        if os.path.exists("client_secrets.json"):
            st.info("✅ client_secrets.json is present.")
        else:
            st.warning("⚠️ client_secrets.json is missing. Please upload it to publish to YouTube.")
            
    # 3. Voice Settings
    with st.expander("🗣️ Narration Voice", expanded=False):
        voice_opt = st.selectbox(
            "Select AI Voice (Edge-TTS)",
            options=[
                ("Female: Emma (Multilingual)", "en-US-EmmaMultilingualNeural"),
                ("Female: Aria (Standard)", "en-US-AriaNeural"),
                ("Male: Guy (Standard)", "en-US-GuyNeural"),
                ("Female: Michelle (English GB)", "en-GB-SoniaNeural"),
                ("Male: Ryan (English GB)", "en-GB-RyanNeural")
            ],
            format_func=lambda x: x[0]
        )
        voice_id = voice_opt[1]
        
    # 4. Background Music Settings
    with st.expander("🎵 Background Music", expanded=False):
        bg_music_file = st.file_uploader("Upload MP3 background music", type=["mp3"])
        bg_volume = st.slider("Music Volume Scale", 0.0, 0.5, 0.15, 0.05)

# Save uploaded background music path
bg_music_path = ""
if bg_music_file is not None:
    bg_music_path = os.path.join("temp", "user_bg_music.mp3")
    with open(bg_music_path, "wb") as f:
        f.write(bg_music_file.getbuffer())

# ==========================================
# MAIN PANEL
# ==========================================
st.markdown('<div class="gradient-header">Antigravity Video Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="gradient-subtitle">Automate Scriptwriting, Media Stitching, and Multi-Platform Publishing</div>', unsafe_allow_html=True)

# Tabs definitions
tab_chat, tab1, tab2, tab3 = st.tabs(["💬 AI Chatbot", "📝 Script Planner", "🎬 Video Compilation", "🚀 Publish Center"])

# Initialize session state for chatbot
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hello! I am your Antigravity AI Assistant. What topic would you like to create a video about today? I can write full scripts, brainstorm hooks, or help refine your voiceover narration."}
    ]

# Initialize session state for script scenes
if "scenes" not in st.session_state:
    st.session_state.scenes = [
        {"text": "Imagine a world where every student has a personal AI tutor… and learning feels like magic.", "query": "futuristic classroom"},
        {"text": "AI is reshaping education. Personalized lessons adapt to each learner's pace, helping them grow.", "query": "student tablet computer"},
        {"text": "Education is evolving. With AI, the classroom becomes limitless. The future starts today.", "query": "university campus sunrise"}
    ]

# ==========================================
# TAB 0: AI CHATBOT WORKSPACE
# ==========================================
with tab_chat:
    st.subheader("💬 Brainstorm with Antigravity AI")
    st.markdown("Use this workspace to brainstorm ideas or write scripts. When a structured script is generated, you can click **Load Script** to send it directly to the timeline.")
    
    # Show free key instruction if no key is present
    if not gemini_key:
        st.info("💡 **Tip**: Get a 100% Free Gemini API Key in 10 seconds from [Google AI Studio](https://aistudio.google.com/) (no credit card required) to enable ultra-fast, high-quality script generation!")
    
    # Container for scrollable chat
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    # Chat input
    user_prompt = st.chat_input("Type your message here (e.g., 'Write a script about space exploration' or 'Make the hook more dramatic')...")
    
    if user_prompt:
        # Display user message
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_prompt)
                
        # Generate assistant response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # If no API key, we can generate a friendly helpful response explaining how to get the free key
            if not gemini_key:
                prompt_lower = user_prompt.lower()
                if "script" in prompt_lower or "video" in prompt_lower or "education" in prompt_lower or "coding" in prompt_lower:
                    mock_reply = "I would love to generate that script for you! However, to run the AI text engine, please enter a **Gemini API Key** in the sidebar. It is 100% free from [Google AI Studio](https://aistudio.google.com/).\n\nMeanwhile, I have pre-loaded a high-quality fallback script on **AI Transforming Education** in the **Script Planner** tab for you to test!"
                else:
                    mock_reply = "Hello! To chat and brainstorm custom ideas, please enter a **Gemini API Key** in the sidebar. The key is completely free to get from [Google AI Studio](https://aistudio.google.com/). Once entered, you can ask me anything!"
                st.session_state.chat_history.append({"role": "assistant", "content": mock_reply})
                response_placeholder.markdown(mock_reply)
            else:
                with st.spinner("Thinking..."):
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=gemini_key)
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        
                        # Build standard history list for Gemini
                        conversation = ""
                        for m in st.session_state.chat_history[:-1]:
                            role_name = "User" if m["role"] == "user" else "AI Assistant"
                            conversation += f"{role_name}: {m['content']}\n\n"
                        
                        system_instructions = """
                        You are Antigravity AI, a professional scriptwriter and video brainstorming partner.
                        Help the user refine their video topics, narration scripts, and visual stock media search terms.
                        
                        If the user asks you to write a script, generate it and format the script at the very end of your response inside a raw JSON block so the app can parse it.
                        The JSON block must be an array of objects like this:
                        [SCRIPT_JSON]
                        [
                          {"text": "Hook text...", "query": "pexels search query"},
                          {"text": "Body text...", "query": "pexels search query"},
                          {"text": "Conclusion text...", "query": "pexels search query"}
                        ]
                        [/SCRIPT_JSON]
                        Keep the JSON clean and include the markers [SCRIPT_JSON] and [/SCRIPT_JSON] around it.
                        """
                        
                        prompt = f"{system_instructions}\n\nConversation history:\n{conversation}\nUser: {user_prompt}\nAI Assistant:"
                        
                        response = model.generate_content(prompt)
                        reply = response.text.strip()
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        response_placeholder.markdown(reply)
                        
                        # Check if response contains a script JSON
                        if "[SCRIPT_JSON]" in reply and "[/SCRIPT_JSON]" in reply:
                            try:
                                json_part = reply.split("[SCRIPT_JSON]")[1].split("[/SCRIPT_JSON]")[0].strip()
                                parsed = json.loads(json_part)
                                if isinstance(parsed, list) and len(parsed) > 0:
                                    st.session_state.temp_chat_script = parsed
                                    st.success("Found a new video script in our chat! Click the button below to load it into your video planner.")
                            except Exception as e:
                                print(f"Failed to parse chatbot script: {e}")
                    except Exception as e:
                        err_msg = f"Chatbot Error: {e}. Please check your API key in the sidebar."
                        st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
                        response_placeholder.error(err_msg)
                        
    # Button to load script if found
    if "temp_chat_script" in st.session_state and st.session_state.temp_chat_script:
        if st.button("📋 Apply Chatbot Script to Planner"):
            st.session_state.scenes = st.session_state.temp_chat_script
            del st.session_state.temp_chat_script
            st.success("Successfully applied chatbot script to the Timeline! Switch to the 'Script Planner' tab to view/edit.")

# ==========================================
# TAB 1: SCRIPT WRITER
# ==========================================
with tab1:
    st.subheader("Generate or Edit Video Script")
    topic_input = st.text_input("Enter Video Topic", value="AI Transforming Education", placeholder="e.g., Space Exploration, Healthy Habits, Coding Benefits")
    
    if st.button("Generate Script with AI"):
        if not gemini_key:
            st.error("Please configure your Gemini API Key in the sidebar to auto-generate scripts.")
        else:
            with st.spinner("Generating scripts and keywords using Google Gemini..."):
                import google.generativeai as genai
                try:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    prompt = f"""
                    You are an expert short-form video scriptwriter for YouTube Shorts and Instagram Reels.
                    Generate a 3-scene script for the topic: "{topic_input}".
                    For each scene, provide:
                    1. Narration Text (optimized for text-to-speech voiceovers, around 12-18 words, short & simple).
                    2. Visual Stock Footage Query (1-3 words of keywords, e.g. "futuristic classroom").
                    
                    Format the response as a strict JSON array of objects with keys "text" and "query". Example:
                    [
                      {{"text": "Imagine a world where every student has a personal AI tutor.", "query": "futuristic classroom"}},
                      {{"text": "AI is reshaping education. Lessons adapt to each student.", "query": "student tablet computer"}},
                      {{"text": "The future of learning starts today. Subscribe for more!", "query": "university campus sunrise"}}
                    ]
                    Return ONLY the raw JSON array. Do not include markdown formatting or backticks.
                    """
                    
                    response = model.generate_content(prompt)
                    res_text = response.text.strip()
                    
                    # Clean markdown if present
                    if res_text.startswith("```json"):
                        res_text = res_text[7:]
                    if res_text.endswith("```"):
                        res_text = res_text[:-3]
                    res_text = res_text.strip()
                    
                    parsed_scenes = json.loads(res_text)
                    if isinstance(parsed_scenes, list) and len(parsed_scenes) > 0:
                        st.session_state.scenes = parsed_scenes
                        st.success("New script generated successfully!")
                    else:
                        st.error("Generated format was invalid. Fallback layout active.")
                except Exception as e:
                    st.error(f"Failed to generate script: {e}")
                    
    st.markdown("---")
    st.markdown("### Scene Breakdowns")
    
    updated_scenes = []
    for idx, scene in enumerate(st.session_state.scenes):
        st.markdown(f'<div class="scene-card">', unsafe_allow_html=True)
        st.markdown(f"**🎬 Scene {idx + 1}**")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            text_val = st.text_area(f"Narration Script (Scene {idx + 1})", value=scene.get("text", ""), key=f"text_{idx}", height=70)
        with col2:
            query_val = st.text_input(f"Stock Media Keyword", value=scene.get("query", ""), key=f"query_{idx}")
            
        st.markdown('</div>', unsafe_allow_html=True)
        updated_scenes.append({"text": text_val, "query": query_val})
        
    st.session_state.scenes = updated_scenes

# ==========================================
# TAB 2: COMPILATION & PREVIEW
# ==========================================
# Direct high-quality download fallbacks (when Pexels is not configured)
MIXKIT_FALLBACKS = [
    "https://github.com/intel-iot-devkit/sample-videos/raw/master/classroom.mp4",
    "https://github.com/intel-iot-devkit/sample-videos/raw/master/people-detection.mp4",
    "https://github.com/intel-iot-devkit/sample-videos/raw/master/driver-action-recognition.mp4"
]

with tab2:
    st.subheader("Asset Sourcing & Video Rendering")
    
    col_l, col_r = st.columns([3, 2])
    
    with col_l:
        st.markdown("### 🔍 Stock Media Assets")
        if not pexels_key:
            st.warning("⚠️ No Pexels API Key detected. Rendering will automatically fallback to pre-selected Mixkit royalty-free vertical video clips.")
        
        # Sourcing button
        if st.button("Fetch & Download Stock Assets"):
            with st.spinner("Downloading stock footage..."):
                for idx, scene in enumerate(st.session_state.scenes):
                    query = scene["query"]
                    video_file_name = f"scene_{idx}.mp4"
                    local_path = os.path.join("downloads", video_file_name)
                    
                    st.write(f"🔍 Searching footage for Scene {idx + 1} (Keyword: *{query}*)...")
                    
                    downloaded = False
                    if pexels_key:
                        videos = compiler.search_pexels_videos(query, pexels_key, limit=3)
                        if videos:
                            try:
                                compiler.download_video_asset(videos[0], video_file_name)
                                st.session_state[f"video_path_{idx}"] = local_path
                                st.success(f"✅ Scene {idx+1}: Sourced from Pexels API")
                                downloaded = True
                            except Exception as e:
                                st.write(f"Pexels download failed for scene {idx+1}: {e}")
                                
                    if not downloaded:
                        # Fallback Mixkit downloader
                        fallback_url = MIXKIT_FALLBACKS[idx % len(MIXKIT_FALLBACKS)]
                        st.write(f"Downloading royalty-free fallback for Scene {idx + 1}...")
                        try:
                            import requests
                            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
                            r = requests.get(fallback_url, headers=headers, stream=True, timeout=30)
                            r.raise_for_status()
                            with open(local_path, "wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            st.session_state[f"video_path_{idx}"] = local_path
                            st.success(f"✅ Scene {idx+1}: Sourced from Fallback Link")
                        except Exception as e:
                            st.error(f"Fallback download failed: {e}")
                            
        st.markdown("---")
        st.markdown("### 🎬 Compile final `.mp4` file")
        
        # Render trigger
        if st.button("Render Final Video"):
            # Check if assets are downloaded
            has_assets = True
            scenes_to_compile = []
            
            for idx, scene in enumerate(st.session_state.scenes):
                local_path = os.path.join("downloads", f"scene_{idx}.mp4")
                if not os.path.exists(local_path):
                    has_assets = False
                    break
                scenes_to_compile.append({
                    "text": scene["text"],
                    "video_path": local_path
                })
                
            if not has_assets:
                st.error("Please click 'Fetch & Download Stock Assets' first to collect stock video footage before rendering.")
            else:
                log_placeholder = st.empty()
                
                def render_status(msg):
                    log_placeholder.info(f"⚙️ {msg}")
                    
                try:
                    final_path = compiler.compile_video(
                        scenes=scenes_to_compile,
                        bg_music_path=bg_music_path,
                        output_name="final_output.mp4",
                        voice=voice_id,
                        bg_music_volume=bg_volume,
                        status_callback=render_status
                    )
                    st.session_state.rendered_video = final_path
                    log_placeholder.success("🎉 Rendering finished! Review your video on the right panel.")
                except Exception as e:
                    log_placeholder.error(f"❌ Video compilation crashed: {e}")
                    
    with col_r:
        st.markdown("### 📺 Video Preview")
        if "rendered_video" in st.session_state and os.path.exists(st.session_state.rendered_video):
            st.video(st.session_state.rendered_video)
            st.success(f"Rendered video saved locally at: `{st.session_state.rendered_video}`")
            with open(st.session_state.rendered_video, "rb") as file:
                st.download_button(
                    label="📥 Download Video File",
                    data=file,
                    file_name="rendered_video.mp4",
                    mime="video/mp4"
                )
        else:
            st.info("Render a video to see the preview here.")

# ==========================================
# TAB 3: PUBLISHER CENTER
# ==========================================
with tab3:
    st.subheader("Social Media API Upload Portal")
    
    if "rendered_video" not in st.session_state or not os.path.exists(st.session_state.rendered_video):
        st.warning("⚠️ You must render a video in the compilation tab before you can use the publishing tools.")
    else:
        st.info(f"Ready to publish: `{st.session_state.rendered_video}`")
        
        col_pub_l, col_pub_r = st.columns([1, 1])
        
        with col_pub_l:
            st.markdown("### 📝 Video Metadata")
            pub_title = st.text_input("YouTube Shorts Title", value=f"AI Transforming Education #shorts #ai")
            pub_description = st.text_area("YouTube/Instagram Description", 
                                           value="Imagine a world where every student has a personal AI tutor. AI is reshaping education with personalized lessons. #shorts #ai #education #learning")
            pub_privacy = st.selectbox("YouTube Privacy Status", ["private", "public", "unlisted"])
            
        with col_pub_r:
            st.markdown("### 🌐 Platform Selector")
            
            # YouTube Block
            st.markdown("#### 🔴 Publish to YouTube")
            if not os.path.exists("client_secrets.json"):
                st.warning("YouTube Upload is locked. Please upload 'client_secrets.json' in the sidebar first.")
                youtube_ready = False
            else:
                youtube_ready = True
                
            trigger_youtube = st.button("Upload to YouTube Shorts", disabled=not youtube_ready)
            if trigger_youtube:
                yt_log = st.empty()
                def yt_status(msg):
                    yt_log.info(msg)
                try:
                    video_url = publisher.upload_to_youtube(
                        video_path=st.session_state.rendered_video,
                        title=pub_title,
                        description=pub_description,
                        privacy_status=pub_privacy,
                        status_callback=yt_status
                    )
                    yt_log.success(f"🎉 YouTube upload complete! Video URL: {video_url}")
                except Exception as e:
                    yt_log.error(f"❌ YouTube Upload Failed: {e}")
                    
            st.markdown("---")
            
            # Instagram Block
            st.markdown("#### 📸 Publish to Instagram")
            if not instagram_uid or not instagram_token:
                st.warning("Instagram Upload is locked. Please configure User ID and Access Token in the sidebar first.")
                instagram_ready = False
            else:
                instagram_ready = True
                
            trigger_instagram = st.button("Upload to Instagram Reels", disabled=not instagram_ready)
            if trigger_instagram:
                ig_log = st.empty()
                def ig_status(msg):
                    ig_log.info(msg)
                try:
                    ig_url = publisher.publish_to_instagram(
                        video_path=st.session_state.rendered_video,
                        caption=pub_description,
                        ig_user_id=instagram_uid,
                        access_token=instagram_token,
                        status_callback=ig_status
                    )
                    ig_log.success(f"🎉 Instagram upload complete! Reel ID / URL: {ig_url}")
                except Exception as e:
                    ig_log.error(f"❌ Instagram Upload Failed: {e}")
