# LightnoteAI Video Editor

> AI-powered video object editing with natural language — built for LightnoteAI technical assignment.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Claude API](https://img.shields.io/badge/Claude-3.5_Sonnet-orange)](https://anthropic.com)

---

## Architecture

User Prompt (Natural Language)
↓
┌─────────────────────────────────────────────────┐
│ STAGE 1: INTENT PARSING │
│ Claude API (claude-sonnet-4-6) │
│ "Replace Coca-Cola with Pepsi" → │
│ { operation: replace_object, │
│ target: "Coca-Cola bottle", │
│ replacement: "Pepsi bottle" } │
└─────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────┐
│ STAGE 2: OBJECT DETECTION │
│ GroundingDINO (zero-shot) │
│ Text prompt → Bounding boxes + confidence │
└─────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────┐
│ STAGE 3: SEGMENTATION & TRACKING │
│ SAM2 (Meta AI) │
│ Bbox → Pixel masks → Multi-frame tracking │
└─────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────┐
│ STAGE 4: INPAINTING │
│ Stable Diffusion Inpainting Pipeline │
│ OR reference-image-guided replacement │
│ OR OpenCV TELEA (fallback removal) │
└─────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────┐
│ STAGE 5: VIDEO COMPOSITION │
│ FFmpeg + OpenCV │
│ Processed frames + original audio → MP4 │
└─────────────────────────────────────────────────┘
↓
Final edited video (web-optimized MP4)


### Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 14 + TailwindCSS | Fast, React-based, SSR |
| Backend API | FastAPI | Async, auto-docs, typed |
| Job Queue | Celery + Redis | Non-blocking GPU tasks |
| Real-time | WebSocket | Live pipeline progress |
| NLP Parser | Claude API | Best-in-class instruction understanding |
| Object Detection | GroundingDINO | Zero-shot, no training needed |
| Segmentation | SAM2 (Meta) | State-of-art video tracking |
| Inpainting | Stable Diffusion | High-quality replacement |
| Video I/O | FFmpeg + OpenCV | Battle-tested, fast |

---

## AI Models & Why I Chose Them

### Claude API (Intent Parsing)
Natural language is ambiguous. "Remove the coke" could mean the drink, the drug, or the fuel. Claude's reasoning capability handles edge cases, compound instructions ("replace X and also remove Y"), multilingual prompts, and low-confidence detection. It returns structured JSON that drives every downstream stage.

### GroundingDINO (Object Detection)
Traditional object detectors (YOLO, R-CNN) require pre-defined class lists. GroundingDINO accepts arbitrary text prompts and performs zero-shot detection — critical since users can ask for any object. It bridges NLP and computer vision directly.

### SAM2 (Segmentation + Tracking)
SAM2 (Segment Anything Model 2) by Meta is the current state-of-the-art for video object segmentation. Given a bounding box in frame 0, it automatically propagates pixel-accurate masks through subsequent frames. This eliminates the need for per-frame detection and dramatically improves temporal consistency.

### Stable Diffusion Inpainting
The `runwayml/stable-diffusion-inpainting` model fills masked regions with contextually appropriate content. For replacement tasks, a text prompt guides what fills the masked area. For removal tasks, a background-focused prompt produces seamless fill.

### Fallback Strategy
On machines without GPU/models: OpenCV TELEA inpainting (removal) + reference image paste (replacement). The pipeline degrades gracefully without crashing.

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis
- FFmpeg (`brew install ffmpeg` / `apt install ffmpeg`)
- (Optional) CUDA GPU for real-time processing

### Quick Start (Docker)
```bash
git clone <your-repo>
cd lightnote-video-editor

# Copy and fill in your API key
cp backend/.env.example backend/.env
# Set ANTHROPIC_API_KEY in backend/.env

docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Set ANTHROPIC_API_KEY in .env

# Terminal 1: Start API
uvicorn main:app --reload --port 8000

# Terminal 2: Start Celery worker
celery -A celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Supported Operations

| Prompt | Operation | Notes |
|--------|-----------|-------|
| "Replace the Coca-Cola with Pepsi" | replace_object | Reference image optional |
| "Remove the watermark" | remove_object | Fills with background |
| "Replace the logo with our brand" | replace_object + reference | Use reference image |
| "Make the car blue" | recolor_object | Color transformation |
| "Delete the person in background" | remove_object | Works on any object |

---

## Known Limitations

1. **Processing time**: Without GPU, each video takes 2-10 minutes. With CUDA, ~15-30s.
2. **Video length**: Capped at 60s / 120 frames to prevent memory exhaustion.
3. **Occlusion**: If the target object goes behind another object mid-video, SAM2 may lose tracking.
4. **Fast motion**: High-speed objects may have inconsistent masks between frames.
5. **Inpainting quality**: Without SD (CPU-only mode), replacements use reference-paste which may have seam artifacts.
6. **Audio**: Original audio is preserved. No audio editing supported.

---

## API Reference

Full OpenAPI docs at `/docs` (Swagger UI) or `/redoc`.

Key endpoints:
- `POST /api/v1/jobs` — Create job (multipart/form-data)
- `GET /api/v1/jobs/{job_id}` — Poll status
- `GET /api/v1/jobs` — List recent jobs
- `DELETE /api/v1/jobs/{job_id}` — Cancel job
- `POST /api/v1/jobs/from-url` — Create from video URL (bonus)
- `WS /ws/{job_id}` — Real-time progress stream

---

## Interview Talking Points

**"Why Celery instead of FastAPI BackgroundTasks?"**
BackgroundTasks die if the server restarts. Celery persists tasks in Redis, supports retries, time limits, and can scale to multiple workers. For GPU-heavy video processing, reliability matters.

**"Why did you pick GroundingDINO over YOLO?"**
YOLO requires the object class to be in its training set. GroundingDINO accepts free-form text, so it works for arbitrary objects without retraining. The tradeoff is slightly slower inference.

**"How does real-time progress work?"**
The Celery worker publishes to a Redis pub/sub channel. The FastAPI WebSocket handler subscribes and forwards updates to the browser client. If WebSocket fails, the frontend falls back to HTTP polling.

**"How does Claude help beyond a simple regex?"**
Consider: "Remove the drink and replace the hat with a red cap." A regex can't handle compound instructions, ambiguity, or multilingual input. Claude returns structured JSON with confidence scores, allowing the pipeline to handle edge cases gracefully.