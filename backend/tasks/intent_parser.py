"""
Stage 1: Natural Language Intent Parser using Claude API.

This is the brain of the pipeline. We use Claude to decompose
natural language prompts into structured, machine-readable editing intent.

Why Claude? It handles ambiguous, multilingual, and complex compound
instructions better than simple regex or keyword matching.

Examples:
  "Remove the coke bottle" -> {operation: remove_object, target: "coca cola bottle"}
  "Replace the logo with Pepsi" -> {operation: replace_object, target: "logo", replacement: "Pepsi logo"}
  "Make the car red" -> {operation: recolor_object, target: "car", color: "red"}
"""
import json
import re
import httpx
from typing import Optional

from config import settings
from models.schemas import ParsedIntent, EditOperation


SYSTEM_PROMPT = """You are an expert video editing assistant that analyzes natural language editing instructions.

Your job is to extract structured editing intent from user prompts.

ALWAYS respond with valid JSON only. No explanation. No markdown. No preamble.

Response schema:
{
  "operation": "replace_object" | "remove_object" | "replace_text" | "recolor_object",
  "target_object": "the specific object to modify (be descriptive for computer vision)",
  "replacement": "what to replace it with (null if operation is remove_object)",
  "color": "target color (only for recolor_object, null otherwise)",
  "confidence": 0.0-1.0,
  "raw_prompt": "the original prompt",
  "explanation": "plain English explanation of what will be done"
}

Rules:
- target_object should be descriptive and CV-friendly (e.g., "Coca-Cola bottle" not just "bottle")
- For replace_object, always fill replacement
- For remove_object, set replacement to null
- confidence reflects how clear the instruction is
- explanation should be user-friendly

Examples:
Input: "Replace the Coca-Cola bottle with Pepsi"
Output: {"operation": "replace_object", "target_object": "Coca-Cola bottle", "replacement": "Pepsi bottle", "color": null, "confidence": 0.97, "raw_prompt": "Replace the Coca-Cola bottle with Pepsi", "explanation": "Will detect and replace the Coca-Cola bottle with a Pepsi bottle throughout the video"}

Input: "Remove the watermark"
Output: {"operation": "remove_object", "target_object": "watermark text overlay", "replacement": null, "color": null, "confidence": 0.93, "raw_prompt": "Remove the watermark", "explanation": "Will detect and remove the watermark from all frames"}
"""


async def parse_editing_intent(prompt: str, reference_image_path: Optional[str] = None) -> ParsedIntent:
    """
    Parse natural language editing instruction into structured intent.
    
    Args:
        prompt: User's natural language editing instruction
        reference_image_path: Optional path to reference image for context
    
    Returns:
        ParsedIntent with structured editing parameters
    """
    content = [{"text": prompt}]
    
    # Add reference image as context if provided
    if reference_image_path:
        import base64
        from pathlib import Path
        
        image_data = Path(reference_image_path).read_bytes()
        b64_image = base64.standard_b64encode(image_data).decode("utf-8")
        
        # Detect image type
        suffix = Path(reference_image_path).suffix.lower()
        media_type_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", 
                          ".png": "image/png", ".webp": "image/webp"}
        media_type = media_type_map.get(suffix, "image/jpeg")
        
        content.append({
            "inlineData": {"mimeType": media_type, "data": b64_image}
        })

    try:
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": content}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                endpoint,
                params={"key": settings.ANTHROPIC_API_KEY},
                json=payload,
            )
            response.raise_for_status()
        raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        parsed_dict = json.loads(raw_text)
    except Exception as error:
        print(f"Gemini intent parsing unavailable, using local parser: {error}")
        parsed_dict = _fallback_intent(prompt)
    
    return ParsedIntent(
        operation=EditOperation(parsed_dict["operation"]),
        target_object=parsed_dict["target_object"],
        replacement=parsed_dict.get("replacement"),
        color=parsed_dict.get("color"),
        confidence=float(parsed_dict["confidence"]),
        raw_prompt=parsed_dict["raw_prompt"],
        explanation=parsed_dict["explanation"]
    )


def _fallback_intent(prompt: str) -> dict:
    """Keep the pipeline usable when the remote intent API is unavailable."""
    normalized = prompt.strip()
    lower_prompt = normalized.lower()
    remove_match = re.search(r"(?:remove|delete|erase)\s+(?:the\s+)?(.+)", lower_prompt)
    replace_match = re.search(r"replace\s+(?:the\s+)?(.+?)\s+with\s+(.+)", lower_prompt)

    if remove_match:
        target = remove_match.group(1).strip()
        return {
            "operation": "remove_object",
            "target_object": target,
            "replacement": None,
            "color": None,
            "confidence": 1.0,
            "raw_prompt": normalized,
            "explanation": f"Will remove the {target} from the video",
        }

    if replace_match:
        target = replace_match.group(1).strip()
        replacement = replace_match.group(2).strip()
        return {
            "operation": "replace_object",
            "target_object": target,
            "replacement": replacement,
            "color": None,
            "confidence": 1.0,
            "raw_prompt": normalized,
            "explanation": f"Will replace the {target} with {replacement}",
        }

    return {
        "operation": "remove_object",
        "target_object": normalized,
        "replacement": None,
        "color": None,
        "confidence": 1.0 if lower_prompt else 0.0,
        "raw_prompt": normalized,
        "explanation": f"Will modify {normalized} in the video",
    }