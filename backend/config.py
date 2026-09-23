"""Configuration for the claims workspace. Values come from .env / the environment."""
from __future__ import annotations

import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()

# Windows consoles default to cp1252; claim text contains characters it cannot encode.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ALIAS = os.environ.get("LAB_ALIAS", "").strip().lower()
if not ALIAS or ALIAS == "changeme":
    sys.exit("Set LAB_ALIAS in your .env file before running this.")
if not re.fullmatch(r"[a-z0-9]{2,12}", ALIAS):
    sys.exit("LAB_ALIAS must be 2-12 characters, lowercase letters and digits only.")

# Shared backend
PROJECT_ENDPOINT = os.environ["PROJECT_ENDPOINT"]
FOUNDRY_ENDPOINT = os.environ["FOUNDRY_ENDPOINT"]
AOAI_ENDPOINT = os.environ["AOAI_ENDPOINT"]
SEARCH_ENDPOINT = os.environ["SEARCH_ENDPOINT"]
SEARCH_API_VERSION = os.environ.get("SEARCH_API_VERSION", "2026-08-01-preview")
CU_API_VERSION = os.environ.get("CU_API_VERSION", "2025-11-01")
STORAGE_ACCOUNT = os.environ["STORAGE_ACCOUNT"]
CLAIMS_CONTAINER = os.environ.get("CLAIMS_CONTAINER", "claims")
POLICY_CONTAINER = os.environ.get("POLICY_CONTAINER", "policies")

KB_NAME = os.environ.get("KB_NAME", "contoso-claims-kb")
KB_CONNECTION_NAME = os.environ.get("KB_CONNECTION_NAME", "contoso-claims-kb-mcp")
KB_MCP_URL = f"{SEARCH_ENDPOINT}/knowledgebases/{KB_NAME}/mcp?api-version={SEARCH_API_VERSION}"

CHAT_DEPLOYMENT = os.environ.get("CHAT_DEPLOYMENT", "gpt-5.5")
MINI_DEPLOYMENT = os.environ.get("MINI_DEPLOYMENT", "gpt-5.4-mini")
AOAI_API_VERSION = os.environ.get("AOAI_API_VERSION", "2025-04-01-preview")

# Per-participant objects
AGENT_NAME = f"claims-agent-{ALIAS}"
ANALYZER_SUFFIX = ALIAS                      # analyzer ids use underscores, never hyphens
CLAIM_TABLE = f"claims{ALIAS}"
REVIEW_TABLE = f"review{ALIAS}"

# Business rules (from the Contoso policy corpus - see CIP-CLM-200 and CIP-CLM-220)
HANDLER_AUTHORITY_LIMIT = 5000.0
CLAIM_FREQUENCY_THRESHOLD = 3                # claims in 12 months
ENHANCED_REVIEW_REPAIRERS = ["Apex Collision Center", "Northgate Bodyworks"]

REQUIRED_DOCUMENTS = {
    "Collision":       ["claim_form", "policy_schedule", "repair_estimate", "customer_statement", "damage_photo"],
    "Theft":           ["claim_form", "policy_schedule", "repair_estimate", "customer_statement", "police_report", "damage_photo"],
    "Attempted theft": ["claim_form", "policy_schedule", "repair_estimate", "customer_statement", "police_report", "damage_photo"],
    "Vandalism":       ["claim_form", "policy_schedule", "repair_estimate", "customer_statement", "police_report", "damage_photo"],
    "Weather":         ["claim_form", "policy_schedule", "repair_estimate", "customer_statement", "damage_photo"],
    "Glass":           ["claim_form", "policy_schedule", "repair_estimate", "damage_photo"],
    "Other":           ["claim_form", "policy_schedule", "repair_estimate", "customer_statement"],
}

# Indicative repair bands from CIP-CLM-220 section 4, used as a sanity check only
REPAIR_BANDS = {
    "light scuff or scratch": (300, 900),
    "shallow dent": (600, 1600),
    "bumper replacement": (1500, 3200),
    "front or rear end collision": (3000, 8000),
    "hail damage": (2500, 7000),
}


def summary() -> str:
    return (
        f"alias           : {ALIAS}\n"
        f"agent           : {AGENT_NAME}\n"
        f"analyzer suffix : {ANALYZER_SUFFIX}\n"
        f"claim table     : {CLAIM_TABLE}\n"
        f"review table    : {REVIEW_TABLE}\n"
        f"project         : {PROJECT_ENDPOINT}\n"
        f"knowledge base  : {KB_NAME}"
    )


if __name__ == "__main__":
    print(summary())
