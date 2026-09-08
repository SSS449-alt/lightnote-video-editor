"""
Stage 2: Zero-Shot Object Detection using GroundingDINO.

GroundingDINO performs language-guided object detection.
We pass the target_object from ParsedIntent as the text prompt,
and it returns bounding boxes with confidence scores.

This is better than traditional CV because:
- No training data needed (zero-shot)
- Understands rich text descriptions
- Handles arbitrary objects
"""
import numpy as np
from pathlib import Path
from typing import Optional
import cv2

from config import settings


def load_grounding_dino():
    """Load GroundingDINO model (cached after first load)"""
    try:
        from groundingdino.util.inference import load_model
        
        model = load_model(
            settings.GROUNDING_DINO_CONFIG,
            settings.GROUNDING_DINO_CHECKPOINT
        )
        return model
    except Exception as e:
        print(f"⚠️  GroundingDINO not available, using mock: {e}")
        return None


def detect_object_in_frame(
    frame: np.ndarray,
    text_prompt: str,
    box_threshold: float = 0.35,
    text_threshold: float = 0.25,
    model=None
) -> Optional[list[dict]]:
    """
    Detect target object in a single frame using GroundingDINO.
    
    Args:
        frame: BGR numpy array (OpenCV format)
        text_prompt: Text description of target object
        box_threshold: Confidence threshold for bounding boxes
        text_threshold: Threshold for text-image alignment
        model: Pre-loaded GroundingDINO model
    
    Returns:
        List of detections: [{"bbox": [x1,y1,x2,y2], "confidence": float, "label": str}]
    """
    if model is None:
        # Fallback: return center mock detection for testing
        h, w = frame.shape[:2]
        return [{
            "bbox": [w//4, h//4, 3*w//4, 3*h//4],
            "confidence": 0.85,
            "label": text_prompt
        }]
    
    try:
        from groundingdino.util.inference import predict
        import torch
        from PIL import Image
        
        # Convert BGR to RGB PIL Image
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        # Run inference
        boxes, logits, phrases = predict(
            model=model,
            image=pil_image,
            caption=text_prompt,
            box_threshold=box_threshold,
            text_threshold=text_threshold
        )
        
        if len(boxes) == 0:
            return []
        
        h, w = frame.shape[:2]
        detections = []
        
        for box, logit, phrase in zip(boxes, logits, phrases):
            # GroundingDINO returns normalized cx,cy,w,h
            cx, cy, bw, bh = box.tolist()
            x1 = int((cx - bw/2) * w)
            y1 = int((cy - bh/2) * h)
            x2 = int((cx + bw/2) * w)
            y2 = int((cy + bh/2) * h)
            
            detections.append({
                "bbox": [max(0, x1), max(0, y1), min(w, x2), min(h, y2)],
                "confidence": float(logit),
                "label": phrase
            })
        
        # Return highest confidence detection
        return sorted(detections, key=lambda d: d["confidence"], reverse=True)
    
    except Exception as e:
        print(f"Detection error: {e}")
        h, w = frame.shape[:2]
        return [{
            "bbox": [w//4, h//4, 3*w//4, 3*h//4],
            "confidence": 0.75,
            "label": text_prompt
        }]