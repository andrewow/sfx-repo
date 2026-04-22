"""Gemini-backed tag suggester for sound effects."""

import json
import logging
import re

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

MODEL = "gemini-2.5-flash"
MAX_TAGS = 6
PROMPT_TEMPLATE = (
    "You are tagging a sound effect for a game studio's SFX library. "
    "Listen to the attached audio and return 3 to 6 short lowercase tags "
    "that describe the sound: what it is, its source, its mood, or how it "
    "might be used in a game. Prefer tags from this existing vocabulary:\n"
    "{existing}\n\n"
    "You may invent at most 2 new tags only if nothing in the vocabulary "
    "fits. Each tag should be 1-3 words. "
    "Respond with a JSON array of strings and nothing else."
)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _parse_tags(text: str) -> list[str]:
    # Strip code fences if the model added them.
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse tag list from model response: {text!r}")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, list):
        raise ValueError(f"Expected a JSON array, got {type(parsed).__name__}")

    out: list[str] = []
    seen: set[str] = set()
    for item in parsed:
        if not isinstance(item, str):
            continue
        name = item.strip().lower()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
        if len(out) >= MAX_TAGS:
            break
    return out


async def suggest_tags(audio_bytes: bytes, mime_type: str, existing_tags: list[str]) -> list[str]:
    """Ask Gemini to suggest tags for a sound effect.

    Returns a list of 3-6 lowercase tag strings, preferring those in existing_tags.
    """
    client = _get_client()
    vocab = ", ".join(sorted(existing_tags)) if existing_tags else "(no existing tags yet)"
    prompt = PROMPT_TEMPLATE.format(existing=vocab)

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            prompt,
        ],
    )
    return _parse_tags(response.text or "")
