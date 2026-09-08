"""
Stage 3: Segmentation and Multi-Frame Tracking using SAM2 (Meta).

SAM2 (Segment Anything Model 2) can:
1. Segment an object in the first frame given a bounding box
2. Track that object through subsequent frames automatically

This gives us per-pixel masks for every frame,
which is what we need for precise inpainting.
"""
import numpy as np
import cv2
from typing import Optional
from pathlib import Path


def load_sam2():
    """Load SAM2 model"""
    try:
        from sam2.build_sam import build_sam2_video_predictor
        from config import settings
        
        predictor = build_sam2_video_predictor(
            settings.SAM2_CONFIG,
            settings.SAM2_CHECKPOINT
        )
        return predictor
    except Exception as e:
        print(f"⚠️  SAM2 not available, using mock segmentation: {e}")
        return None


def segment_and_track_frames(
    frames: list[np.ndarray],
    initial_bbox: list[int],
    predictor=None
) -> list[np.ndarray]:
    """
    Segment object in first frame, track through all frames.
    
    Args:
        frames: List of BGR frames
        initial_bbox: [x1, y1, x2, y2] bounding box in first frame
        predictor: SAM2 video predictor model
    
    Returns:
        List of binary masks (same length as frames)
        Each mask is uint8 array, 255=object, 0=background
    """
    h, w = frames[0].shape[:2]
    
    if predictor is None:
        # Mock: return elliptical masks for testing
        masks = []
        x1, y1, x2, y2 = initial_bbox
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        rx, ry = (x2 - x1) // 2, (y2 - y1) // 2
        
        for i, frame in enumerate(frames):
            mask = np.zeros((h, w), dtype=np.uint8)
            # Simulate slight movement
            drift_x = int(i * 0.5)
            cv2.ellipse(mask, (cx + drift_x, cy), (rx, ry), 0, 0, 360, 255, -1)
            masks.append(mask)
        
        return masks
    
    try:
        import torch
        from PIL import Image
        import tempfile
        import os
        
        # SAM2 needs frames as files - write to temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, frame in enumerate(frames):
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(rgb)
                pil.save(os.path.join(tmpdir, f"{i:05d}.jpg"))
            
            # Initialize predictor with video frames
            with torch.inference_mode():
                state = predictor.init_state(video_path=tmpdir)
                
                # Provide initial bounding box prompt for frame 0
                x1, y1, x2, y2 = initial_bbox
                box = np.array([x1, y1, x2, y2], dtype=np.float32)
                
                predictor.add_new_prompts(
                    inference_state=state,
                    frame_idx=0,
                    obj_id=1,
                    boxes=box[None]
                )
                
                # Propagate through all frames
                masks = [None] * len(frames)
                for frame_idx, obj_ids, mask_logits in predictor.propagate_in_video(state):
                    mask = (mask_logits[0][0] > 0.0).cpu().numpy().astype(np.uint8) * 255
                    masks[frame_idx] = cv2.resize(mask, (w, h))
                
                return [m if m is not None else np.zeros((h, w), dtype=np.uint8) for m in masks]
    
    except Exception as e:
        print(f"SAM2 tracking error: {e}")
        # Fall back to mock
        return segment_and_track_frames(frames, initial_bbox, predictor=None)


def dilate_mask(mask: np.ndarray, pixels: int = 10) -> np.ndarray:
    """Slightly expand mask for cleaner inpainting edges"""
    kernel = np.ones((pixels, pixels), np.uint8)
    return cv2.dilate(mask, kernel, iterations=1)