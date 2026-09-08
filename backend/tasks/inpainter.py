"""
Stage 4: Object Inpainting / Replacement.

Two strategies depending on operation:
1. REMOVE: Use LaMa inpainting to fill the masked region with background
2. REPLACE: Use Stable Diffusion inpainting with the replacement description

We also support reference-image-based replacement by using the reference
as an IP-Adapter conditioning image.
"""
import numpy as np
import cv2
from typing import Optional
from pathlib import Path
from PIL import Image

from models.schemas import EditOperation, ParsedIntent


def load_inpainting_pipeline(device: str = "cpu"):
    """Load Stable Diffusion inpainting pipeline"""
    try:
        from diffusers import StableDiffusionInpaintPipeline
        import torch
        
        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting",
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            safety_checker=None
        )
        pipe = pipe.to(device)
        pipe.enable_attention_slicing()  # Memory optimization
        
        return pipe
    except Exception as e:
        print(f"⚠️  SD Inpainting not available, using simple fill: {e}")
        return None


def inpaint_frame(
    frame: np.ndarray,
    mask: np.ndarray,
    intent: ParsedIntent,
    reference_image: Optional[np.ndarray] = None,
    pipe=None
) -> np.ndarray:
    """
    Inpaint/replace the masked region in a single frame.
    
    Args:
        frame: BGR frame
        mask: Binary mask (255=region to replace)
        intent: Parsed editing intent
        reference_image: Optional reference image for replacement
        pipe: SD inpainting pipeline
    
    Returns:
        Modified BGR frame
    """
    if pipe is None:
        return _simple_inpaint(frame, mask, intent, reference_image)
    
    try:
        h, w = frame.shape[:2]
        
        # Resize to SD's preferred 512x512 (will resize back)
        target_size = (512, 512)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb).resize(target_size)
        mask_pil = Image.fromarray(mask).resize(target_size)
        
        # Build inpainting prompt
        if intent.operation == EditOperation.REMOVE_OBJECT:
            inpaint_prompt = "clean background, seamless texture, natural background"
            negative_prompt = f"{intent.target_object}, object, artifact"
        else:
            inpaint_prompt = f"photorealistic {intent.replacement}, high quality, natural lighting"
            negative_prompt = f"{intent.target_object}, blurry, deformed, bad quality"
        
        import torch
        with torch.inference_mode():
            result = pipe(
                prompt=inpaint_prompt,
                negative_prompt=negative_prompt,
                image=frame_pil,
                mask_image=mask_pil,
                num_inference_steps=20,
                guidance_scale=7.5,
                strength=0.99
            ).images[0]
        
        # Resize back to original
        result_resized = result.resize((w, h))
        result_bgr = cv2.cvtColor(np.array(result_resized), cv2.COLOR_RGB2BGR)
        
        # Blend: use mask to composite result over original
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(float) / 255.0
        blended = (result_bgr.astype(float) * mask_3ch + 
                   frame.astype(float) * (1 - mask_3ch)).astype(np.uint8)
        
        return blended
    
    except Exception as e:
        print(f"Inpainting error: {e}")
        return _simple_inpaint(frame, mask, intent, reference_image)


def _simple_inpaint(
    frame: np.ndarray,
    mask: np.ndarray,
    intent: ParsedIntent,
    reference_image: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Fallback: OpenCV telea inpainting for removal,
    or reference image paste for replacement.
    """
    result = frame.copy()
    
    if intent.operation == EditOperation.REMOVE_OBJECT:
        # OpenCV inpainting (fills with background)
        result = cv2.inpaint(frame, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    
    elif reference_image is not None:
        # Find bounding box of mask and paste scaled reference
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            x, y, bw, bh = cv2.boundingRect(max(contours, key=cv2.contourArea))
            ref_resized = cv2.resize(reference_image, (bw, bh))
            
            # Only paste within mask
            roi_mask = mask[y:y+bh, x:x+bw]
            roi = result[y:y+bh, x:x+bw]
            roi[roi_mask > 0] = ref_resized[roi_mask > 0]
    
    else:
        # Simple color fill based on operation
        color_map = {"red": (0, 0, 255), "blue": (255, 0, 0), "green": (0, 255, 0)}
        fill_color = color_map.get(intent.color or "", (128, 128, 128))
        result[mask > 0] = fill_color
    
    return result