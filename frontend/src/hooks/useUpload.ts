/**
 * Hook for managing video upload state and progress.
 */
import { useState, useCallback } from "react";
import { createJob, CreateJobResponse } from "@/lib/api";

interface UseUploadResult {
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
  submitJob: (video: File, prompt: string, refImage?: File | null) => Promise<CreateJobResponse | null>;
  reset: () => void;
}

export function useUpload(): UseUploadResult {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const submitJob = useCallback(async (
    video: File,
    prompt: string,
    refImage?: File | null
  ): Promise<CreateJobResponse | null> => {
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const response = await createJob(video, prompt, refImage);
      setUploadProgress(100);
      return response;
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || "Upload failed";
      setError(Array.isArray(msg) ? msg.map((e: any) => e.msg).join(", ") : msg);
      return null;
    } finally {
      setIsUploading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsUploading(false);
    setUploadProgress(0);
    setError(null);
  }, []);

  return { isUploading, uploadProgress, error, submitJob, reset };
}