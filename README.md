# 🎬 Antigravity AI Video Automation & Publisher

An elegant, premium Streamlit dashboard that automates short-form video generation (YouTube Shorts, Instagram Reels) and publishes them directly to social platforms.

Developed with:
- **Streamlit**: Elegant glassmorphic dark-theme UI.
- **MoviePy & PIL**: Core video compiler that crops footage to vertical (9:16) format, mixes audio tracks, and burns readable yellow captions on frames without requiring external image libraries.
- **Edge-TTS**: Ultra-realistic text-to-speech narration (fallback to gTTS).
- **Pexels API**: Dynamic search and download of premium stock footage based on keywords (fallback to Mixkit royalty-free vertical URLs).
- **YouTube Data API v3**: Automatic video upload with local OAuth2 flow.
- **Instagram Graph API**: Automated container creation, polling, and direct Reels publishing (utilizing secure temporary public file hosting proxies).

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- **Python**: Version 3.10 to 3.13.
- **FFmpeg**: On Windows, MoviePy will attempt to download FFmpeg automatically. If you encounter any encoding errors, download and install [FFmpeg](https://ffmpeg.org/download.html) and add it to your system PATH.

### 2. Installation
Clone the repository (or copy the files) into your local folder, and run:
```bash
pip install -r requirements.txt
```

### 3. Running the App
Launch the Streamlit web dashboard:
```bash
streamlit run app.py
```
This will open the application in your default browser at `http://localhost:8501`.

---

## 🔑 Setting up API Credentials

You can enter and save your API credentials directly in the Streamlit Sidebar. They are saved in a local, untracked `.env` file for security.

### 1. Pexels API (Stock Sourcing)
1. Register for a free account on [Pexels](https://www.pexels.com/).
2. Go to the [Pexels API Documentation](https://www.pexels.com/api/new-key/) and generate your API key.
3. Paste it into the Streamlit sidebar under **API Credentials** and click **Save**.
*(If omitted, the app automatically falls back to Mixkit royalty-free videos.)*

### 2. Google Gemini API (Script Writer)
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/).
2. Save it in the sidebar. This allows the AI to automatically write scripts and visual cue keywords.

### 3. YouTube API Setup (Direct Upload)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. In the sidebar, select **APIs & Services** -> **Library**, search for **YouTube Data API v3**, and click **Enable**.
4. Go to **APIs & Services** -> **OAuth consent screen**. Create an External consent screen, fill in basic details, and add the scope `.../auth/youtube.upload`. Add your email as a **Test User**.
5. Go to **APIs & Services** -> **Credentials**. Click **+ Create Credentials** -> **OAuth client ID**. Select **Desktop app** as the application type.
6. Click **Download JSON** on the created credential. Rename the downloaded file to `client_secrets.json`.
7. Upload this file directly in the Streamlit Sidebar under the YouTube section.

### 4. Instagram Graph API Setup (Direct Reels)
1. Create a Facebook Developer Account on [Meta for Developers](https://developers.facebook.com/).
2. Create a Developer App (Type: Other or Business) and set up the **Instagram Graph API**.
3. Set up a Facebook Page and link it to an **Instagram Professional/Business Account**.
4. Go to the Graph API Explorer:
   - Select your App.
   - Request permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
   - Generate a **User Access Token**, exchange it for a **Long-Lived Page Access Token**.
5. Get your **Instagram User ID** via the Graph Explorer or Page settings.
6. Input these values in the Streamlit sidebar.

---

## 🛠️ Verification & Diagnostic Check

Before running the Streamlit app, you can verify your system handles TTS and MoviePy compilation correctly by running our diagnostic script:
```bash
python test_compilation.py
```
If successful, this will render a 9:16 test video to `output/test_output.mp4` with a voiceover and burned-in subtitles.

---

## 🌐 Git & Deployment Workflow

### 1. Pushing to GitHub
Initialize your repository and push the code:
```bash
git init
git add .
git commit -m "feat: initial commit of AI video automation app"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```
*(Notice that `.gitignore` automatically prevents your `.env`, `client_secrets.json`, and credentials from being uploaded.)*

### 2. Deploying to Streamlit Community Cloud
1. Create an account on [Streamlit Community Cloud](https://share.streamlit.io/).
2. Click **New app**, select your GitHub repository, branch, and set the main file path to `app.py`.
3. In the Streamlit app settings, paste your `.env` contents under **Secrets** (optional) or simply enter the keys in the sidebar when visiting your deployed app interface.
4. If you deploy online, note that YouTube OAuth credentials (`client_secrets.json`) can be uploaded directly via the UI sidebar file uploader on each session, meaning you don't need to commit credentials to your Git repository!
