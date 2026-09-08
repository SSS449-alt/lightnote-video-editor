"use client";

import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, Video, Image as ImageIcon, X, Link } from "lucide-react";
import clsx from "clsx";

interface VideoUploaderProps {
  onVideoSelect: (file: File) => void;
  onRefImageSelect: (file: File | null) => void;
  selectedVideo: File | null;
  selectedRefImage: File | null;
}

export function VideoUploader({
  onVideoSelect,
  onRefImageSelect,
  selectedVideo,
  selectedRefImage,
}: VideoUploaderProps) {
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const [refPreviewUrl, setRefPreviewUrl] = useState<string | null>(null);

  const onVideoDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        onVideoSelect(file);
        const url = URL.createObjectURL(file);
        setVideoPreviewUrl(url);
      }
    },
    [onVideoSelect]
  );

  const onRefDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        onRefImageSelect(file);
        const url = URL.createObjectURL(file);
        setRefPreviewUrl(url);
      }
    },
    [onRefImageSelect]
  );

  const { getRootProps: getVideoProps, getInputProps: getVideoInput, isDragActive: isVideoDrag } =
    useDropzone({
      onDrop: onVideoDrop,
      accept: { "video/*": [".mp4", ".webm", ".mov", ".avi"] },
      maxSize: 100 * 1024 * 1024,
      multiple: false,
    });

  const { getRootProps: getRefProps, getInputProps: getRefInput, isDragActive: isRefDrag } =
    useDropzone({
      onDrop: onRefDrop,
      accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp"] },
      maxSize: 10 * 1024 * 1024,
      multiple: false,
    });

  const clearVideo = () => {
    onVideoSelect(null as any);
    setVideoPreviewUrl(null);
  };

  const clearRef = () => {
    onRefImageSelect(null);
    setRefPreviewUrl(null);
  };

  return (
    <div className="space-y-4">
      {/* Video Upload */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
          Input Video <span className="text-[var(--error)]">*</span>
        </label>

        {selectedVideo && videoPreviewUrl ? (
          <div className="relative rounded-xl overflow-hidden border border-[var(--border)] group">
            <video
              src={videoPreviewUrl}
              className="w-full max-h-48 object-cover"
              controls
            />
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <button
                onClick={clearVideo}
                className="flex items-center gap-2 px-4 py-2 bg-[var(--error)] text-white rounded-lg text-sm font-medium"
              >
                <X size={14} /> Remove video
              </button>
            </div>
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
              <p className="text-white text-xs truncate">
                <Video size={12} className="inline mr-1" />
                {selectedVideo.name} ({(selectedVideo.size / 1024 / 1024).toFixed(1)}MB)
              </p>
            </div>
          </div>
        ) : (
          <div
            {...getVideoProps()}
            className={clsx(
              "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200",
              isVideoDrag
                ? "border-[var(--accent)] bg-[var(--accent-glow)] scale-[1.01]"
                : "border-[var(--border)] hover:border-[var(--accent)] hover:bg-[var(--surface-2)]"
            )}
          >
            <input {...getVideoInput()} />
            <div className="flex flex-col items-center gap-3">
              <div className={clsx(
                "w-14 h-14 rounded-full flex items-center justify-center transition-colors",
                isVideoDrag ? "bg-[var(--accent)]" : "bg-[var(--surface-2)]"
              )}>
                <Upload size={24} className={isVideoDrag ? "text-white" : "text-[var(--text-secondary)]"} />
              </div>
              <div>
                <p className="text-[var(--text-primary)] font-medium">
                  {isVideoDrag ? "Drop your video here" : "Upload your video"}
                </p>
                <p className="text-[var(--text-secondary)] text-sm mt-1">
                  MP4, WebM, MOV, AVI · Max 100MB
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Reference Image (Optional) */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
          Reference Image{" "}
          <span className="text-xs text-[var(--text-secondary)] font-normal ml-1">
            (optional — for guided replacement)
          </span>
        </label>

        {selectedRefImage && refPreviewUrl ? (
          <div className="relative rounded-xl overflow-hidden border border-[var(--border)] group">
            <img
              src={refPreviewUrl}
              alt="Reference"
              className="w-full max-h-32 object-cover"
            />
            <button
              onClick={clearRef}
              className="absolute top-2 right-2 p-1.5 bg-[var(--error)] text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <X size={12} />
            </button>
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2">
              <p className="text-white text-xs truncate">
                <ImageIcon size={10} className="inline mr-1" />
                {selectedRefImage.name}
              </p>
            </div>
          </div>
        ) : (
          <div
            {...getRefProps()}
            className={clsx(
              "border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-200",
              isRefDrag
                ? "border-[var(--accent)] bg-[var(--accent-glow)]"
                : "border-[var(--border)] hover:border-[var(--accent)] hover:bg-[var(--surface-2)]"
            )}
          >
            <input {...getRefInput()} />
            <div className="flex items-center gap-3 justify-center">
              <ImageIcon size={20} className="text-[var(--text-secondary)]" />
              <span className="text-[var(--text-secondary)] text-sm">
                Drop reference image or click to browse
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}