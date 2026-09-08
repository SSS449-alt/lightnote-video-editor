
"use client";

import React, { useRef, useState } from "react";
import { Download, RotateCcw, CheckCircle } from "lucide-react";

interface VideoPreviewProps {
  outputUrl: string;
  prompt: string;
  processingTime?: number | string | null;
  onReset: () => void;
}

export function VideoPreview({
  outputUrl,
  prompt,
  processingTime,
  onReset,
}: VideoPreviewProps) {
  const BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fullUrl = `${BASE_URL}${outputUrl}`;
  const duration = processingTime == null ? null : Number(processingTime);
  const [isDownloading, setIsDownloading] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);

  const downloadVideo = async () => {
    setIsDownloading(true);
    try {
      const response = await fetch(fullUrl);
      if (!response.ok) throw new Error(`Download failed: ${response.status}`);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = "lightnote_output.mp4";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Video download failed:", error);
      window.open(fullUrl, "_blank", "noopener,noreferrer");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="space-y-4">

      {/* Success banner */}
      <div className="flex items-center gap-3 p-4 rounded-xl bg-[var(--success)]/10 border border-[var(--success)]/30">
        <CheckCircle
          size={20}
          className="text-[var(--success)] flex-shrink-0"
        />

        <div>
          <p className="text-sm font-medium text-[var(--success)]">
            Video processed successfully!
          </p>

          {duration != null && Number.isFinite(duration) && (
            <p className="text-xs text-[var(--text-secondary)]">
              Completed in {duration.toFixed(1)} seconds
            </p>
          )}
        </div>
      </div>

      {/* Video player */}
      <div className="relative rounded-xl overflow-hidden bg-black border border-[var(--border)]">
        <video
          ref={videoRef}
          src={fullUrl}
          className="w-full max-h-64 object-contain"
          controls
        />
      </div>

      {/* Applied instruction */}
      <div className="glass rounded-xl p-3">
        <p className="text-xs text-[var(--text-secondary)] mb-1">
          Applied instruction
        </p>

        <p className="text-sm text-[var(--text-primary)]">
          "{prompt}"
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-3">

        {/* Download button */}
        <button
          type="button"
          onClick={downloadVideo}
          disabled={isDownloading}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-[var(--accent)] hover:bg-[var(--accent)]/90 text-white rounded-xl text-sm font-medium transition-colors"
        >
          <Download size={16} />
          {isDownloading ? "Downloading..." : "Download Video"}
        </button>

        {/* New edit button */}
        <button
          type="button"
          onClick={onReset}
          className="flex items-center justify-center gap-2 px-4 py-3 glass hover:bg-[var(--surface-2)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-xl text-sm font-medium transition-colors"
        >
          <RotateCcw size={16} />
          New Edit
        </button>

      </div>
    </div>
  );
}
