# LightnoteAI Video Editor

> AI-powered video object editing with natural language — built for LightnoteAI technical assignment.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Gemini API](https://img.shields.io/badge/Gemini-API-blue)](https://ai.google.dev/)

---
LightNoteAI --- AI-Powered Video Object Editor

Full-Stack AI Developer Intern Technical Assignment
Natural-language video editing with object detection, segmentation,
tracking, AI-assisted replacement/removal, and asynchronous
processing.

1. Overview

LightNoteAI is an AI-powered video editing prototype that lets a
user modify an object in a video using a natural-language instruction.

Example

Input

Video: a person holding a Coca-Cola bottle

Reference image: Pepsi bottle

Instruction: Replace the Coca-Cola bottle with the Pepsi bottle.

Output

An edited MP4 in which the target object is attempted to be replaced
while preserving the rest of the video and original audio.

The system is designed around a clear separation of responsibilities:

User
 │
 ▼
Next.js Frontend
 │
 ▼
FastAPI API
 │
 ├──────────────► Claude ──────────────► Structured editing intent
 │
 ▼
Celery + Redis
 │
 ▼
Video Processing Pipeline
 │
 ├── GroundingDINO ──► Target detection
 ├── SAM2 ───────────► Segmentation + tracking
 ├── Inpainting / replacement ──► Visual modification
 └── FFmpeg + OpenCV ───────────► Final MP4
 │
 ▼
Output Video

2. Product Workflow

flowchart LR
    A["Upload Video"] --> B["Optional Reference Image"]
    B --> C["Natural-Language Prompt"]
    C --> D["Start Processing"]
    D --> E["Create Async Job"]
    E --> F["Track Progress"]
    F --> G["AI Video Pipeline"]
    G --> H["Final Edited Video"]

User-facing flow

Step                    User Action             System Result

1                       Upload video            Video is validated and
stored

2                       Add reference image     Optional replacement
visual is stored

3                       Enter instruction       Natural-language
editing request is
submitted

4                       Start processing        Backend creates a
processing job

5                       Monitor status          UI receives pipeline
progress

3. System Architecture

flowchart TB
    U["User / Browser"]

    subgraph FE["Frontend"]
        UI["Next.js 14 UI"]
        STATE["Job State / Progress UI"]
        PLAYER["Output Video Player"]
    end

    subgraph API["Backend"]
        FAST["FastAPI"]
        JOBAPI["Job API"]
        WS["WebSocket Progress"]
    end

    subgraph QUEUE["Async Processing"]
        REDIS["Redis"]
        CELERY["Celery Worker"]
    end

    subgraph AI["AI / Computer Vision Pipeline"]
        CLAUDE["Claude API<br/>Intent Parsing"]
        GDINO["GroundingDINO<br/>Zero-shot Detection"]
        SAM["SAM2<br/>Segmentation + Tracking"]
        EDIT["Inpainting / Replacement"]
        VIDEO["FFmpeg + OpenCV<br/>Video Composition"]
    end

    U --> UI
    UI --> JOBAPI
    JOBAPI --> FAST
    FAST --> REDIS
    REDIS --> CELERY
    CELERY --> CLAUDE
    CLAUDE --> GDINO
    GDINO --> SAM
    SAM --> EDIT
    EDIT --> VIDEO
    CELERY --> REDIS
    REDIS --> WS
    WS --> STATE
    VIDEO --> PLAYER
    PLAYER --> UI

4. Core AI Pipeline

The editing pipeline is intentionally divided into five stages.

flowchart TD
    P["Natural-Language Instruction"]

    S1["01 — Intent Parsing<br/>Claude API"]
    S2["02 — Object Detection<br/>GroundingDINO"]
    S3["03 — Segmentation & Tracking<br/>SAM2"]
    S4["04 — Object Editing<br/>Inpainting / Reference Replacement"]
    S5["05 — Video Composition<br/>FFmpeg + OpenCV"]

    O["Final Edited MP4"]

    P --> S1 --> S2 --> S3 --> S4 --> S5 --> O

Stage 1 --- Intent Parsing

Claude converts the user's natural-language instruction into structured
intent.

User:
"Replace the Coca-Cola bottle with Pepsi."

                │
                ▼

Claude API

                │
                ▼

{
  "operation": "replace_object",
  "target": "Coca-Cola bottle",
  "replacement": "Pepsi bottle"
}

The structured result becomes the contract between language
understanding and the downstream computer-vision pipeline.

Stage 2 --- Object Detection

GroundingDINO receives the target description as a text prompt.

Target:
"Coca-Cola bottle"

        │
        ▼

GroundingDINO

        │
        ▼

Bounding Box + Confidence

The key design reason is that the target comes from the user's language
rather than a fixed application-specific object list.

Stage 3 --- Segmentation & Tracking

The detected region is converted into a pixel-level mask and propagated
through the video using SAM2.

Frame 0
  │
  ├── Bounding Box
  │
  ▼
SAM2 Segmentation
  │
  ▼
Pixel Mask
  │
  ▼
Temporal Tracking
  │
  ├── Frame 1
  ├── Frame 2
  ├── Frame 3
  └── ...

This avoids treating every frame as an independent detection problem.

Stage 4 --- Object Editing

The mask identifies the region to modify.

Replacement

Original Frame
      │
      ▼
Target Mask
      │
      ▼
Reference / Generated Replacement
      │
      ▼
Edited Frame

Removal

Original Frame
      │
      ▼
Target Mask
      │
      ▼
Inpainting
      │
      ▼
Background-Filled Frame

The implementation can use an AI inpainting pipeline where available,
with an OpenCV-based fallback for removal and reference-image-based
replacement.

Stage 5 --- Video Composition

Processed frames are converted back into a playable video.

flowchart LR
    F["Processed Frames"]
    A["Original Audio"]
    FF["FFmpeg / OpenCV"]
    OUT["Web-Optimized MP4"]

    F --> FF
    A --> FF
    FF --> OUT

The original audio is preserved; audio editing is outside the current
scope.

5. Why These Technologies?

Component         Technology        Responsibility    Why

Frontend          Next.js 14 +      UI and job        React-based,
TypeScript        interaction       typed, practical
full-stack
integration

Styling           TailwindCSS       UI                Fast, consistent
interface

API               FastAPI           Backend           Typed Python API
orchestration     and automatic API
documentation

Job Queue         Celery            Background        Suitable for
processing        long-running
video/AI tasks

Queue / Broker    Redis             Job and progress  Lightweight
transport         infrastructure for
asynchronous work

NLP               Claude API        Intent parsing    Converts flexible
natural language
into structured
intent

Detection         GroundingDINO     Target detection  Text-conditioned
zero-shot
detection

Segmentation      SAM2              Segmentation and  Pixel-level masks
tracking          and multi-frame
propagation

Editing           Inpainting /      Object            Removes or
reference         modification      replaces masked
replacement                         content

6. End-to-End Request Lifecycle

sequenceDiagram
    participant U as User
    participant F as Next.js
    participant A as FastAPI
    participant R as Redis
    participant C as Celery
    participant AI as AI Pipeline
    participant V as Video Output

    U->>F: Upload video + reference + prompt
    F->>A: POST /api/v1/jobs
    A->>R: Create queued job
    A-->>F: job_id
    R->>C: Deliver job
    C->>AI: Parse intent
    AI->>AI: Detect target
    AI->>AI: Segment + track
    AI->>AI: Edit object
    AI->>V: Compose MP4
    C->>R: Publish progress
    R-->>A: Progress events
    A-->>F: WebSocket / polling status
    V-->>F: Output URL
    F-->>U: Preview final video

7. Asynchronous Job Processing

Video processing can take significantly longer than a normal HTTP
request. Therefore, the API creates a job instead of keeping the request
open for the complete pipeline.

HTTP Request
     │
     ▼
Create Job
     │
     ▼
job_id returned immediately
     │
     ├───────────────► Browser tracks status
     │
     ▼
Redis
     │
     ▼
Celery Worker
     │
     ▼
Long-running AI/video processing
     │
     ▼
Completed / Failed

Job lifecycle

stateDiagram-v2
    [*] --> QUEUED
    QUEUED --> PROCESSING
    PROCESSING --> COMPLETED
    PROCESSING --> FAILED
    QUEUED --> CANCELLED
    PROCESSING --> CANCELLED
    COMPLETED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]

8. Real-Time Progress

The frontend can receive live progress through WebSocket communication.

flowchart LR
    W["Celery Worker"]
    R["Redis Pub/Sub"]
    A["FastAPI WebSocket"]
    B["Browser"]

    W -->|"progress event"| R
    R -->|"event"| A
    A -->|"WebSocket"| B

Example UI state:

✓ Intent Parsing
✓ Object Detection
✓ Segmentation & Tracking
⟳ Object Editing
○ Video Composition

If WebSocket communication is unavailable, the frontend can fall back to
HTTP status polling.

9. API Design

Base API:

/api/v1

Method   Endpoint           Purpose

POST     /jobs            Create a video-editing job
GET      /jobs/{job_id}   Get job status
GET      /jobs            List recent jobs
DELETE   /jobs/{job_id}   Cancel a job
POST     /jobs/from-url   Create job from a video URL
WS       /ws/{job_id}     Stream real-time job progress

FastAPI also exposes interactive API documentation:

http://localhost:8000/docs
http://localhost:8000/redoc

10. Supported Editing Operations

User Instruction                        Operation          Reference Image

Replace the Coca-Cola with Pepsi      replace_object   Optional
Remove the bottle                     remove_object    No
Replace the logo with our brand       replace_object   Recommended
Make the car blue                     recolor_object   No
Delete the person in the background   remove_object    No

11. Fallback Strategy

The application is designed to degrade gracefully when heavyweight AI
models are unavailable.

flowchart TD
    A["Requested Editing Operation"]
    A --> B{"Required AI Model Available?"}

    B -->|"Yes"| C["AI Processing Pipeline"]
    B -->|"No"| D["Fallback Processing"]

    D --> E["OpenCV TELEA<br/>for removal"]
    D --> F["Reference-image paste<br/>for replacement"]

    C --> G["Final Composition"]
    E --> G
    F --> G

This allows the application architecture to remain demonstrable even
when a local machine does not have the hardware needed for every model.

12. Project Structure

lightnote-video-editor/
│
├── backend/
│   ├── main.py
│   ├── celery_app.py
│   ├── requirements.txt
│   ├── .env.example
│   └── ...
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── docker-compose.yml
├── README.md
└── ...

The exact structure may evolve as implementation modules are separated
further.

13. Local Setup

Prerequisites

Python 3.11+

Node.js 18+

Redis

FFmpeg

Optional CUDA-compatible GPU for faster model execution

Anthropic API key

Option A --- Docker

git clone <your-repository-url>
cd lightnote-video-editor

cp backend/.env.example backend/.env

Set:

ANTHROPIC_API_KEY=your_api_key

Then:

docker-compose up --build

Services:

Frontend   → http://localhost:3000
Backend    → http://localhost:8000
API Docs   → http://localhost:8000/docs

Option B --- Manual Setup

Backend

cd backend

python -m venv venv

Windows

venv\Scripts\activate

macOS / Linux

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Create environment file:

cp .env.example .env

Set the required API key in .env.

Start FastAPI:

uvicorn main:app --reload --port 8000

Start Celery in another terminal:

celery -A celery_app worker --loglevel=info

Frontend

Open another terminal:

cd frontend
npm install
npm run dev

Then open:

http://localhost:3000

14. Environment Variables

Example:

ANTHROPIC_API_KEY=your_api_key
REDIS_URL=redis://localhost:6379/0

Frontend/backend URLs should be configured according to the local or
deployed environment.

Security rule

Never commit .env or real API keys to GitHub.

Commit only:

.env.example

15. Error Handling

The system should treat each stage as an independently observable
operation.

Upload Validation
       │
       ▼
Job Creation
       │
       ▼
Intent Parsing
       │
       ▼
Detection
       │
       ▼
Segmentation / Tracking
       │
       ▼
Editing
       │
       ▼
Composition
       │
       ▼
Output Validation

If a stage fails:

FAILED
  │
  ├── Store error information
  ├── Stop dependent stages
  ├── Expose useful status to frontend
  └── Keep the API responsive

Useful validation includes:

supported video formats

supported image formats

file size limits

video duration limits

required prompt validation

job existence checks

missing/invalid environment variables

model/runtime failures

16. Known Limitations

This is a prototype focused on engineering approach rather than
production-level visual quality.

Processing time

CPU-only execution can take considerably longer than GPU execution.

Video length

The current implementation limits video duration/frame count to control
memory usage.

Occlusion

If the target becomes heavily occluded, tracking quality may decrease.

Fast motion

Very fast object movement can produce inconsistent masks.

Replacement quality

Without a dedicated generative/reference-conditioned editing model,
reference-based replacement may show seam or perspective artifacts.

Audio

Original audio can be preserved, but audio editing is not currently
supported.

17. Engineering Decisions

Why Celery instead of FastAPI BackgroundTasks?

Video processing and AI inference are long-running workloads.

FastAPI Request
      │
      ▼
Create Job
      │
      ▼
Celery + Redis
      │
      ▼
Worker executes heavy processing

This keeps the API responsive and provides a cleaner path toward
retries, time limits, and multiple workers.

Why GroundingDINO instead of a traditional fixed-class detector?

The application accepts arbitrary natural-language object descriptions.

User:
"Replace the red helmet."

        │
        ▼

Text-conditioned detection

        │
        ▼

Target bounding box

A text-conditioned detector better matches this interaction model than
an application restricted to a fixed object-class list.

Why Claude instead of regex?

Natural-language instructions can contain:

compound operations

ambiguous wording

different descriptions of the same object

multilingual input

additional constraints

Example:

"Remove the drink and replace the hat with a red cap."

A structured intent parser can separate these operations before the
computer-vision pipeline executes them.

Why SAM2?

Detection answers:

Where is the object?

Segmentation answers:

Which pixels belong to the object?

Tracking answers:

Where is that object in subsequent frames?

Combining these steps provides the mask sequence required for temporal
video editing.

18. Design Principles

1. Keep video processing out of the frontend.
2. Keep long-running work asynchronous.
3. Convert natural language into structured intent early.
4. Separate detection, segmentation, editing, and composition.
5. Expose processing state to the user.
6. Provide fallback behavior where practical.
7. Keep APIs versioned and predictable.
8. Validate inputs before expensive processing.
9. Never commit secrets.
10. Prefer explainable engineering decisions over unnecessary complexity.

19. Demo Scenario

The recommended demo uses:

Input Video:
Person holding Coca-Cola bottle

Reference Image:
Pepsi bottle

Prompt:
"Replace the Coca-Cola bottle with the Pepsi bottle."

Demo flow

flowchart LR
    A["Upload Video"]
    B["Upload Pepsi Reference"]
    C["Enter Prompt"]
    D["Start Processing"]
    E["Show Status"]
    F["Play Final Video"]

    A --> B --> C --> D --> E --> F

20. 2--3 Minute Demo Video

The demo video should visibly show:

Uploading the input video

Adding the optional reference image

Entering the editing prompt

Starting processing

Showing processing stages

Playing the final result

Suggested narration

"Hello, this is LightNoteAI, an AI-powered video editing application.
First, I'm uploading the input video. Next, I'm adding a Pepsi
reference image. I'll now provide the instruction: replace the
Coca-Cola bottle with the Pepsi bottle. I'll start the processing. The
backend handles the request asynchronously through the AI
video-processing pipeline. The system parses the instruction, detects
the target, segments and tracks it, applies the replacement, and
finally composes the output video. The processing is complete, and
here is the final edited result."

Keep long processing/waiting periods trimmed from the recording.

21. Interview Quick Reference

Pipeline in one sentence

Claude parses the instruction → GroundingDINO detects the target →
SAM2 segments and tracks it → the editing stage modifies the masked
region → FFmpeg composes the final video.

Backend in one sentence

FastAPI handles APIs, Celery executes long-running jobs, Redis
coordinates the queue/progress flow, and WebSocket or polling exposes
job status to the frontend.

Main engineering challenge

The difficult part is not simply generating an image; it is
maintaining a consistent target mask across video frames and turning
that temporal data into a valid final video.

Prototype trade-off

The project prioritizes a modular, explainable end-to-end pipeline
over claiming production-level visual quality.

22. Future Improvements

Possible next steps:

Reference-image conditioning
        │
        ▼
Better identity / appearance preservation

Temporal video inpainting
        │
        ▼
More consistent frame-to-frame results

Additional engineering improvements:

GPU-aware worker scheduling

object-storage integration

stronger authentication/authorization

rate limiting

persistent job metadata

richer retry policies

model health checks

automated integration tests

improved temporal consistency

production deployment with separate worker infrastructure

23. Repository Submission Checklist

Before submission:

[ ] Frontend source code
[ ] Backend source code
[ ] AI pipeline code
[ ] Worker / queue configuration
[ ] Docker configuration, if used
[ ] .env.example
[ ] README.md
[ ] No API keys or secrets committed
[ ] Local setup tested from a clean environment
[ ] Video upload tested
[ ] Reference image tested
[ ] Natural-language prompt tested
[ ] Processing status tested
[ ] Final output tested
[ ] 2–3 minute demo video recorded

24. Final Architecture Summary

                         LIGHTNOTEAI
                              │
                              ▼
                    ┌───────────────────┐
                    │ Natural Language  │
                    │ Editing Request   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Claude API      │
                    │ Intent Parsing    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  GroundingDINO    │
                    │ Object Detection  │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │       SAM2        │
                    │ Segment + Track   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Object Editing    │
                    │ Inpaint / Replace │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ FFmpeg + OpenCV   │
                    │ Video Composition │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Final Edited MP4  │
                    └───────────────────┘

       FastAPI + Celery + Redis handle the workflow
       Next.js provides the user-facing application

License

Add the license appropriate for your submission/repository.

Acknowledgement

Built as a technical assignment project for LightNote AI ---
Full-Stack AI Developer Intern.

**
The Gemini response is constrained to structured JSON with operation, target, replacement, and confidence. If the API is unavailable, the deterministic fallback still supports common remove and replace commands.
