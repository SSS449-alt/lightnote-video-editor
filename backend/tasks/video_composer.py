"""
Stage 5: Video Composition using FFmpeg.

Takes processed frames and reassembles them into the final video,
preserving original audio from the input video.
"""
import numpy as np
import cv2
import ffmpeg
import tempfile
import os
import uuid
from pathlib import Path


def extract_frames(video_path: str, max_frames: int = 150) -> tuple[list[np.ndarray], float, tuple]:
    """
    Extract frames from video.
    
    Returns:
        frames: List of BGR frames
        fps: Original FPS
        size: (width, height) tuple
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Limit frames to avoid memory issues
    frame_skip = max(1, total_frames // max_frames)
    
    frames = []
    frame_idx = 0
    
    while cap.isOpened() and len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_idx % frame_skip == 0:
            frames.append(frame)
        
        frame_idx += 1
    
    cap.release()
    
    return frames, fps, (width, height)


def compose_video(
    processed_frames: list[np.ndarray],
    original_video_path: str,
    output_path: str,
    fps: float,
    size: tuple
) -> str:
    """
    Compose processed frames into final video with original audio.
    
    Strategy:
    1. Write frames to temp video (no audio)
    2. Use FFmpeg to mux with original audio
    """
    width, height = size
    tmp_video = output_path + ".tmp.mp4"
    
    # Write frames
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(tmp_video, fourcc, fps, (width, height))
    
    for frame in processed_frames:
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))
        writer.write(frame)
    
    writer.release()
    
    # Mux with original audio using FFmpeg
    try:
        (
            ffmpeg
            .input(tmp_video)
            .output(
                ffmpeg.input(original_video_path).audio,
                output_path,
                vcodec="libx264",
                acodec="aac",
                crf=23,
                preset="fast",
                movflags="+faststart"  # Web-optimized
            )
            .overwrite_output()
            .run(quiet=True)
        )
        os.unlink(tmp_video)
    except (ffmpeg.Error, FileNotFoundError):
        # No audio in original, just convert
        try:
            (
                ffmpeg
                .input(tmp_video)
                .output(output_path, vcodec="libx264", crf=23, preset="fast", movflags="+faststart")
                .overwrite_output()
                .run(quiet=True)
            )
            os.unlink(tmp_video)
        except (ffmpeg.Error, FileNotFoundError):
            os.replace(tmp_video, output_path)
    
    return output_path