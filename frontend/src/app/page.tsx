"use client";

import React, { useState } from "react";
import { Sparkles, Zap, Github } from "lucide-react";
import { VideoUploader } from "@/components/VideoUploader";
import { PromptInput } from "@/components/PromptInput";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { VideoPreview } from "@/components/VideoPreview";
import { useUpload } from "@/hooks/useUpload";
import { useJobStatus } from "@/hooks/useJobStatus";

type AppState = "idle" | "uploading" | "processing" | "done" | "error";

export default function Home() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [selectedVideo, setSelectedVideo] = useState<File | null>(null);
  const [selectedRefImage, setSelectedRefImage] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);

  const { isUploading, error: uploadError, submitJob } = useUpload();
  const { job, overallProgress } = useJobStatus(jobId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedVideo || !prompt.trim()) return;

    setAppState("uploading");

    const response = await submitJob(selectedVideo, prompt.trim(), selectedRefImage);

    if (response) {
      setJobId(response.job_id);
      setAppState("processing");
    } else {
      setAppState("error");
    }
  };

  React.useEffect(() => {
    if (!job) return;
    if (job.status === "completed") {
      setAppState("done");
    } else if (job.status === "failed") {
      setAppState("error");
    }
  }, [job?.status]);

  const handleReset = () => {
    setAppState("idle");
    setSelectedVideo(null);
    setSelectedRefImage(null);
    setPrompt("");
    setJobId(null);
  };

  const canSubmit =
    selectedVideo && prompt.trim().length >= 5 && appState === "idle" && !isUploading;

  return (
    <div className="min-h-screen gradient-bg">
      <header className="border-b border-[var(--border)] bg-[var(--surface)]/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[var(--accent)] flex items-center justify-center">
              <Zap size={20} className="text-white" fill="white" />
            </div>
            <div>
              <h1 className="font-bold text-[var(--text-primary)] text-lg leading-none">
                LightnoteAI
              </h1>
              <p className="text-xs text-[var(--text-secondary)]">AI Video Editor</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--success)]/10 border border-[var(--success)]/30 text-[var(--success)] text-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
              5-Stage AI Pipeline
            </span>
            <a
              href="https://github.com"
              target="_blank"
              className="p-2 rounded-lg glass hover:bg-[var(--surface-2)] transition-colors text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              <Github size={18} />
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-[var(--accent)]/30 text-[var(--accent)] text-sm mb-4">
            <Sparkles size={14} />
            Powered by Claude · GroundingDINO · SAM2 · Stable Diffusion
          </div>
          <h2 className="text-4xl sm:text-5xl font-bold text-[var(--text-primary)] mb-4 leading-tight">
            Edit videos with{" "}
            <span className="bg-gradient-to-r from-[var(--accent)] to-purple-400 bg-clip-text text-transparent">
              natural language
            </span>
          </h2>
          <p className="text-[var(--text-secondary)] text-lg max-w-2xl mx-auto">
            Upload a video, describe your edit, and our 5-stage AI pipeline will handle the rest.
            Replace, remove, or modify any object — no editing skills required.
          </p>
        </div>

        <div className="grid lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2">
            <div className="glass rounded-2xl p-6 sticky top-24">
              <h3 className="font-semibold text-[var(--text-primary)] mb-5 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[var(--accent)] text-white text-xs flex items-center justify-center font-bold">1</span>
                Set up your edit
              </h3>

              {appState === "idle" || appState === "uploading" || appState === "error" ? (
                <form onSubmit={handleSubmit} className="space-y-5">
                  <VideoUploader
                    onVideoSelect={setSelectedVideo}
                    onRefImageSelect={setSelectedRefImage}
                    selectedVideo={selectedVideo}
                    selectedRefImage={selectedRefImage}
                  />

                  <PromptInput
                    value={prompt}
                    onChange={setPrompt}
                    disabled={isUploading}
                  />

                  {(uploadError || (appState === "error" && job?.error_message)) && (
                    <div className="p-3 rounded-xl bg-[var(--error)]/10 border border-[var(--error)]/30">
                      <p className="text-[var(--error)] text-sm">
                        {uploadError || job?.error_message}
                      </p>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={!canSubmit}
                    className="w-full py-3.5 px-6 rounded-xl font-semibold text-white transition-all duration-200 flex items-center justify-center gap-2 relative overflow-hidden disabled:opacity-40 disabled:cursor-not-allowed bg-gradient-to-r from-[var(--accent)] to-purple-500 hover:from-[var(--accent)]/90 hover:to-purple-500/90 shadow-lg shadow-[var(--accent)]/20"
                  >
                    {isUploading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Sparkles size={18} />
                        Start AI Processing
                      </>
                    )}
                  </button>
                </form>
              ) : (
                <div className="text-center py-8">
                  <div className="w-12 h-12 rounded-full bg-[var(--accent)]/20 flex items-center justify-center mx-auto mb-3">
                    <Sparkles size={24} className="text-[var(--accent)]" />
                  </div>
                  <p className="text-[var(--text-primary)] font-medium">"{prompt}"</p>
                  <p className="text-[var(--text-secondary)] text-sm mt-1">Processing your video...</p>
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-3">
            <div className="glass rounded-2xl p-6">
              <h3 className="font-semibold text-[var(--text-primary)] mb-5 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[var(--accent)] text-white text-xs flex items-center justify-center font-bold">2</span>
                {appState === "done" ? "Your edited video" : "Pipeline progress"}
              </h3>

              {appState === "idle" && (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <div className="w-20 h-20 rounded-2xl bg-[var(--surface-2)] flex items-center justify-center mb-4 border border-[var(--border)]">
                    <Zap size={32} className="text-[var(--text-secondary)]" />
                  </div>
                  <p className="text-[var(--text-primary)] font-medium">Ready to process</p>
                  <p className="text-[var(--text-secondary)] text-sm mt-1 max-w-xs">
                    Upload a video and describe your edit to see the 5-stage AI pipeline in action
                  </p>

                  <div className="mt-8 w-full max-w-sm">
                    {["Intent Parsing (Claude)", "Object Detection (GroundingDINO)", "Segmentation & Tracking (SAM2)", "Inpainting (Stable Diffusion)", "Video Composition (FFmpeg)"].map((stage, i) => (
                      <div key={stage} className="flex items-center gap-3 py-2">
                        <div className="w-6 h-6 rounded-full bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-xs text-[var(--text-secondary)] flex-shrink-0">
                          {i + 1}
                        </div>
                        <span className="text-sm text-[var(--text-secondary)] text-left">{stage}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(appState === "processing" || appState === "uploading") && job && (
                <ProcessingStatus
                  stages={typeof job.stages === "string" ? JSON.parse(job.stages) : job.stages || []}
                  overallProgress={overallProgress}
                  parsedIntent={job.parsed_intent}
                  processingTime={null}
                />
              )}

              {appState === "done" && job?.output_video_url && (
                <VideoPreview
                  outputUrl={job.output_video_url}
                  prompt={prompt}
                  processingTime={job.processing_time_seconds}
                  onReset={handleReset}
                />
              )}

              {appState === "error" && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="w-16 h-16 rounded-2xl bg-[var(--error)]/10 flex items-center justify-center mb-4 border border-[var(--error)]/30">
                    <span className="text-3xl">⚠️</span>
                  </div>
                  <p className="text-[var(--error)] font-medium">Processing failed</p>
                  <p className="text-[var(--text-secondary)] text-sm mt-1 max-w-xs">
                    {job?.error_message || "An unexpected error occurred"}
                  </p>
                  <button
                    onClick={handleReset}
                    className="mt-4 px-6 py-2.5 glass rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-sm transition-colors"
                  >
                    Try again
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="mt-12 glass rounded-2xl p-8">
          <h3 className="font-semibold text-[var(--text-primary)] mb-6 text-center">
            How the 5-Stage AI Pipeline Works
          </h3>
          <div className="grid sm:grid-cols-5 gap-4">
            {[
              { num: "01", title: "Intent Parsing", desc: "Claude API decomposes your instruction into structured JSON: operation, target object, and replacement.", color: "#6366f1" },
              { num: "02", title: "Object Detection", desc: "GroundingDINO uses zero-shot detection to find the target object in video frames using text prompts.", color: "#8b5cf6" },
              { num: "03", title: "Segmentation & Tracking", desc: "SAM2 creates precise pixel masks and tracks the object automatically across all frames.", color: "#a855f7" },
              { num: "04", title: "Inpainting", desc: "Stable Diffusion fills the masked region with either background (remove) or the replacement object.", color: "#ec4899" },
              { num: "05", title: "Composition", desc: "FFmpeg reassembles processed frames with original audio into a web-optimized output video.", color: "#f43f5e" },
            ].map((step) => (
              <div key={step.num} className="text-center">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-3 font-bold text-white text-sm"
                  style={{ background: step.color }}
                >
                  {step.num}
                </div>
                <h4 className="font-medium text-[var(--text-primary)] text-sm mb-2">{step.title}</h4>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

