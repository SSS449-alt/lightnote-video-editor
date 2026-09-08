"""
MAIN PIPELINE ORCHESTRATOR

This is the heart of the system. It chains all 5 stages together
and pushes real-time progress updates via Redis pub/sub -> WebSocket.

Pipeline stages:
  1. Intent Parsing    (Claude API)         ~2s
  2. Object Detection  (GroundingDINO)      ~1-3s per keyframe  
  3. Segmentation      (SAM2)               ~5-15s
  4. Inpainting        (SD / OpenCV)        ~2-5s per frame
  5. Video Composition (FFmpeg)             ~5-10s
"""
import asyncio
import time
import uuid
from pathlib import Path
from typing import Optional
import cv2
import numpy as np

from celery import Task
from celery_app import celery_app
from config import settings
from models.job_store import job_store
from models.schemas import JobStatus, EditOperation
from tasks.intent_parser import parse_editing_intent
from tasks.object_detector import detect_object_in_frame, load_grounding_dino
from tasks.segmenter import segment_and_track_frames, load_sam2, dilate_mask
from tasks.inpainter import inpaint_frame, load_inpainting_pipeline
from tasks.video_composer import extract_frames, compose_video


def push_progress(job_id: str, stage_idx: int, stage_status: str,
                   message: str, progress: int, overall_progress: int):
    """
    Push progress update to Redis pub/sub channel.
    WebSocket handler subscribes and forwards to client.
    """
    import redis
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    import json
    
    r.publish(f"job_progress:{job_id}", json.dumps({
        "type": "progress",
        "job_id": job_id,
        "stage_index": stage_idx,
        "stage_status": stage_status,
        "message": message,
        "stage_progress": progress,
        "overall_progress": overall_progress
    }))
    
    # Also update Redis job state
    asyncio.run(job_store.update_stage(job_id, stage_idx, stage_status, message, progress))


# ==================== LAZY MODEL LOADING ====================
# Models are loaded once per worker, not per task

_grounding_dino = None
_sam2 = None
_sd_pipe = None


def get_models():
    """Lazy load all ML models on first use"""
    global _grounding_dino, _sam2, _sd_pipe
    
    if _grounding_dino is None:
        print("Loading GroundingDINO...")
        _grounding_dino = load_grounding_dino()
    
    if _sam2 is None:
        print("Loading SAM2...")
        _sam2 = load_sam2()
    
    if _sd_pipe is None:
        print("Loading SD Inpainting...")
        _sd_pipe = load_inpainting_pipeline(settings.DEVICE)
    
    return _grounding_dino, _sam2, _sd_pipe


# ==================== CELERY TASK ====================

@celery_app.task(name="tasks.pipeline.run_pipeline", bind=True)
def run_pipeline(
    self: Task,
    job_id: str,
    video_filename: str,
    prompt: str,
    reference_image_filename: Optional[str] = None
):
    """
    Main Celery task: orchestrates the 5-stage AI pipeline.
    """
    start_time = time.time()
    video_path = str(Path(settings.UPLOAD_DIR) / video_filename)
    ref_image_path = (
        str(Path(settings.UPLOAD_DIR) / reference_image_filename)
        if reference_image_filename else None
    )
    
    try:
        # Update job status to running
        asyncio.run(job_store.update_job_status(job_id, JobStatus.PARSING_INTENT))
        
        # =========================================================
        # STAGE 1: INTENT PARSING (Claude API)
        # =========================================================
        push_progress(job_id, 0, "running", "Analyzing your editing instruction...", 0, 5)
        
        intent = asyncio.run(parse_editing_intent(prompt, ref_image_path))
        asyncio.run(job_store.set_parsed_intent(job_id, intent.model_dump()))
        
        push_progress(job_id, 0, "done", 
                      f"Understood: {intent.explanation}", 100, 15)
        
        # =========================================================
        # STAGE 2: OBJECT DETECTION (GroundingDINO)
        # =========================================================
        asyncio.run(job_store.update_job_status(job_id, JobStatus.DETECTING_OBJECT))
        push_progress(job_id, 1, "running", 
                      f"Detecting '{intent.target_object}' in video...", 0, 20)
        
        # Extract frames
        frames, fps, size = extract_frames(video_path, max_frames=120)
        
        if not frames:
            raise ValueError("Could not extract frames from video")
        
        gdino, sam2_model, sd_pipe = get_models()
        
        # Detect on first frame (or best frame)
        detections = detect_object_in_frame(frames[0], intent.target_object, model=gdino)
        
        if not detections:
            # Try a few more frames
            for frame in frames[1:5]:
                detections = detect_object_in_frame(frame, intent.target_object, model=gdino)
                if detections:
                    break
        
        if not detections:
            raise ValueError(
                f"Could not detect '{intent.target_object}' in video. "
                "Try a more specific description or check the video content."
            )
        
        best_detection = detections[0]
        initial_bbox = best_detection["bbox"]
        
        push_progress(job_id, 1, "done",
                      f"Detected '{intent.target_object}' (confidence: {best_detection['confidence']:.0%})",
                      100, 35)
        
        # =========================================================
        # STAGE 3: SEGMENTATION & TRACKING (SAM2)
        # =========================================================
        asyncio.run(job_store.update_job_status(job_id, JobStatus.SEGMENTING))
        push_progress(job_id, 2, "running", 
                      f"Segmenting and tracking object across {len(frames)} frames...", 0, 40)
        
        masks = segment_and_track_frames(frames, initial_bbox, predictor=sam2_model)
        
        # Dilate masks for cleaner inpainting
        masks = [dilate_mask(m, pixels=8) for m in masks]
        
        push_progress(job_id, 2, "done", 
                      f"Tracked object across all {len(frames)} frames", 100, 55)
        
        # =========================================================
        # STAGE 4: INPAINTING (SD or OpenCV)
        # =========================================================
        asyncio.run(job_store.update_job_status(job_id, JobStatus.INPAINTING))
        
        # Load reference image if provided
        ref_image_bgr = None
        if ref_image_path:
            ref_image_bgr = cv2.imread(ref_image_path)
        
        processed_frames = []
        total_frames = len(frames)
        
        for i, (frame, mask) in enumerate(zip(frames, masks)):
            frame_progress = int((i / total_frames) * 100)
            overall_progress = 55 + int((i / total_frames) * 30)
            
            if i % 5 == 0:  # Update every 5 frames
                push_progress(job_id, 3, "running",
                              f"Processing frame {i+1}/{total_frames}...",
                              frame_progress, overall_progress)
            
            processed = inpaint_frame(frame, mask, intent, ref_image_bgr, sd_pipe)
            processed_frames.append(processed)
        
        push_progress(job_id, 3, "done", 
                      f"Processed all {total_frames} frames", 100, 85)
        
        # =========================================================
        # STAGE 5: VIDEO COMPOSITION (FFmpeg)
        # =========================================================
        asyncio.run(job_store.update_job_status(job_id, JobStatus.COMPOSING))
        push_progress(job_id, 4, "running", "Composing final video...", 0, 88)
        
        output_filename = f"output_{job_id}.mp4"
        output_path = str(Path(settings.OUTPUT_DIR) / output_filename)
        
        compose_video(processed_frames, video_path, output_path, fps, size)
        
        push_progress(job_id, 4, "done", "Video ready!", 100, 100)
        
        # =========================================================
        # COMPLETE
        # =========================================================
        processing_time = time.time() - start_time
        output_url = f"/outputs/{output_filename}"
        
        asyncio.run(job_store.set_output(job_id, output_url, processing_time))
        
        print(f"✅ Job {job_id} completed in {processing_time:.1f}s")
        return {"status": "completed", "output_url": output_url}
    
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        print(f"❌ Job {job_id} failed: {error_msg}")
        
        asyncio.run(job_store.update_job_status(
            job_id, JobStatus.FAILED, error_message=error_msg
        ))
        push_progress(job_id, -1, "failed", f"Error: {error_msg}", 0, 0)
        
        raise  # Re-raise for Celery retry logic