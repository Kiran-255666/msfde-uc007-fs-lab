"""Damage photograph analysis with a vision model.

Content Understanding gives grounded field extraction for documents. Photographs are
different: there is no text to ground against, so a vision model describes what is visible
and estimates a repair band. The band is what later lets the pipeline notice that a $6,940
estimate does not match a light scuff.
"""
from __future__ import annotations

import base64
import io
import json
import pathlib
from typing import Any

from azure.identity import AzureCliCredential, get_bearer_token_provider
from openai import AzureOpenAI
from PIL import Image

import config as cfg

_client: AzureOpenAI | None = None

PHOTO_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["vehicle_colour", "damage_area", "severity", "visible_damage",
                 "indicative_repair_band", "panel_replacement_likely", "notes"],
    "properties": {
        "vehicle_colour": {"type": "string"},
        "damage_area": {"type": "string",
                        "enum": ["Front", "Rear", "Side", "Roof", "Glass", "Underbody",
                                 "Multiple", "None visible"]},
        "severity": {"type": "string", "enum": ["none", "minor", "moderate", "severe"]},
        "visible_damage": {"type": "string", "description": "What is actually visible, in one sentence"},
        "indicative_repair_band": {
            "type": "string",
            "enum": ["300-900", "600-1600", "1500-3200", "2500-7000", "3000-8000", "unknown"],
            "description": "Indicative band from CIP-CLM-220 section 4 for the damage visible here",
        },
        "panel_replacement_likely": {"type": "boolean",
                                     "description": "Would this damage normally need a panel replaced rather than repaired?"},
        "notes": {"type": "string"},
    },
}

# TODO 2: write the instructions for assessing a damage photograph.
#
# The assessment feeds a rule that compares the repair estimate against what the photo
# actually shows, so it must be conservative and specific:
#   - describe only what is visible; never infer a cause or who was at fault
#   - never guess at damage that is out of frame
#   - say "None visible" when there is no damage in the image
#   - map the visible damage to one of the indicative bands in CIP-CLM-220 section 4
#     (read reference/policies/CIP-CLM-220 - the bands are in the table in section 4)
INSTRUCTIONS = (
    "TODO: write the photograph assessment instructions here."
)


def _get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        token_provider = get_bearer_token_provider(
            AzureCliCredential(), "https://cognitiveservices.azure.com/.default")
        _client = AzureOpenAI(azure_endpoint=cfg.AOAI_ENDPOINT,
                              azure_ad_token_provider=token_provider,
                              api_version=cfg.AOAI_API_VERSION)
    return _client


def _encode(path: str | pathlib.Path, max_side: int = 1024) -> str:
    image = Image.open(path)
    image.thumbnail((max_side, max_side))
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=82)
    return base64.b64encode(buffer.getvalue()).decode()


def analyse_photo(path: str | pathlib.Path, model: str | None = None) -> dict[str, Any]:
    """Return a structured assessment of one damage photograph."""
    client = _get_client()
    encoded = _encode(path)
    response = client.responses.create(
        model=model or cfg.CHAT_DEPLOYMENT,
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": INSTRUCTIONS},
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{encoded}"},
        ]}],
        text={"format": {"type": "json_schema", "name": "photo_assessment",
                         "strict": True, "schema": PHOTO_SCHEMA}},
    )
    try:
        assessment = json.loads(response.output_text)
    except json.JSONDecodeError:
        assessment = {"vehicle_colour": "unknown", "damage_area": "None visible",
                      "severity": "none", "visible_damage": response.output_text[:200],
                      "indicative_repair_band": "unknown",
                      "panel_replacement_likely": False,
                      "notes": "the model did not return the expected structure"}
    assessment["file"] = pathlib.Path(path).name
    return assessment


def band_ceiling(band: str) -> float | None:
    """Upper bound of an indicative band, or None when unknown."""
    if not band or band == "unknown":
        return None
    try:
        return float(band.split("-")[1])
    except (IndexError, ValueError):
        return None
