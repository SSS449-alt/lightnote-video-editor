"""
Pydantic schemas for all API request/response models.
These define the contract between frontend and backend.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
import datetime


class EditOperation(str, Enum):
    REPLACE_OBJECT = "replace_object"
    REMOVE_OBJECT = "remove_object"
    REPLACE_TEXT = "replace_text"
    RECOLOR_OBJECT = "recolor_object"


class ParsedIntent(BaseModel):
    """Structured editing intent extracted by Claude from natural language"""
    operation: EditOperation = Field(description="Type of edit operation")
    target_object: str = Field(description="Object to be modified/removed")
    replacement: Optional[str] = Field(None, description="What to replace target with")
    color: Optional[str] = Field(None, description="Color for recolor operation")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in parsing")
    raw_prompt: str = Field(description="Original user prompt")
    explanation: str = Field(description="Human-readable explanation of what will be done")


class JobStatus(str, Enum):
    QUEUED = "queued"
    PARSING_INTENT = "parsing_intent"
    DETECTING_OBJECT = "detecting_object"
    SEGMENTING = "segmenting"
    INPAINTING = "inpainting"
    COMPOSING = "composing"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStage(BaseModel):
    name: str
    status: Literal["pending", "running", "done", "failed"]
    message: Optional[str] = None
    progress: int = 0  # 0-100


class Job(BaseModel):
    """Represents a video editing job"""
    job_id: str
    status: JobStatus
    prompt: str
    video_filename: str
    reference_image_filename: Optional[str] = None
    parsed_intent: Optional[ParsedIntent] = None
    stages: list[PipelineStage] = []
    output_video_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    processing_time_seconds: Optional[float] = None


class CreateJobRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=500)
    video_url: Optional[str] = Field(None, description="Optional YouTube/video URL instead of upload")


class JobProgressUpdate(BaseModel):
    """WebSocket message format for real-time updates"""
    type: Literal["progress", "stage_update", "final", "error"]
    job_id: str
    stage: Optional[str] = None
    stage_progress: int = 0
    overall_progress: int = 0
    message: str = ""
    data: Optional[dict] = None