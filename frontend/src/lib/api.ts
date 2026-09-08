/**
 * API client for LightnoteAI Video Editor backend.
 * Centralizes all HTTP calls and WebSocket management.
 */
import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

// --- Types ---

export interface ParsedIntent {
  operation: string;
  target_object: string;
  replacement: string | null;
  color: string | null;
  confidence: number;
  raw_prompt: string;
  explanation: string;
}

export interface PipelineStage {
  name: string;
  status: "pending" | "running" | "done" | "failed";
  message: string;
  progress: number;
}

export interface Job {
  job_id: string;
  status: string;
  prompt: string;
  video_filename: string;
  reference_image_filename: string | null;
  parsed_intent: ParsedIntent | null;
  stages: PipelineStage[];
  output_video_url: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  processing_time_seconds: number | null;
}

export interface CreateJobResponse {
  job_id: string;
  status: string;
  message: string;
  websocket_url: string;
  poll_url: string;
}

// --- API Functions ---

export async function createJob(
  video: File,
  prompt: string,
  referenceImage?: File | null
): Promise<CreateJobResponse> {
  const formData = new FormData();
  formData.append("video", video);
  formData.append("prompt", prompt);
  if (referenceImage) {
    formData.append("reference_image", referenceImage);
  }

  const response = await api.post<CreateJobResponse>("/api/v1/jobs", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

export async function getJob(jobId: string): Promise<Job> {
  const response = await api.get<Job>(`/api/v1/jobs/${jobId}`);
  return response.data;
}

export async function listJobs(limit = 10): Promise<{ jobs: Job[]; count: number }> {
  const response = await api.get(`/api/v1/jobs?limit=${limit}`);
  return response.data;
}

// --- WebSocket ---

export type WSMessage = {
  type: "connected" | "progress" | "stage_update" | "final" | "error";
  job_id: string;
  stage?: string;
  stage_index?: number;
  stage_progress?: number;
  overall_progress?: number;
  message?: string;
  job?: Job;
};

export function connectJobWebSocket(
  jobId: string,
  onMessage: (msg: WSMessage) => void,
  onError?: (err: Event) => void,
  onClose?: () => void
): WebSocket {
  const ws = new WebSocket(`${WS_URL}/ws/${jobId}`);

  ws.onmessage = (event) => {
    try {
      const data: WSMessage = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error("WS parse error:", e);
    }
  };

  ws.onerror = onError || (() => {});
  ws.onclose = onClose || (() => {});

  return ws;
}