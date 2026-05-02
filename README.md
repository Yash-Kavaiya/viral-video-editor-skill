# 🎬 Viral Video Editor — ADK Agent Skill

An **Agent Development Kit (ADK)** skill that uses **Gemini Embedding 2** (multimodal) to understand video content and automatically create viral short-form reels (45–90 seconds) complete with:

- 🧠 AI-powered scene selection using semantic embedding similarity
- 📝 Animated word-by-word captions synced to speech
- 🎵 Background music & sound effect injection
- ✨ Zoom, fade, and text animation effects
- 📱 Auto-reframe to 9:16 vertical format for Reels/Shorts/TikTok

---

## 📁 Project Structure

```
viral-video-editor-skill/
├── agent.py                    # Root ADK agent entry point
├── .env.example                # Environment variable template
├── requirements.txt            # Python dependencies
├── skills/
│   └── viral-video-editor/
│       ├── SKILL.md            # ADK Skill definition (L1 metadata + L2 instructions)
│       ├── scripts/
│       │   ├── video_analyzer.py      # Gemini Embedding 2 video understanding
│       │   ├── scene_selector.py      # Cosine similarity-based scene scoring
│       │   ├── reel_editor.py         # MoviePy + FFmpeg reel assembly
│       │   ├── caption_engine.py      # Animated caption/subtitle generator
│       │   ├── sound_mixer.py         # Background music & SFX overlay
│       │   └── viral_scorer.py        # Engagement potential scoring
│       ├── references/
│       │   ├── VIRAL_PATTERNS.md      # Research-backed viral video patterns
│       │   └── CAPTION_STYLES.md      # Caption animation style catalog
│       └── assets/
│           └── sounds/                # Default sound effect placeholders
└── tests/
    └── test_skill.py
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Run the Agent
```bash
adk web
# or
python agent.py
```

### 4. Example Prompts
```
"Extract the most viral moment from interview.mp4 and make a 60-second reel with captions"
"Create a viral reel from my podcast recording with animated subtitles and background music"
"Find the top 3 engaging clips from lecture.mp4 and combine into a 90-second reel"
```

---

## 🧠 How Gemini Embedding 2 Powers This

1. **Video Ingestion** → Upload video segments to Gemini Embedding 2 API
2. **Embedding Generation** → Get 768-dim multimodal vectors for each scene
3. **Viral Pattern Matching** → Compare scene embeddings against high-engagement reference patterns
4. **Semantic Scene Selection** → Pick scenes with highest cosine similarity to "viral" reference embeddings
5. **Reel Assembly** → Cut, sequence, and render the selected scenes with MoviePy + FFmpeg

---

## 📋 Requirements

- Python 3.10+
- Google ADK (`google-adk >= 1.0.0`)
- `google-genai` (Gemini SDK)
- `moviepy >= 2.0`
- `ffmpeg-python`
- `numpy`, `scipy` (for cosine similarity)
- `pycaps` (animated captions)
- FFmpeg binary installed on system

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
