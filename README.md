# Asụsụ

**Video, in every language.**

Asụsụ (meaning "language" in Igbo) is a video dubbing platform. Paste a video link or upload a file, pick a target language, and get back a shareable link with the video dubbed into that language. The visuals stay identical — only the speech audio is replaced.

## Supported Languages

Spanish, Portuguese, French, German, Mandarin Chinese, Japanese, Thai, Hindi, Arabic, Yoruba, Igbo, Swahili, Korean

## Quick Start

### Prerequisites

- Docker & Docker Compose
- API keys: Anthropic (Claude), ElevenLabs, Cloudflare R2

### Setup

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up --build
```

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API docs**: http://localhost:8000/docs

### Local Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
redis-server &  # Start Redis
uvicorn api.main:app --reload --port 8000 &
celery -A workers.celery_app worker --loglevel=info --concurrency=2

# Frontend
cd frontend
npm install
npm run dev
```

## Architecture

```
React Frontend (Vite) → FastAPI Server → Redis Queue → Celery Workers → Cloudflare R2
```

### Pipeline Steps

1. **Download** video (yt-dlp)
2. **Separate** vocals from background (Demucs)
3. **Transcribe** speech (OpenAI Whisper)
4. **Translate** transcript (Claude API)
5. **Generate** dubbed speech (ElevenLabs TTS)
6. **Mix** new audio + background + video (FFmpeg)
7. **Upload** to cloud storage (Cloudflare R2)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/translate` | Submit video for dubbing |
| GET | `/api/v1/jobs/{id}` | Check job status |
| GET | `/api/v1/jobs/{id}/result` | Get completed job result |
| GET | `/api/v1/languages` | List supported languages |

## Testing

```bash
# Run pipeline with stubs (no API keys needed)
python scripts/seed_test.py --video_url "https://youtube.com/watch?v=..." --target_lang es
```

## Tech Stack

- **Frontend**: React 18, Vite, Framer Motion, Lucide Icons
- **Backend**: FastAPI, Celery, Redis
- **AI/ML**: OpenAI Whisper, Claude API, ElevenLabs TTS
- **Media**: FFmpeg, Demucs, yt-dlp
- **Storage**: Cloudflare R2 (S3-compatible)
