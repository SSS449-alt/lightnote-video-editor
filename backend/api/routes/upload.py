"""
File upload endpoints.
Handles video and reference image uploads with validation.
"""
import uuid
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from config import settings
from models.job_store import job_store
from tasks.pipeline import run_pipeline
from celery_app import celery_app

router = APIRouter()

ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/avi"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_VIDEO_BYTES = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024


async def save_upload(file: UploadFile, directory: str, prefix: str = "") -> str:
    """Save uploaded file and return filename"""
    ext = Path(file.filename).suffix.lower()
    filename = f"{prefix}{uuid.uuid4().hex}{ext}"
    filepath = Path(directory) / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        if len(content) > MAX_VIDEO_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.MAX_VIDEO_SIZE_MB}MB"
            )
        await f.write(content)
    
    return filename


@router.post("/jobs", summary="Create a new video editing job")
async def create_job(
    video: UploadFile = File(..., description="Input video file"),
    prompt: str = Form(..., min_length=5, max_length=500),
    reference_image: Optional[UploadFile] = File(None, description="Optional reference image for replacement"),
):
    """
    Create and enqueue a new video editing job.
    
    The pipeline will:
    1. Parse your natural language prompt into structured editing intent
    2. Detect the target object using GroundingDINO
    3. Segment and track across frames using SAM2
    4. Apply inpainting/replacement using Stable Diffusion
    5. Compose the final video using FFmpeg
    """
    # Validate video
    if video.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid video type: {video.content_type}. Allowed: {ALLOWED_VIDEO_TYPES}"
        )
    
    job_id = uuid.uuid4().hex
    
    # Save video
    video_filename = await save_upload(video, settings.UPLOAD_DIR, prefix="video_")
    
    # Save reference image if provided
    ref_image_filename = None
    if reference_image and reference_image.filename:
        if reference_image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type: {reference_image.content_type}"
            )
        ref_image_filename = await save_upload(
            reference_image, settings.UPLOAD_DIR, prefix="ref_"
        )
    
    # Create job in Redis
    await job_store.create_job(
        job_id=job_id,
        prompt=prompt,
        video_filename=video_filename,
        reference_image_filename=ref_image_filename
    )
    
    # Enqueue Celery task
    celery_app.send_task(
        "tasks.pipeline.run_pipeline",
        args=[job_id, video_filename, prompt, ref_image_filename],
        task_id=job_id
    )
    
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "queued",
            "message": "Job enqueued successfully. Connect to WebSocket for real-time progress.",
            "websocket_url": f"/ws/{job_id}",
            "poll_url": f"/api/v1/jobs/{job_id}"
        }
    )


@router.post("/jobs/from-url", summary="Create job from video URL")
async def create_job_from_url(
    video_url: str = Form(...),
    prompt: str = Form(..., min_length=5),
):
    """
    Bonus: Accept a YouTube/direct video URL instead of file upload.
    Uses yt-dlp to download the video.
    """
    import subprocess
    
    job_id = uuid.uuid4().hex
    output_filename = f"video_{job_id}.mp4"
    output_path = Path(settings.UPLOAD_DIR) / output_filename
    
    try:
        result = subprocess.run([
            "yt-dlp", "-f", "mp4", "-o", str(output_path), 
            "--max-filesize", f"{settings.MAX_VIDEO_SIZE_MB}M",
            video_url
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download video: {result.stderr}"
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Video download timed out")
    
    await job_store.create_job(
        job_id=job_id,
        prompt=prompt,
        video_filename=output_filename
    )
    
    celery_app.send_task(
        "tasks.pipeline.run_pipeline",
        args=[job_id, output_filename, prompt, None],
        task_id=job_id
    )
    
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "queued",
            "message": "Video downloaded and job enqueued.",
            "websocket_url": f"/ws/{job_id}"
        }
    )