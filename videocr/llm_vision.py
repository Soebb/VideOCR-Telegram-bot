from __future__ import annotations

import base64
import datetime
import io
import json
import os
import sys
import tempfile
import urllib.request
from typing import Any

import numpy as np
from PIL import Image

_DEBUG_ENABLED = os.environ.get("VIDEOCR_LLM_DEBUG", "") == "1"
_LLM_LOG_PATH = os.path.join(tempfile.gettempdir(), "videocr_llm_debug.log")


def _debug_log(msg: str) -> None:
    try:
        with open(_LLM_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


LLM_RECOGNITION_PROMPT = """You are processing a grid of video subtitle frames.
Frames are numbered 0 to N-1 left-to-right, top-to-bottom.
Many frames may show the same subtitle text — this is expected.

Task: Read the subtitle text in each frame. Group frames with identical text into one entry.

Return ONLY valid JSON (no markdown, no explanation):
{"entries": [
  {"text": "subtitle A", "frames": [0, 1, 2]},
  {"text": "subtitle B", "frames": [3, 4]}
]}"""


def encode_image_base64(img_array: np.ndarray, quality: int = 75) -> str:
    """Encode a numpy RGB image array as base64 JPEG string."""
    img = Image.fromarray(img_array)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def build_grid_image(frames: list[np.ndarray], max_width: int = 1920, spacing: int = 4) -> np.ndarray:
    """Build a grid image from a list of frame arrays (one per row)."""
    if not frames:
        raise ValueError("No frames to build grid from")

    if len(frames) == 1:
        return frames[0]

    h, w = frames[0].shape[:2]
    cols = max(1, (max_width + spacing) // (w + spacing))
    rows = (len(frames) + cols - 1) // cols

    canvas_h = rows * h + (rows - 1) * spacing
    canvas_w = min(len(frames), cols) * w + (min(len(frames), cols) - 1) * spacing
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

    for i, frame in enumerate(frames):
        r = i // cols
        c = i % cols
        y = r * (h + spacing)
        x = c * (w + spacing)
        fh, fw = frame.shape[:2]
        canvas[y:y + fh, x:x + fw] = frame

    return canvas


def call_llm_api(grid_image: np.ndarray, api_key: str, api_base: str, model: str,
                 lang: str = "auto", timeout: int = 120, disable_inference: bool = False,
                 image_quality: int = 75) -> dict[str, Any]:
    """Call an OpenAI-compatible Vision API with a grid image for subtitle recognition + dedup.

    Args:
        grid_image: numpy RGB array of the grid image
        api_key: API key for authentication
        api_base: Base URL of the API (e.g. "https://api.openai.com/v1")
        model: Model name (e.g. "gpt-4o", "claude-sonnet-4-20250514")
        lang: Language hint for the prompt
        timeout: Request timeout in seconds
        disable_inference: If True, disable reasoning/thinking mode for supported models
        image_quality: JPEG quality for encoding, 50-100

    Returns:
        Parsed JSON response with "entries" key
    """
    b64_image = encode_image_base64(grid_image, quality=image_quality)

    lang_hint = ""
    if lang and lang != "auto":
        lang_hint = f"\nSubtitle language hint: {lang}"

    prompt = LLM_RECOGNITION_PROMPT + lang_hint

    # Normalize api_base - remove trailing slash
    api_base = api_base.rstrip('/')

    # Determine if this is Anthropic or OpenAI-compatible
    is_anthropic = "anthropic" in api_base or "claude" in model.lower()

    if is_anthropic:
        return _call_anthropic_api(b64_image, prompt, api_key, api_base, model, timeout, disable_inference)
    else:
        return _call_openai_api(b64_image, prompt, api_key, api_base, model, timeout, disable_inference)


def _call_openai_api(b64_image: str, prompt: str, api_key: str, api_base: str,
                     model: str, timeout: int, disable_inference: bool = False) -> dict[str, Any]:
    """Call an OpenAI-compatible Vision API."""
    url = f"{api_base}/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.1
    }

    # Disable reasoning/inference mode for supported models (o1, o3, etc.)
    if disable_inference:
        model_lower = model.lower()
        if model_lower.startswith("o1") or model_lower.startswith("o3") or model_lower.startswith("o4"):
            payload["reasoning_effort"] = "low"
        # For other models, no special parameter needed

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    return _send_request(url, payload, headers, timeout)


def _call_anthropic_api(b64_image: str, prompt: str, api_key: str, api_base: str,
                        model: str, timeout: int, disable_inference: bool = False) -> dict[str, Any]:
    """Call the Anthropic Messages API."""
    url = f"{api_base}/messages"

    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64_image
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ]
    }

    # Disable extended thinking for Anthropic models
    if disable_inference:
        payload["thinking"] = {"type": "disabled"}

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    return _send_request(url, payload, headers, timeout)


def _send_request(url: str, payload: dict[str, Any], headers: dict[str, str],
                  timeout: int) -> dict[str, Any]:
    """Send HTTP request and parse the response."""
    if _DEBUG_ENABLED:
        _debug_log(f"=== LLM API Request ===")
        _debug_log(f"Request URL: {url}")
        _debug_log(f"Model: {payload.get('model', 'N/A')}")

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            response_body = resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        if _DEBUG_ENABLED:
            _debug_log(f"HTTP Error {e.code}: {error_body[:500]}")
        raise RuntimeError(f"LLM API HTTP error {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        if _DEBUG_ENABLED:
            _debug_log(f"URL Error: {e.reason}")
        raise RuntimeError(f"LLM API connection error: {e.reason}") from e

    response_json = json.loads(response_body)

    if "choices" in response_json:
        content = response_json["choices"][0]["message"]["content"]
    elif "content" in response_json:
        content = response_json["content"][0]["text"]
    else:
        if _DEBUG_ENABLED:
            _debug_log(f"Unexpected response format: {response_body[:500]}")
        raise RuntimeError(f"Unexpected LLM API response format: {response_body[:500]}")

    if _DEBUG_ENABLED:
        _debug_log(f"LLM response content (first 500 chars): {content[:500]}")

    return _parse_llm_response(content)


def _parse_llm_response(content: str) -> dict[str, Any]:
    """Parse the LLM's JSON response, handling markdown code blocks if present."""
    text = content.strip()

    # Strip markdown code block if present
    if text.startswith("```"):
        lines = text.split('\n')
        # Remove first line (```json or ```) and last line (```)
        start = 1
        end = len(lines) - 1
        if end > 0 and lines[end].strip() == "```":
            end -= 1
        text = '\n'.join(lines[start:end + 1]).strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse LLM response as JSON: {e}\nResponse content: {content[:500]}") from e

    if "entries" not in result:
        raise RuntimeError(f"LLM response missing 'entries' key: {content[:500]}")

    return result


def llm_recognize_and_dedup(
    ssim_batches: list[list[dict[str, Any]]],
    api_key: str,
    api_base: str,
    model: str,
    lang: str = "auto",
    disable_inference: bool = False
) -> dict[int, tuple[str, float]]:
    """Recognize and deduplicate subtitle frames using a Vision LLM.

    Args:
        ssim_batches: List of SSIM-similar batches, each batch is a list of frame dicts
                     with 'img' (numpy array), 'frame_idx', 'det_score' keys.
        api_key: LLM API key
        api_base: LLM API base URL
        model: LLM model name
        lang: Language hint
        disable_inference: If True, disable reasoning/thinking mode

    Returns:
        Dict mapping frame_idx -> (text, confidence) for the best frame of each subtitle group.
        Timestamps use the first frame in each LLM-returned group.
    """
    if not ssim_batches:
        return {}

    # Flatten all batches into a single grid for the LLM
    all_frames: list[np.ndarray] = []
    frame_idx_map: list[int] = []  # maps grid position -> original frame_idx

    for batch in ssim_batches:
        for item in batch:
            all_frames.append(item["img"])
            frame_idx_map.append(item["frame_idx"])

    if not all_frames:
        return {}

    grid_image = build_grid_image(all_frames)

    llm_response = call_llm_api(grid_image, api_key, api_base, model, lang, disable_inference=disable_inference)

    # Map LLM results back to frame indices
    result: dict[int, tuple[str, float]] = {}

    for entry in llm_response.get("entries", []):
        text = entry.get("text", "")
        frames = entry.get("frames", [])
        best = entry.get("best", frames[0] if frames else 0)

        if not text or not frames:
            continue

        # Map grid positions back to original frame indices
        # Use the first frame in the group for timestamp
        original_frames = [frame_idx_map[f] for f in frames if f < len(frame_idx_map)]
        best_original = frame_idx_map[best] if best < len(frame_idx_map) else original_frames[0]

        if original_frames:
            # Use first frame's index as the timestamp anchor
            timestamp_frame = original_frames[0]
            result[timestamp_frame] = (text, 1.0)

    return result
