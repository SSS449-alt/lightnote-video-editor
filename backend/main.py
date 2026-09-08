"""
LightnoteAI Video Editor - FastAPI Application
Main entry point with WebSocket support and background job processing
"""
import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import upload, jobs
from api.routes.websocket import websocket_manager
from models.job_store import job_store
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""
    # Ensure directories exist
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    print("✅ LightnoteAI Video Editor started")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="LightnoteAI Video Editor API",
    description="""
    AI-powered video object replacement pipeline.
    
    ## Pipeline Stages
    1. **Intent Parsing** - Claude API extracts structured editing intent from natural language
    2. **Object Detection** - GroundingDINO zero-shot detection
    3. **Segmentation & Tracking** - SAM2 multi-frame tracking
    4. **Inpainting** - Stable Diffusion inpainting
    5. **Video Composition** - FFmpeg final output
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])

# Static files for output videos
app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress streaming.
    Sends stage-by-stage updates as the pipeline runs.
    """
    await websocket_manager.connect(job_id, websocket)
    try:
        while True:
            # Keep connection alive, send pings
            await asyncio.sleep(1)
            
            # Check if job is done
            job = await job_store.get_job(job_id)
            if job and job.get("status") in ["completed", "failed"]:
                await websocket.send_json({
                    "type": "final",
                    "job": job
                })
                break
    except WebSocketDisconnect:
        websocket_manager.disconnect(job_id)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "pipeline_stages": [
            "intent_parsing",
            "object_detection", 
            "segmentation_tracking",
            "inpainting",
            "video_composition"
        ]
    }