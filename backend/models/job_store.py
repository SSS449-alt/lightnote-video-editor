"""
Redis-backed job state management.
Stores job metadata, pipeline progress, and results.
"""
import json
import asyncio
import datetime
from typing import Optional

import redis.asyncio as aioredis

from config import settings
from models.schemas import Job, JobStatus, PipelineStage


class JobStore:
    
    JOB_TTL = 86400  # 24 hours
    
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._redis_loop = None
    
    async def _get_redis(self) -> aioredis.Redis:
        current_loop = asyncio.get_running_loop()
        if self._redis and self._redis_loop is not current_loop:
            self._redis = None

        if not self._redis:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            self._redis_loop = current_loop
        return self._redis
    
    async def create_job(self, job_id: str, prompt: str, video_filename: str, 
                         reference_image_filename: Optional[str] = None) -> dict:
        now = datetime.datetime.utcnow().isoformat()
        job_data = {
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "prompt": prompt,
            "video_filename": video_filename,
            "reference_image_filename": reference_image_filename,
            "parsed_intent": None,
            "stages": json.dumps([
                {"name": "Intent Parsing", "status": "pending", "message": "", "progress": 0},
                {"name": "Object Detection", "status": "pending", "message": "", "progress": 0},
                {"name": "Segmentation & Tracking", "status": "pending", "message": "", "progress": 0},
                {"name": "Inpainting", "status": "pending", "message": "", "progress": 0},
                {"name": "Video Composition", "status": "pending", "message": "", "progress": 0},
            ]),
            "output_video_url": None,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
            "processing_time_seconds": None,
        }
        r = await self._get_redis()
        await r.hset(f"job:{job_id}", mapping={
            k: json.dumps(v) if isinstance(v, (dict, list)) else (v or "")
            for k, v in job_data.items()
        })
        await r.expire(f"job:{job_id}", self.JOB_TTL)
        return job_data
    
    async def get_job(self, job_id: str) -> Optional[dict]:
        r = await self._get_redis()
        data = await r.hgetall(f"job:{job_id}")
        if not data:
            return None
        for key in ["stages", "parsed_intent"]:
            if data.get(key):
                try:
                    data[key] = json.loads(data[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return data
    
    async def update_job_status(self, job_id: str, status: JobStatus, 
                                 error_message: Optional[str] = None):
        r = await self._get_redis()
        updates = {
            "status": status.value,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        if error_message:
            updates["error_message"] = error_message
        await r.hset(f"job:{job_id}", mapping=updates)
    
    async def update_stage(self, job_id: str, stage_index: int, 
                           status: str, message: str, progress: int):
        r = await self._get_redis()
        stages_raw = await r.hget(f"job:{job_id}", "stages")
        stages = json.loads(stages_raw) if stages_raw else []
        if 0 <= stage_index < len(stages):
            stages[stage_index].update({
                "status": status,
                "message": message,
                "progress": progress
            })
        await r.hset(f"job:{job_id}", mapping={
            "stages": json.dumps(stages),
            "updated_at": datetime.datetime.utcnow().isoformat()
        })
    
    async def set_parsed_intent(self, job_id: str, intent: dict):
        r = await self._get_redis()
        await r.hset(f"job:{job_id}", mapping={
            "parsed_intent": json.dumps(intent),
            "updated_at": datetime.datetime.utcnow().isoformat()
        })
    
    async def set_output(self, job_id: str, output_url: str, processing_time: float):
        r = await self._get_redis()
        await r.hset(f"job:{job_id}", mapping={
            "output_video_url": output_url,
            "processing_time_seconds": str(processing_time),
            "status": JobStatus.COMPLETED.value,
            "updated_at": datetime.datetime.utcnow().isoformat()
        })
    
    async def list_recent_jobs(self, limit: int = 10) -> list[dict]:
        r = await self._get_redis()
        keys = await r.keys("job:*")
        jobs = []
        for key in keys[:limit]:
            job_id = key.split(":")[1]
            job = await self.get_job(job_id)
            if job:
                jobs.append(job)
        return sorted(jobs, key=lambda x: x.get("created_at", ""), reverse=True)


# Singleton instance
job_store = JobStore()