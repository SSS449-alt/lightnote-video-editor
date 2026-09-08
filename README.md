# LightnoteAI Video Editor

> AI-powered video object editing with natural language — built for LightnoteAI technical assignment.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Gemini API](https://img.shields.io/badge/Gemini-API-blue)](https://ai.google.dev/)

---
LightNoteAI

AI-Powered Video Object Editing with Natural Language

Turn a simple instruction like “Replace the Coca-Cola bottle with Pepsi” into an edited video.

01 · What is LightNoteAI?

LightNoteAI is a full-stack AI video editing prototype built for the LightNote AI Full-Stack AI Developer Intern Technical Assignment.

The user does not manually select frames or create masks. They simply provide a video, an optional reference image, and a natural-language instruction.

VIDEO + OPTIONAL REFERENCE IMAGE + NATURAL-LANGUAGE PROMPT
                              |
                              v
                     AI VIDEO PROCESSING
                              |
                              v
                         EDITED VIDEO

Example

Input Video
Person holding a Coca-Cola bottle

Reference Image
Pepsi bottle

Instruction
"Replace the Coca-Cola bottle with the Pepsi bottle."

                         |
                         v

Output
Edited video with the requested replacement

02 · Architecture at a Glance

+-------------------+
|       USER        |
| Video + Image +   |
| Natural Language  |
+---------+---------+
          |
          v
+-------------------+
|  NEXT.JS FRONTEND |
| Upload / Prompt   |
| Status / Preview  |
+---------+---------+
          |
          v
+-------------------+
|     FASTAPI       |
| REST API + Jobs   |
+---------+---------+
          |
          v
+-------------------+
|    CELERY +       |
|      REDIS        |
| Async Processing  |
+---------+---------+
          |
          v
+------------------------------------------+
|             AI VIDEO PIPELINE            |
|                                          |
| Claude -> GroundingDINO -> SAM2         |
|                 -> Editing -> FFmpeg     |
+----------------------+-------------------+
                       |
                       v
               +---------------+
               |   FINAL MP4   |
               | Preview/Output|
               +---------------+

Core principle: the frontend collects the request; the backend owns the complete video-processing workflow.

03 · The 5-Stage AI Pipeline

USER PROMPT
    |
    v
+-----------------------------+
| 1. INTENT PARSING           |
| Claude API                  |
| Understand what user wants  |
+--------------+--------------+
               |
               v
+-----------------------------+
| 2. OBJECT DETECTION         |
| GroundingDINO               |
| Find requested object       |
+--------------+--------------+
               |
               v
+-----------------------------+
| 3. SEGMENT + TRACK          |
| SAM2                        |
| Follow object across frames |
+--------------+--------------+
               |
               v
+-----------------------------+
| 4. OBJECT EDITING           |
| Inpainting / Replacement    |
| Modify masked region        |
+--------------+--------------+
               |
               v
+-----------------------------+
| 5. VIDEO COMPOSITION        |
| FFmpeg + OpenCV             |
| Frames + audio -> final MP4 |
+--------------+--------------+
               |
               v
          FINAL VIDEO

04 · Stage 1 — Understand the Instruction

User input:

"Replace the Coca-Cola bottle with Pepsi."

Claude converts it into structured intent:

{
  "operation": "replace_object",
  "target": "Coca-Cola bottle",
  "replacement": "Pepsi bottle"
}

This creates a clean contract between language understanding and the computer-vision pipeline.

05 · Stage 2 — Find the Target

GroundingDINO receives the target description:

"Coca-Cola bottle"
       |
       v
 GroundingDINO
       |
       v
+---------------------+
| Bounding Box        |
| + Confidence        |
+---------------------+

Text-conditioned detection matches the application's natural-language interaction model.

06 · Stage 3 — Segment and Track

SAM2 turns the detected region into a pixel-level mask and tracks it through the video.

Frame 0
   |
   v
Bounding Box
   |
   v
  SAM2
   |
   v
Object Mask
   |
   v
Track through frames
   |
   +-- Frame 1
   +-- Frame 2
   +-- Frame 3
   +-- ...

Detection answers where the object is; segmentation identifies which pixels belong to it; tracking follows it over time.

07 · Stage 4 — Modify the Object

The mask identifies the region to modify.

Replacement

Original Frame
      |
      v
  Target Mask
      |
      v
Reference / Generated Replacement
      |
      v
  Edited Frame

Removal

Original Frame
      |
      v
  Target Mask
      |
      v
   Inpainting
      |
      v
Background-filled Frame

Where heavyweight generative models are unavailable, practical fallback processing can be used.

08 · Stage 5 — Build the Final Video

Processed Frames --------+
                         |
                         v
                  +-------------+
Original Audio -->|   FFmpeg    |--> Final MP4
                  |  + OpenCV   |
                  +-------------+

The original audio can be preserved while edited visual frames are assembled into the final video.

09 · Backend Architecture

Video editing is a long-running workload, so the API does not keep the browser request open until processing finishes.

                 Browser
                    |
                    v
              +-----------+
              |  FastAPI  |
              | REST API  |
              +-----+-----+
                    |
               Create Job
                    |
                    v
              +-----------+
              |   Redis   |
              |   Queue   |
              +-----+-----+
                    |
                    v
              +-----------+
              |  Celery   |
              |   Worker  |
              +-----+-----+
                    |
                    v
              AI/Video Work

The browser receives a job_id quickly, while heavy processing continues in the background.

10 · Job Lifecycle

QUEUED
   |
   v
PROCESSING
  / \
 v   v
DONE FAILED

A job can also be cancelled before completion when supported by the implementation.

11 · Live Processing Status

Celery Worker
      |
      v
 Redis Pub/Sub
      |
      v
FastAPI WebSocket
      |
      v
   Browser
      |
      v
Progress UI

Example:

[✓] Intent Parsing
[✓] Object Detection
[✓] Segmentation & Tracking
[>] Object Editing
[ ] Video Composition

HTTP status polling can act as a fallback if WebSocket communication is unavailable.

12 · Complete Request Flow

+----------+
|   USER   |
+----+-----+
     |
     | Video + Reference + Prompt
     v
+------------+
|  FRONTEND  |
|  Next.js   |
+-----+------+
      |
      | POST /api/v1/jobs
      v
+------------+
|  FASTAPI   |
+-----+------+
      |
      | Create Job
      v
+------------+
|   REDIS    |
+-----+------+
      |
      | Queue
      v
+------------+
|   CELERY   |
|   WORKER   |
+-----+------+
      |
      v
   CLAUDE
      |
      v
GROUNDINGDINO
      |
      v
    SAM2
      |
      v
 OBJECT EDITING
      |
      v
 FFMPEG/OPENCV
      |
      v
+------------+
| FINAL VIDEO|
+-----+------+
      |
      v
+------------+
|  FRONTEND  |
|  PREVIEW   |
+------------+

13 · Technology Stack

Layer

Technology

Role

Frontend

Next.js 14 + TypeScript

User interface

Styling

TailwindCSS

UI styling

Backend

FastAPI

API + orchestration

Background Jobs

Celery

Long-running processing

Queue / Pub-Sub

Redis

Job and progress transport

Language Understanding

Claude API

Intent parsing

Object Detection

GroundingDINO

Text-conditioned detection

Segmentation / Tracking

SAM2

Masks + video tracking

Editing

Inpainting / reference replacement

Object modification

Video I/O

FFmpeg + OpenCV

Frame and video composition

14 · Project Structure

lightnote-video-editor/
|
+-- frontend/                 # Next.js application
|   +-- app/
|   +-- components/
|   +-- ...
|
+-- backend/                  # FastAPI application
|   +-- main.py
|   +-- celery_app.py
|   +-- requirements.txt
|   +-- ...
|
+-- docker-compose.yml        # Local multi-service setup
+-- README.md
+-- ...

15 · API Overview

Base path:

/api/v1

Method

Endpoint

Purpose

POST

/jobs

Create editing job

GET

/jobs/{job_id}

Get job status

GET

/jobs

List recent jobs

DELETE

/jobs/{job_id}

Cancel a job

POST

/jobs/from-url

Video URL input

WS

/ws/{job_id}

Real-time progress

API documentation:

http://localhost:8000/docs
http://localhost:8000/redoc

16 · Supported Operations

"Replace the Coca-Cola with Pepsi"
                |
                v
         replace_object

"Remove the bottle"
                |
                v
          remove_object

"Replace the logo with our brand"
                |
                v
     replace_object + reference

"Make the car blue"
                |
                v
          recolor_object

17 · Fallback Strategy

              Requested Operation
                       |
                       v
              AI Model Available?
                  /          \
                YES           NO
                 |             |
                 v             v
          AI Processing     Fallback
                               |
                       +-------+-------+
                       |               |
                       v               v
                 OpenCV TELEA    Reference Paste
                   removal        replacement
                       |               |
                       +-------+-------+
                               |
                               v
                         Final Video

The fallback path makes the prototype more practical on machines where heavyweight model execution is unavailable.

18 · Local Setup

Requirements

Python 3.11+

Node.js 18+

Redis

FFmpeg

Anthropic API key

Optional CUDA-compatible GPU

Docker

git clone <your-repository-url>
cd lightnote-video-editor
cp backend/.env.example backend/.env

Add the required API key to .env, then:

docker-compose up --build

Open:

Frontend -> http://localhost:3000
Backend  -> http://localhost:8000
Docs     -> http://localhost:8000/docs

Manual Setup

Backend

cd backend
python -m venv venv

Windows:

venv\Scripts\activate

macOS / Linux:

source venv/bin/activate

Install:

pip install -r requirements.txt

Start API:

uvicorn main:app --reload --port 8000

Start worker in another terminal:

celery -A celery_app worker --loglevel=info

Frontend

cd frontend
npm install
npm run dev

Then open:

http://localhost:3000

Replace the example commands/paths above with the exact commands used by the final repository if the implementation structure changes.

19 · Environment Variables

Example:

ANTHROPIC_API_KEY=your_api_key
REDIS_URL=redis://localhost:6379/0

Never commit:

.env
API keys
secrets
credentials

Commit:

.env.example

20 · Error Handling & Validation

File Upload
    |
    v
Validate Type / Size
    |
    v
Validate Prompt
    |
    v
Create Job
    |
    v
Run Pipeline
    |
    v
Validate Output
    |
    v
Return Result

Useful validation includes supported file types, file size/duration limits, prompt validation, job existence, environment configuration, and model/runtime failures.

21 · Known Limitations

This is a prototype focused on technical approach and end-to-end implementation, not production-level visual perfection.

CPU-only processing can be slow.

Video length/frame limits may be required for memory control.

Heavy occlusion can affect tracking.

Fast motion can produce inconsistent masks.

Reference-based replacement may show visual seams.

Original audio is preserved; audio editing is outside the current scope.

These are explicit prototype trade-offs rather than hidden limitations.

22 · Why These Choices?

Why Claude?

Natural-language instructions can be flexible or compound. A structured intent parser is more suitable than relying on simple string matching.

Why GroundingDINO?

The application needs text-conditioned object detection because users may describe arbitrary objects.

Why SAM2?

The system needs more than a bounding box. It needs a pixel-level mask and temporal tracking through the video.

Why Celery + Redis?

AI/video processing is long-running. A background worker keeps the API responsive and gives the system a clean job-processing model.

Why FFmpeg?

The final result must be a real playable video, not just a collection of processed frames.

23 · Design Principles

1. Frontend collects the request; backend owns video processing.
2. Long-running AI/video work is asynchronous.
3. Natural language is converted into structured intent early.
4. Detection, tracking, editing, and composition are separate stages.
5. Processing progress is visible to the user.
6. Practical fallback paths are available where possible.
7. API boundaries are kept clean and predictable.
8. Inputs are validated before expensive processing.
9. Secrets are never committed.
10. The prototype prioritizes a working, explainable pipeline.

24 · Demo

Example

1. Upload video
2. Upload Pepsi reference image
3. Enter:
   "Replace the Coca-Cola bottle with the Pepsi bottle."
4. Click Start Processing
5. Show processing status
6. Play final edited video

Demo flow

UPLOAD
  |
  v
REFERENCE IMAGE
  |
  v
PROMPT
  |
  v
START PROCESSING
  |
  v
LIVE STATUS
  |
  v
FINAL VIDEO

Suggested narration

“Hello, this is LightNoteAI, an AI-powered video editing application. First, I’m uploading the input video. Next, I’m adding a Pepsi reference image. I’ll now provide the instruction: replace the Coca-Cola bottle with the Pepsi bottle. I’ll start the processing. The backend handles the request asynchronously through the AI video-processing pipeline. The system parses the instruction, detects the target, segments and tracks it, applies the replacement, and finally composes the output video. The processing is complete, and here is the final edited result.”

Keep long processing/waiting periods trimmed from the recording.

25 · Interview Quick Reference

Pipeline in one sentence

Claude parses the instruction -> GroundingDINO detects the target -> SAM2 segments and tracks it -> the editing stage modifies it -> FFmpeg composes the final video.

Backend in one sentence

FastAPI handles APIs, Celery executes long-running jobs, Redis coordinates queue/progress flow, and WebSocket or polling exposes status to the frontend.

Main engineering challenge

The difficult part is maintaining a consistent target representation across video frames and turning that temporal information into a valid final video.

Prototype trade-off

The project prioritizes a modular, explainable end-to-end pipeline over claiming production-level visual quality.

26 · Future Improvements

Better Reference Conditioning
            |
            v
Better Appearance Preservation
            |
            v
More Consistent Video Inpainting

Additional improvements could include GPU-aware worker scheduling, persistent object storage, stronger authentication, rate limiting, persistent job history, model health checks, automated integration tests, and improved temporal consistency.

27 · Submission Checklist

[✓] Video upload
[✓] Reference image upload
[✓] Natural-language prompt
[✓] AI intent parsing
[✓] Object detection
[✓] Segmentation / tracking
[✓] Video modification
[✓] Backend API
[✓] Async processing
[✓] Processing status
[✓] Output video
[✓] README
[✓] Local run instructions
[ ] Final 2–3 minute demo recording
[ ] GitHub repository submission

28 · Final Architecture in One View

                         LIGHTNOTEAI
                              |
                              v
                 +------------------------+
                 | Natural-Language Input |
                 +-----------+------------+
                             |
                             v
                 +------------------------+
                 |       Claude API       |
                 |      Intent Parsing     |
                 +-----------+------------+
                             |
                             v
                 +------------------------+
                 |     GroundingDINO      |
                 |    Object Detection    |
                 +-----------+------------+
                             |
                             v
                 +------------------------+
                 |          SAM2           |
                 |    Segment + Track      |
                 +-----------+------------+
                             |
                             v
                 +------------------------+
                 |     Object Editing      |
                 |   Inpaint / Replace     |
                 +-----------+------------+
                             |
                             v
                 +------------------------+
                 |     FFmpeg + OpenCV    |
                 |    Video Composition    |
                 +-----------+------------+
                             |
                             v
                 +------------------------+
                 |      Final Edited MP4   |
                 +------------------------+

       Next.js = user experience
       FastAPI = API orchestration
       Celery + Redis = asynchronous processing

Built for the LightNote AI Technical Assignment

LightNoteAI — Natural language -> AI video editing -> final video

**
The Gemini response is constrained to structured JSON with operation, target, replacement, and confidence. If the API is unavailable, the deterministic fallback still supports common remove and replace commands.
