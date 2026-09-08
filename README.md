# LightnoteAI Video Editor

> AI-powered video object editing with natural language — built for LightnoteAI technical assignment.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Gemini API](https://img.shields.io/badge/Gemini-API-blue)](https://ai.google.dev/)

---
LightNote AI — AI Video Object Editor

An AI-powered video editing application that lets users modify objects in a video using natural-language instructions.

Example

"Replace the Coca-Cola bottle with Pepsi."

The application understands the instruction, detects the target object, segments and tracks it across the video, performs the requested edit, and returns the final edited video.

01. What This Project Does

VIDEO + OPTIONAL REFERENCE IMAGE + NATURAL-LANGUAGE PROMPT
                         |
                         v
                 LIGHTNOTE AI
                         |
                         v
              EDITED VIDEO OUTPUT

Example

Input Video:
Person holding a Coca-Cola bottle

Prompt:
"Replace the Coca-Cola bottle with Pepsi"

Reference Image:
Pepsi bottle

Output:
Video with the Coca-Cola bottle replaced by Pepsi

02. Architecture at a Glance

                         USER
                          |
                          v
              +-----------------------+
              |    NEXT.JS FRONTEND   |
              | Upload / Prompt / UI  |
              +-----------+-----------+
                          |
                    REST API + WS
                          |
                          v
              +-----------------------+
              |      FASTAPI          |
              | Job / API Management  |
              +-----------+-----------+
                          |
                          v
              +-----------------------+
              |   CELERY + REDIS     |
              |  Async Job Processing |
              +-----------+-----------+
                          |
                          v
              +-----------------------+
              |    AI VIDEO PIPELINE  |
              |                       |
              | Claude                |
              | GroundingDINO         |
              | SAM2                  |
              | Editing / Inpainting  |
              | FFmpeg + OpenCV       |
              +-----------+-----------+
                          |
                          v
                 +----------------+
                 |  FINAL MP4     |
                 | Preview / Save |
                 +----------------+

Core principle: the frontend collects the request; the backend owns the complete video-processing workflow.

03. The 5-Stage AI Pipeline

User Prompt
     |
     v
+----------------------+
| 1. INTENT PARSING    |
| Claude API            |
+----------+-----------+
           |
           v
+----------------------+
| 2. OBJECT DETECTION  |
| GroundingDINO         |
+----------+-----------+
           |
           v
+----------------------+
| 3. SEGMENT + TRACK   |
| SAM2                  |
+----------+-----------+
           |
           v
+----------------------+
| 4. OBJECT EDITING    |
| Inpainting / Replace |
+----------+-----------+
           |
           v
+----------------------+
| 5. VIDEO COMPOSITION |
| FFmpeg + OpenCV      |
+----------+-----------+
           |
           v
       FINAL VIDEO

04. Stage 1 — Understand the Instruction

The user gives a natural-language editing instruction.

Example:

"Replace the Coca-Cola bottle with Pepsi."

Claude converts the instruction into structured intent that the backend can use.

Natural Language
       |
       v
   Claude API
       |
       v
Structured Intent
       |
       +--> Operation: replace
       +--> Target: Coca-Cola bottle
       +--> Replacement: Pepsi

This makes the system easier to extend than relying on hard-coded commands.

05. Stage 2 — Detect the Target Object

GroundingDINO is used for text-conditioned object detection.

Target:
"Coca-Cola bottle"

        |
        v

    GroundingDINO
        |
        v

Bounding Box
        |
        v

+-----------------------+
|       VIDEO FRAME     |
|                       |
|       [ BOTTLE ]      |
|                       |
+-----------------------+

Why GroundingDINO?

The target can come directly from the user's text instead of being limited to a fixed set of object classes.

06. Stage 3 — Segment and Track

SAM2 is used to obtain a precise object mask and track the object through the video.

Detected Object
      |
      v
     SAM2
      |
      +------> Object Mask
      |
      +------> Object Tracking
      |
      v
Object location across frames

Frame 1        Frame 2        Frame 3
+-------+      +-------+      +-------+
| [OBJ] | ---> | [OBJ] | ---> | [OBJ] |
+-------+      +-------+      +-------+
    |              |              |
    +--------------+--------------+
                   |
             tracked object

07. Stage 4 — Edit the Object

The detected and tracked mask defines the region that needs to be modified.

Replacement

Original Frame
      |
      v
Object Mask
      |
      v
Replacement Generation
      |
      v
Edited Frame

A reference image can guide the replacement when supplied by the user.

Removal

For object-removal operations, the masked region can be inpainted or processed using the available fallback strategy.

Fallback

If the advanced generation model is unavailable, the system can fall back to simpler OpenCV-based processing where appropriate.

08. Stage 5 — Compose the Final Video

After processing the frames:

Edited Frames
      |
      v
+------------------+
| FFmpeg + OpenCV  |
+------------------+
      |
      +----> Video
      |
      +----> Original Audio
      |
      v
   Final MP4

The final result is assembled into a playable video.

09. Backend Processing

Video processing is asynchronous because AI/video operations can take time.

Frontend
   |
   | POST /api/v1/jobs
   v
FastAPI
   |
   v
Create Job
   |
   v
Celery Queue <------ Redis
   |
   v
Celery Worker
   |
   v
AI Video Pipeline
   |
   v
Update Job Progress
   |
   v
Frontend

Why Celery + Redis?

It keeps heavy processing outside the web request and allows jobs to be queued, retried, and processed by workers.

10. Processing Status

The frontend can receive live progress through WebSocket communication.

Celery Worker
     |
     | progress
     v
   Redis
     |
     v
  FastAPI
     |
     | WebSocket
     v
 Next.js UI
     |
     v
Progress: 65%

HTTP polling can be used as a fallback.

11. Complete Request Flow

1. User uploads video
          |
          v
2. Optional reference image
          |
          v
3. User enters prompt
          |
          v
4. Next.js sends job to FastAPI
          |
          v
5. Celery creates background job
          |
          v
6. Claude parses the instruction
          |
          v
7. GroundingDINO detects target
          |
          v
8. SAM2 segments + tracks target
          |
          v
9. Editing / replacement is performed
          |
          v
10. FFmpeg + OpenCV compose final video
          |
          v
11. Job becomes COMPLETED
          |
          v
12. Frontend previews final MP4

12. Technology Stack

Layer

Technology

Frontend

Next.js 14, TypeScript, Tailwind CSS, shadcn/ui

Backend

FastAPI, Python

AI Intent

Claude API

Object Detection

GroundingDINO

Segmentation / Tracking

SAM2

Video Processing

FFmpeg, OpenCV

Background Jobs

Celery

Queue / State

Redis

Containerization

Docker

Communication

REST API + WebSocket

13. Project Structure

lightnote-video-editor/
|
+-- frontend/
|   +-- app/
|   +-- components/
|   +-- lib/
|   +-- public/
|   +-- package.json
|
+-- backend/
|   +-- api/
|   +-- services/
|   +-- workers/
|   +-- models/
|   +-- utils/
|   +-- main.py
|   +-- celery_app.py
|   +-- requirements.txt
|   +-- .env.example
|
+-- docker-compose.yml
+-- README.md

Adjust individual folders above to match the final repository structure.

14. API Overview

Method

Endpoint

Purpose

POST

/api/v1/jobs

Create a video-editing job

GET

/api/v1/jobs/{job_id}

Get job status

GET

/api/v1/jobs

List jobs

DELETE

/api/v1/jobs/{job_id}

Delete a job

POST

/api/v1/jobs/from-url

Create job from video URL

WS

/ws/{job_id}

Live job progress

15. Supported Operations

The pipeline is designed around natural-language editing instructions such as:

Replace an object
Remove an object
Modify an object
Use a reference image for replacement

The same architecture can be extended with additional operations without changing the complete frontend/backend design.

16. Error Handling

The application validates the request before starting heavy processing.

User Request
     |
     v
Validation
     |
     +---- Invalid ---> Clear Error Message
     |
     v
Create Job
     |
     v
Process
     |
     +---- Failure ---> Job Failed + Error Status
     |
     v
Completed

This prevents the frontend from silently waiting when a processing error occurs.

17. Why These Technologies?

Claude

Used to understand natural-language editing instructions and convert them into structured intent.

GroundingDINO

Useful for text-conditioned object detection without requiring every possible target to be a fixed model class.

SAM2

Provides object segmentation and tracking across video frames.

Celery + Redis

Suitable for long-running video/AI jobs without blocking the FastAPI request.

FFmpeg + OpenCV

Reliable tools for frame/video processing and final video composition.

18. Local Setup

Requirements

Python 3.11+
Node.js 18+
Redis
FFmpeg
Git
Optional: CUDA-compatible GPU

Backend

cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

Create:

backend/.env

Add the required API keys and configuration from:

backend/.env.example

Start FastAPI using the command defined by the final repository.

Celery Worker

Start Redis first, then start the Celery worker using the command defined by the final repository.

Frontend

cd frontend
npm install
npm run dev

Open:

http://localhost:3000

FastAPI documentation is available at:

http://localhost:8000/docs

Use the exact commands from the final repository in the submitted README.

19. Environment Variables

Example:

ANTHROPIC_API_KEY=your_key_here
REDIS_URL=your_redis_url

Other model-specific variables should be documented in .env.example.

Never commit real API keys to GitHub.

20. Fallback Strategy

The project is designed so that the complete application does not depend on a single processing technique.

Advanced AI Processing
        |
        | available
        v
  AI-based editing
        |
        v
   Final Video


If unavailable
        |
        v
OpenCV / simpler fallback
        |
        v
   Final Video

The fallback may have lower visual quality, but it keeps the workflow demonstrable.

21. Important Limitations

Video processing is computationally expensive.

GPU acceleration can significantly improve processing time.

Very fast object movement can reduce tracking quality.

Heavy occlusion can make object tracking difficult.

Simple fallback replacement may show visible seams.

The current workflow focuses on object editing rather than audio editing.

These limitations are expected for a technical prototype and provide clear areas for future improvement.

22. Design Principles

The project follows a few simple engineering principles:

Frontend
  -> User Experience

FastAPI
  -> API + Job Management

Celery
  -> Background Processing

AI Pipeline
  -> Understanding + Detection + Tracking + Editing

FFmpeg / OpenCV
  -> Final Video

Redis
  -> Queue / Progress Support

The architecture keeps responsibilities separated so that each part can be improved independently.

23. Demo Flow

The recommended demo is approximately 2–3 minutes.

Upload Video
     |
     v
Upload Reference Image
     |
     v
Enter Natural-Language Prompt
     |
     v
Start Processing
     |
     v
Show Live Progress
     |
     v
Show Final Edited Video

Demo Example

Prompt:
"Replace the Coca-Cola bottle with Pepsi."

Show:

Video upload

Reference image upload

Natural-language prompt

Start processing

Processing status

Final edited video

24. Interview Quick Reference

How does the application work?

"It is a five-stage pipeline. Claude parses the user's instruction, GroundingDINO detects the target object, SAM2 segments and tracks it, the editing stage modifies the object, and FFmpeg/OpenCV compose the final video. The complete workflow runs asynchronously using Celery and Redis."

Why not process the video in Next.js?

"Video processing is computationally heavy, so the frontend only handles the user interaction. The backend owns the AI and video-processing workflow."

Why Celery?

"The processing can take time, so Celery lets us run it as a background job instead of keeping the API request blocked."

Why GroundingDINO?

"The user can describe an object in natural language, and GroundingDINO supports text-conditioned detection."

Why SAM2?

"Detection gives us the target location, while SAM2 provides a more precise mask and tracks the object across frames."

25. Future Improvements

Possible next improvements include:

IP-Adapter
    |
    v
Better reference-image control

ProPainter
    |
    v
Improved object removal

Better temporal consistency
    |
    v
More stable video edits

Cloud Storage
    |
    v
S3 / scalable media handling

Rate Limiting
    |
    v
Production API protection

26. Final Architecture — One View

                         USER
                          |
                          v
                 +----------------+
                 | NEXT.JS UI     |
                 | Upload / Prompt|
                 +-------+--------+
                         |
                         v
                 +----------------+
                 | FASTAPI        |
                 | REST + WebSocket|
                 +-------+--------+
                         |
                         v
                 +----------------+
                 | CELERY + REDIS |
                 | Async Jobs     |
                 +-------+--------+
                         |
                         v
        +-----------------------------------+
        |          AI VIDEO PIPELINE        |
        |                                   |
        | Claude                            |
        |      -> Intent                    |
        |                                   |
        | GroundingDINO                     |
        |      -> Detection                 |
        |                                   |
        | SAM2                              |
        |      -> Segmentation + Tracking   |
        |                                   |
        | Editing / Inpainting              |
        |      -> Object Modification       |
        |                                   |
        | FFmpeg + OpenCV                   |
        |      -> Final Video               |
        +----------------+------------------+
                         |
                         v
                  +-------------+
                  | FINAL VIDEO |
                  +-------------+

27. Submission Checklist

Before submission, verify:

GitHub repository is accessible

No API keys are committed

README setup instructions match the final code

.env.example is included

Application runs locally

Video upload works

Reference image works

Natural-language prompt works

Processing status works

Final video preview works

2–3 minute demo is recorded

Architecture and limitations are documented

Project Summary

LightNote AI demonstrates an end-to-end AI video-editing workflow:

Natural Language
       +
Video
       +
Optional Reference Image
       |
       v
AI Understanding
       |
       v
Object Detection
       |
       v
Segmentation + Tracking
       |
       v
Object Editing
       |
       v
Video Composition
       |
       v
Edited Video

The goal is not only to produce an edited video, but to demonstrate a clean separation between frontend interaction, backend orchestration, asynchronous processing, AI reasoning, computer vision, and final media composition.

**
The Gemini response is constrained to structured JSON with operation, target, replacement, and confidence. If the API is unavailable, the deterministic fallback still supports common remove and replace commands.
