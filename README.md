# LightnoteAI Video Editor

> AI-powered video object editing with natural language — built for LightnoteAI technical assignment.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Gemini API](https://img.shields.io/badge/Gemini-API-blue)](https://ai.google.dev/)

---

Technical Design & Implementation Overview

PROJECT GOAL
Modify or replace an object in a user-uploaded video from a natural-language instruction, while keeping the AI/video workflow on the backend and exposing clear processing progress to the frontend.

Input
Video + optional reference image + natural-language editing prompt	Output
Processed, web-friendly MP4 with the requested object edit
Core AI
Claude API • GroundingDINO • SAM2 • Stable Diffusion / OpenCV fallback	Engineering
FastAPI • Celery • Redis • WebSocket • FFmpeg • Next.js 14

Prepared for LightNoteAI — Full-Stack AI Developer Intern Technical Assignment
Design focus: AI understanding • reliable backend workflow • explainable engineering decisions
 
1. Executive Overview
LightNoteAI is a prototype full-stack AI video editor that converts a natural-language editing request into a structured, asynchronous computer-vision pipeline. The application is designed around a simple user experience while keeping model orchestration, video processing, job state, and failure handling on the backend.
ONE-LINE SYSTEM STORY
Upload video → describe the edit → parse intent → detect target → segment & track → edit/inpaint → recompose video → preview result.

What the prototype demonstrates
•	Natural-language editing intent is converted into structured machine-readable instructions.
•	Arbitrary objects can be located from text without training a custom detector.
•	The selected object is segmented and tracked across video frames before modification.
•	Long-running video work is executed asynchronously instead of blocking the API request.
•	The user sees job progress and receives a final MP4 when processing completes.
•	The pipeline has a graceful fallback path for environments without the full GPU model stack.
Design principles
Functionality first
Prioritize a reliable end-to-end prototype over visual perfection.	AI where it matters
Use LLM reasoning for intent and vision models for spatial/temporal understanding.
Backend ownership
Keep model orchestration, frame processing, queues, and file generation off the client.	Graceful degradation
Use OpenCV/reference compositing when heavier models are unavailable.

2. System Architecture
The application separates interaction, orchestration, asynchronous execution, model inference, and media composition. This keeps the browser lightweight and makes the heavy workflow observable and retryable.
WEB CLIENT — Next.js 14 + TailwindCSS
↓
API LAYER — FastAPI (upload, validation, job creation, status)
↓
JOB LAYER — Redis + Celery worker
↓
AI / VIDEO PIPELINE — Claude → GroundingDINO → SAM2 → Edit/Inpaint
↓
MEDIA COMPOSITION — OpenCV + FFmpeg
↓
RESULT — Final MP4 + status metadata
WebSocket pushes progress updates; HTTP polling remains the fallback path.
3. Five-Stage AI Processing Pipeline
A single edit request is transformed through five explicit stages. Each stage has a narrow responsibility, which makes the pipeline easier to debug, explain, and extend.
Stage	Technology	Input	Output / Responsibility
1 — Intent Parsing	Claude API	Natural-language prompt	Structured JSON: operation, target, replacement, confidence
2 — Object Detection	GroundingDINO	Target text + sampled frame	Bounding box(es) + confidence
3 — Segmentation & Tracking	SAM2	Bounding box + video frames	Pixel mask propagated across frames
4 — Edit / Inpaint	Stable Diffusion / reference-guided path / OpenCV fallback	Frame + mask + replacement intent	Edited frame sequence
5 — Video Composition	FFmpeg + OpenCV	Processed frames + original media	Web-friendly MP4 with original audio preserved

Stage 1 — Natural-language intent
Example request: “Replace the Coca-Cola bottle with Pepsi.” The parser converts the sentence into a deterministic structure that downstream components can consume.
STRUCTURED INTENT
operation: replace_object   |   target: Coca-Cola bottle   |   replacement: Pepsi bottle   |   reference_image: optional

Why use an LLM instead of only regex? Real user prompts may be compound, ambiguous, or multilingual. The structured response becomes the contract between language understanding and computer vision.
Stage 2–3 — Locate, segment, and track
GroundingDINO provides zero-shot text-conditioned detection, so the target does not have to belong to a fixed application-specific class list. SAM2 then converts the selected box into a pixel mask and propagates that mask through subsequent frames.
Text target → GroundingDINO
↓
Best bounding box → SAM2
↓
Pixel mask → temporal propagation
Detection answers “where is it?”; segmentation answers “which pixels?”; tracking answers “where does it move?”
Stage 4–5 — Modify and recompose
The mask defines the region to modify. The primary path uses an inpainting/replacement strategy; a reference image can guide replacement. A lighter OpenCV TELEA/reference-paste fallback keeps the prototype usable without the complete model stack. FFmpeg then reconstructs the final MP4 and preserves the original audio where available.
4. End-to-End Request Flow
The frontend never waits synchronously for the full video edit. It receives a job identifier immediately, then tracks progress until a result URL is available.
Step	Component	What happens
1	Browser	User selects a video, optional reference image, and enters an editing prompt.
2	FastAPI	Validates files and request fields, stores upload metadata, creates a job.
3	Redis / Celery	Job is queued so the HTTP request can return quickly.
4	Celery worker	Runs intent parsing and the AI/video pipeline.
5	WebSocket / polling	Frontend receives stage, percentage, and status updates.
6	FFmpeg / output store	Processed frames are encoded into the final MP4.
7	Browser	Final result is previewed from the completed job.

Job state lifecycle
QUEUED
↓
PARSING_INTENT
↓
DETECTING
↓
TRACKING
↓
EDITING
↓
COMPOSING
↓
COMPLETED
Any stage can transition to FAILED with a user-safe message and diagnostic logs.
Progress delivery
Primary — WebSocket
FastAPI streams job progress to the browser for near real-time UI updates.	Fallback — HTTP polling
If the socket is unavailable, the client periodically calls the job-status endpoint.
Worker signal
The worker publishes progress/status events while processing each stage.	User experience
The UI remains responsive and can show the current stage instead of a frozen request.

5. Backend Engineering
FastAPI acts as the API boundary; Celery owns long-running work; Redis provides the queue/broker role and supports progress communication. This avoids tying GPU-heavy video processing to the lifetime of a single web request.
Concern	Design choice	Reason
Long-running tasks	Celery worker	Jobs can execute outside the request/response lifecycle.
Queue / broker	Redis	Lightweight coordination for asynchronous jobs and progress events.
API contract	FastAPI	Typed request handling and automatically generated OpenAPI documentation.
Live status	WebSocket + polling fallback	Responsive progress without making correctness depend on a socket.
Media processing	OpenCV + FFmpeg	Frame-level manipulation plus reliable video/audio encoding.

6. API Design
The API is job-oriented. Uploading an edit creates a job; the client then queries or subscribes to that job instead of holding a long POST request open.
Method / Route	Purpose
POST /api/v1/jobs	Create an edit job from multipart form-data.
GET /api/v1/jobs/{job_id}	Read current status, progress, errors, and result metadata.
GET /api/v1/jobs	List recent jobs.
DELETE /api/v1/jobs/{job_id}	Cancel a job when supported by the active worker state.
POST /api/v1/jobs/from-url	Bonus path: create a job from a video URL.
WS /ws/{job_id}	Receive real-time progress events.

API DOCUMENTATION
FastAPI exposes interactive OpenAPI documentation at /docs and /redoc, which makes the backend easy to inspect during evaluation.

7. Fallback & Failure Strategy
A prototype should fail predictably. The pipeline distinguishes “model-quality fallback” from “hard failure,” so limited hardware does not automatically make the application unusable.
Can full model path run?
↓
YES → GroundingDINO + SAM2 + primary edit/inpaint path
↓
NO → OpenCV TELEA for removal / reference-image compositing for replacement
↓
Recompose MP4 → return result or explicit failure
The fallback is a functional degradation path, not a claim of equivalent visual quality.
Typical error handling
Failure	Expected handling
Unsupported / corrupt file	Reject early with a clear validation error.
Target not found	Return a failed/low-confidence job state instead of editing arbitrary pixels.
Model unavailable	Use the configured fallback when possible; otherwise expose a clear failure reason.
Worker exception	Mark the job FAILED and retain logs/metadata for diagnosis.
WebSocket disconnect	Continue processing; frontend falls back to polling.
FFmpeg composition error	Do not expose a broken output; fail the job with composition diagnostics.

8. Technology Stack
Layer	Technology	Why it fits
Frontend	Next.js 14 + TailwindCSS	Fast React UI for upload, prompt, progress, and result preview.
Backend API	FastAPI	Typed async-friendly API with OpenAPI docs.
Background jobs	Celery + Redis	Non-blocking execution for heavy video/model tasks.
Real-time status	WebSocket	Immediate progress updates with polling fallback.
Intent parsing	Claude API	Transforms free-form language into structured edit intent.
Object detection	GroundingDINO	Zero-shot text-conditioned target detection.
Segmentation/tracking	SAM2	Video mask propagation from an initial spatial prompt.
Editing	Stable Diffusion / reference path / OpenCV fallback	Supports replacement/removal with graceful degradation.
Video I/O	FFmpeg + OpenCV	Reliable encoding plus frame-level processing.

9. Local Setup & Runbook
Two supported local paths are documented: Docker for the shortest setup path, and manual startup for development/debugging.
Prerequisites
•	Python 3.11+
•	Node.js 18+
•	Redis
•	FFmpeg
•	Optional CUDA-capable GPU for faster model inference
Quick start — Docker
COMMANDS
git clone <your-repo>
cd lightnote-video-editor
cp backend/.env.example backend/.env
# set ANTHROPIC_API_KEY in backend/.env
docker-compose up --build

Service	Local URL / role
Frontend	http://localhost:3000
Backend API	http://localhost:8000
API Docs	http://localhost:8000/docs
Redis	Queue/broker and progress coordination
Celery worker	Executes AI/video jobs

Manual startup — development
Terminal	Commands / purpose
1 — Backend	cd backend → create/activate venv → pip install -r requirements.txt → copy .env → uvicorn main:app --reload --port 8000
2 — Worker	cd backend → activate venv → celery -A celery_app worker --loglevel=info
3 — Frontend	cd frontend → npm install → npm run dev

DEMO CHECK
Before recording: upload a short video → add a reference image → enter the prompt → start processing → show stage progress → play the final output.

10. Supported Operations
Example prompt	Operation	Notes
Replace the Coca-Cola with Pepsi	replace_object	Reference image optional.
Remove the watermark	remove_object	Masked region is filled with surrounding/background content.
Replace the logo with our brand	replace_object + reference	Reference image is used by the replacement path.
Make the car blue	recolor_object	Object-local color transformation.
Delete the person in background	remove_object	Target is selected from free-form text.

11. Known Limitations
The prototype intentionally prioritizes technical approach and a working pipeline over production-grade visual quality. The following constraints should be communicated clearly rather than hidden.
Limitation	Impact
CPU processing time	Without GPU acceleration, video processing can take several minutes.
Video length / frame cap	Short inputs are preferred to avoid excessive memory use.
Occlusion	Tracking can degrade if the object becomes fully hidden.
Fast motion	Masks may become inconsistent on rapid movement or motion blur.
Fallback quality	Reference-paste/OpenCV modes can show seams or less realistic blending.
Audio editing	Original audio is preserved; semantic audio editing is outside scope.

12. Key Engineering Decisions
Celery over in-process background tasks
A persistent queue is more suitable for long-running video work, retries, time limits, and independent workers.	GroundingDINO over a fixed-class detector
The target comes from arbitrary user text, so zero-shot text-conditioned detection is a better fit than a project-specific fixed class list.
SAM2 for video masks
Tracking a propagated mask avoids re-detecting from scratch on every frame and improves temporal continuity.	WebSocket + polling
WebSocket improves responsiveness; polling keeps status retrieval robust when the socket is unavailable.
Explicit fallback path
The application remains demonstrable on limited hardware while clearly separating fallback quality from primary-model quality.	Job-oriented API
A job ID is a clean contract for upload, progress, cancellation, failure handling, and final result retrieval.

13. Security & Reliability Notes
•	Keep API keys in environment variables; do not commit secrets to GitHub.
•	Validate file types, extensions, and size limits before queueing work.
•	Use generated job/file names rather than trusting user-supplied paths.
•	Return user-safe error messages while keeping detailed diagnostics in server logs.
•	Treat uploaded media as untrusted input and clean temporary files according to retention policy.
•	Use request size limits and rate limiting before exposing the service publicly.
14. Future Enhancements
Enhancement	Value
IP-Adapter / stronger reference conditioning	Improve visual identity transfer from a reference image.
Temporally consistent video inpainting	Reduce frame-to-frame flicker and improve realism.
Cloud object storage	Move uploads/results from local disk to durable storage.
GPU worker pool	Scale expensive inference independently from the API.
Rate limits + auth	Safer public deployment and basic abuse protection.
Capability-aware routing / RAG	Route prompts to documented editing capabilities and explain unsupported requests more reliably.

15. Interview-Ready Explanation
30-SECOND SUMMARY
“The system uses a five-stage pipeline. Claude converts the user’s prompt into structured intent. GroundingDINO performs zero-shot target detection. SAM2 segments and tracks the object across frames. The edit stage inpaints or replaces the masked region, with an OpenCV/reference fallback when needed. FFmpeg then composes the final video. Heavy work runs asynchronously through Celery and Redis, while the frontend receives live progress through WebSocket with polling fallback.”

Likely technical questions
Question	Answer direction
Why Celery instead of FastAPI BackgroundTasks?	Video jobs can outlive one web request; a queue/worker model supports persistence, retries, time limits, and separate scaling.
Why GroundingDINO instead of YOLO?	The object is described by arbitrary user text; zero-shot text-conditioned detection avoids relying on an application-specific fixed class list.
How does progress work?	The worker emits stage/progress updates; FastAPI forwards them through WebSocket; the UI polls status if the socket fails.
Why use Claude instead of regex?	Structured LLM parsing handles ambiguity, compound instructions, and free-form language better than brittle string rules.
What happens without GPU models?	The pipeline degrades to OpenCV removal/reference compositing where possible and communicates the quality limitation.

 
16. Demo Flow (2–3 minutes)
Time	Screen action	What to say
0:00–0:15	Open LightNoteAI	“This is my AI-powered video editing prototype that modifies objects from natural-language instructions.”
0:15–0:35	Upload input video	“I am uploading a short video containing the object I want to modify.”
0:35–0:50	Add reference image	“I am also providing an optional reference image for the replacement.”
0:50–1:05	Enter prompt	“I will describe the edit in natural language: Replace the Coca-Cola bottle with the Pepsi bottle.”
1:05–1:15	Start processing	“The request is now submitted as an asynchronous backend job.”
1:15–1:50	Show processing stages	“The pipeline parses intent, detects the target, segments and tracks it, applies the edit, and composes the final video.”
1:50–2:30	Preview final output	“The processing is complete, and here is the final edited result.”

17. Final Evaluation Mapping
Evaluation area	Where this solution addresses it
AI Integration & Understanding	Structured LLM intent + zero-shot detection + video segmentation/tracking + edit pipeline.
Problem Solving	Stage separation, fallbacks, clear limitations, and robust job lifecycle.
Backend Engineering	FastAPI, Celery, Redis, typed API, asynchronous processing, failure states.
Full-Stack Implementation	Upload UI, prompt input, progress status, output preview, backend integration.
Code Quality	Modular pipeline stages, explicit API contracts, environment configuration.
Architecture Decisions	Job-oriented API, zero-shot detector, propagated masks, WebSocket/polling, fallback strategy.

FINAL POSITIONING
This is intentionally a technically strong prototype: the architecture and AI orchestration are the main deliverables, while visual output quality is treated as an improvable model-level concern rather than hidden behind frontend polish.

**
The Gemini response is constrained to structured JSON with operation, target, replacement, and confidence. If the API is unavailable, the deterministic fallback still supports common remove and replace commands.
