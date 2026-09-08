"use client";

import React from "react";
import { CheckCircle, Circle, Loader, XCircle, Brain, Eye, Layers, Wand2, Film } from "lucide-react";
import clsx from "clsx";
import { PipelineStage } from "@/lib/api";

const STAGE_ICONS = [Brain, Eye, Layers, Wand2, Film];
const STAGE_COLORS = ["#6366f1", "#8b5cf6", "#a855f7", "#ec4899", "#f43f5e"];

interface ProcessingStatusProps {
  stages: PipelineStage[];
  overallProgress: number;
  parsedIntent?: {
    operation: string;
    target_object: string;
    replacement?: string | null;
    confidence: number;
    explanation: string;
  } | null;
  processingTime?: number | null;
}

export function ProcessingStatus({
  stages,
  overallProgress,
  parsedIntent,
  processingTime,
}: ProcessingStatusProps) {
  return (
    <div className="space-y-6">
      {/* Overall Progress */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-[var(--text-secondary)]">
            Overall Progress
          </span>
          <span className="text-sm font-bold text-[var(--accent)]">{overallProgress}%</span>
        </div>
        <div className="h-2 bg-[var(--surface-2)] rounded-full overflow-hidden">
          <div
            className="progress-bar h-full"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        {processingTime && (
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Completed in {processingTime.toFixed(1)}s
          </p>
        )}
      </div>

      {/* Parsed Intent Card */}
      {parsedIntent && (
        <div className="glass rounded-xl p-4 border-l-4 border-[var(--accent)]">
          <p className="text-xs text-[var(--text-secondary)] uppercase tracking-wider mb-2">
            AI Understood Your Instruction
          </p>
          <p className="text-[var(--text-primary)] text-sm font-medium mb-1">
            {parsedIntent.explanation}
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            <span className="px-2 py-0.5 bg-[var(--accent)]/20 text-[var(--accent)] text-xs rounded-full border border-[var(--accent)]/30">
              {parsedIntent.operation.replace("_", " ")}
            </span>
            <span className="px-2 py-0.5 bg-white/5 text-[var(--text-secondary)] text-xs rounded-full border border-[var(--border)]">
              Target: {parsedIntent.target_object}
            </span>
            {parsedIntent.replacement && (
              <span className="px-2 py-0.5 bg-white/5 text-[var(--text-secondary)] text-xs rounded-full border border-[var(--border)]">
                Replace with: {parsedIntent.replacement}
              </span>
            )}
            <span className="px-2 py-0.5 bg-[var(--success)]/20 text-[var(--success)] text-xs rounded-full border border-[var(--success)]/30">
              {Math.round(parsedIntent.confidence * 100)}% confident
            </span>
          </div>
        </div>
      )}

      {/* Pipeline Stages */}
      <div className="space-y-3">
        {stages.map((stage, idx) => {
          const Icon = STAGE_ICONS[idx] || Circle;
          const color = STAGE_COLORS[idx] || "#6366f1";

          return (
            <div key={stage.name} className="flex items-start gap-3">
              {/* Icon */}
              <div
                className={clsx(
                  "w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 transition-all",
                  stage.status === "done" && "bg-[var(--success)]/20 text-[var(--success)]",
                  stage.status === "running" && "animate-pulse-glow",
                  stage.status === "pending" && "bg-[var(--surface-2)] text-[var(--text-secondary)]",
                  stage.status === "failed" && "bg-[var(--error)]/20 text-[var(--error)]"
                )}
                style={stage.status === "running" ? { background: `${color}20`, color } : {}}
              >
                {stage.status === "done" && <CheckCircle size={18} />}
                {stage.status === "running" && <Loader size={18} className="animate-spin" />}
                {stage.status === "pending" && <Circle size={18} />}
                {stage.status === "failed" && <XCircle size={18} />}
              </div>

              {/* Stage info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span
                    className={clsx(
                      "text-sm font-medium",
                      stage.status === "done" && "text-[var(--success)]",
                      stage.status === "running" && "text-[var(--text-primary)]",
                      stage.status === "pending" && "text-[var(--text-secondary)]",
                      stage.status === "failed" && "text-[var(--error)]"
                    )}
                  >
                    {stage.name}
                  </span>
                  {stage.status === "running" && (
                    <span className="text-xs text-[var(--text-secondary)]">
                      {stage.progress}%
                    </span>
                  )}
                  {stage.status === "done" && (
                    <span className="text-xs text-[var(--success)]">Done</span>
                  )}
                </div>

                {stage.message && (
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5 truncate">
                    {stage.message}
                  </p>
                )}

                {stage.status === "running" && stage.progress > 0 && (
                  <div className="h-1 bg-[var(--surface-2)] rounded-full mt-2 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${stage.progress}%`,
                        background: `linear-gradient(90deg, ${color}, ${color}88)`
                      }}
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}