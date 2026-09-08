"use client";

import React, { useState } from "react";
import { Sparkles, ChevronDown } from "lucide-react";
import clsx from "clsx";

const EXAMPLE_PROMPTS = [
  "Replace the Coca-Cola bottle with Pepsi",
  "Remove the watermark from the video",
  "Replace the red car with a blue Tesla",
  "Remove the person in the background",
  "Replace the logo with our brand logo",
];

interface PromptInputProps {
  value: string;
  onChange: (val: string) => void;
  disabled?: boolean;
}

export function PromptInput({ value, onChange, disabled }: PromptInputProps) {
  const [showExamples, setShowExamples] = useState(false);

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="block text-sm font-medium text-[var(--text-secondary)]">
          Editing Instruction <span className="text-[var(--error)]">*</span>
        </label>
        <button
          type="button"
          onClick={() => setShowExamples(!showExamples)}
          className="flex items-center gap-1 text-xs text-[var(--accent)] hover:text-[var(--text-primary)] transition-colors"
        >
          <Sparkles size={12} />
          Examples
          <ChevronDown
            size={12}
            className={clsx("transition-transform", showExamples && "rotate-180")}
          />
        </button>
      </div>

      {showExamples && (
        <div className="mb-3 space-y-1">
          {EXAMPLE_PROMPTS.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => {
                onChange(example);
                setShowExamples(false);
              }}
              className="w-full text-left px-3 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)] transition-colors border border-transparent hover:border-[var(--border)]"
            >
              "{example}"
            </button>
          ))}
        </div>
      )}

      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder='e.g., "Replace the Coca-Cola bottle with Pepsi"'
          rows={3}
          maxLength={500}
          className={clsx(
            "w-full px-4 py-3 rounded-xl text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]",
            "bg-[var(--surface-2)] border transition-all resize-none",
            "focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent",
            disabled
              ? "border-[var(--border)] opacity-50 cursor-not-allowed"
              : "border-[var(--border)] hover:border-[var(--accent)]"
          )}
        />
        <div className="absolute bottom-2 right-3 text-xs text-[var(--text-secondary)]">
          {value.length}/500
        </div>
      </div>
    </div>
  );
}