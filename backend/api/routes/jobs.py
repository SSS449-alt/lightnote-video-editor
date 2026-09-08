"""
Job management endpoints - query status, list jobs, download results.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from config import settings
from models.job_store import job_store

router = APIRouter()


@router.get("/jobs/{job_id}", summary="Get job status and details")
async def get_job(job_id: str):
    """
    Poll job status. Returns full pipeline state including
    per-stage progress, parsed intent, and output URL when done.
    """
    job = await job_store.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return job


@router.get("/jobs", summary="List recent jobs")
async def list_jobs(limit: int = 10):
    """List the most recent video editing jobs"""
    jobs = await job_store.list_recent_jobs(limit=limit)
    return {"jobs": jobs, "count": len(jobs)}


@router.delete("/jobs/{job_id}", summary="Cancel or delete a job")
async def delete_job(job_id: str):
    """Cancel a queued/running job or delete a completed job"""
    job = await job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Try to revoke Celery task
    from celery_app import celery_app
    celery_app.control.revoke(job_id, terminate=True)
    
    # Clean up files
    for filename_key in ["video_filename", "reference_image_filename", "output_video_url"]:
        filename = job.get(filename_key)
        if filename:
            for directory in [settings.UPLOAD_DIR, settings.OUTPUT_DIR]:
                filepath = Path(directory) / Path(filename).name
                if filepath.exists():
                    filepath.unlink(missing_ok=True)
    
    return {"message": f"Job {job_id} cancelled and files cleaned up"}