/**
 * Custom hook for real-time job status via WebSocket with HTTP polling fallback.
 * 
 * Strategy:
 * 1. Connect WebSocket for real-time updates
 * 2. If WS fails, fall back to polling every 2s
 * 3. Auto-cleanup on unmount
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { connectJobWebSocket, getJob, Job, WSMessage } from "@/lib/api";

interface UseJobStatusResult {
  job: Job | null;
  wsMessage: WSMessage | null;
  overallProgress: number;
  isConnected: boolean;
  error: string | null;
}

export function useJobStatus(jobId: string | null): UseJobStatusResult {
  const [job, setJob] = useState<Job | null>(null);
  const [wsMessage, setWsMessage] = useState<WSMessage | null>(null);
  const [overallProgress, setOverallProgress] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refreshJob = useCallback(async (id: string) => {
    try {
      const jobData = await getJob(id);
      setJob(jobData);

      if (jobData.stages?.length) {
        const totalProgress = jobData.stages.reduce(
          (sum, stage) => sum + stage.progress,
          0
        );
        setOverallProgress(Math.round(totalProgress / jobData.stages.length));
      }

      if (["completed", "failed"].includes(jobData.status) && pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    } catch (e) {
      setError("Unable to read job status");
      console.error("Polling error:", e);
    }
  }, []);
  
  const startPolling = useCallback((id: string) => {
    if (pollIntervalRef.current) return;

    pollIntervalRef.current = setInterval(() => refreshJob(id), 2000);
  }, []);

  useEffect(() => {
    if (!jobId) return;

    refreshJob(jobId);
    startPolling(jobId);

    // Try WebSocket first
    const ws = connectJobWebSocket(
      jobId,
      (msg) => {
        setWsMessage(msg);
        setIsConnected(true);
        
        if (msg.type === "progress") {
          setOverallProgress(msg.overall_progress || 0);
        }
        
        if (msg.type === "final" && msg.job) {
          setJob(msg.job as Job);
          setOverallProgress(100);
        }
        
        // Refresh job data on any update
        getJob(jobId).then(setJob).catch(() => {});
      },
      (err) => {
        console.warn("WebSocket failed, switching to polling:", err);
        setIsConnected(false);
        startPolling(jobId);
      },
      () => {
        setIsConnected(false);
        startPolling(jobId);
      }
    );

    wsRef.current = ws;

    return () => {
      ws.close();
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [jobId, refreshJob, startPolling]);

  return { job, wsMessage, overallProgress, isConnected, error };
}