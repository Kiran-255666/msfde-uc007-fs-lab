"""The claims agent: turns extracted data and rule findings into a grounded claim summary.

The agent is grounded on the Contoso policy corpus through Foundry IQ over MCP, so every
policy statement it makes is traceable. It explains findings and recommends a next step; it
never approves, declines or pays a claim (CIP-CLM-200 section 5.2).
"""
from __future__ import annotations

import json
import re
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MCPTool, PromptAgentDefinition
from azure.identity import AzureCliCredential

import config as cfg

INSTRUCTIONS = """
TODO 4: write the agent instructions.

The agent receives the extracted fields, the photo assessments and the rule findings, and
must produce a claim summary a handler can act on. Your instructions must cover:

  grounding   - use the policy knowledge base for every rule it cites, and never invent a
                name, date, amount or reference
  honesty     - say plainly when something is missing or was extracted with low confidence
  output      - a short summary, an explanation of each finding naming the conflicting
                documents and the policy rule, outstanding items, and next steps
  boundary    - never approve, decline, pay, or allege fraud (CIP-CLM-200 section 5.2,
                CIP-CLM-210 section 4.2)
  precedence  - "refer" for COVER_NOT_IN_FORCE, EXCEEDS_AUTHORITY, ESTIMATE_EVIDENCE_MISMATCH,
                REPAIRER_ENHANCED_REVIEW, CLAIM_FREQUENCY or DAMAGE_LOCATION_MISMATCH;
                "request_information" for a missing document or a date/vehicle conflict;
                "proceed" otherwise. Low confidence alone does not change the recommendation.
""".strip()

RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "findings_explained", "outstanding_items",
                 "recommended_next_steps", "recommendation", "policy_citations"],
    "properties": {
        "summary": {"type": "string", "description": "The claim in under 120 words"},
        "findings_explained": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "explanation", "policy_reference"],
                "properties": {
                    "code": {"type": "string"},
                    "explanation": {"type": "string"},
                    "policy_reference": {"type": "string",
                                         "description": "Document id and section, e.g. CIP-CLM-200 section 2.1"},
                },
            },
        },
        "outstanding_items": {"type": "array", "items": {"type": "string"}},
        "recommended_next_steps": {"type": "array", "items": {"type": "string"}},
        "recommendation": {"type": "string",
                           "enum": ["proceed", "request_information", "refer"]},
        "policy_citations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["document", "section"],
                "properties": {"document": {"type": "string"}, "section": {"type": "string"}},
            },
        },
    },
}


# Models sometimes copy retrieval markers such as "【7:1†source】" into their output.
_MARKER = re.compile(r"\s*(?:【[^】]*】|\[ref_id:\s*\d+\])")


def _strip_markers(value):
    if isinstance(value, str):
        return _MARKER.sub("", value).strip()
    if isinstance(value, list):
        return [_strip_markers(v) for v in value]
    if isinstance(value, dict):
        return {k: _strip_markers(v) for k, v in value.items()}
    return value


def build_definition(model: str | None = None) -> PromptAgentDefinition:
    policy_tool = MCPTool(
        server_label="policy_corpus",
        server_description="Contoso Insurance policy wording, claims handling standards, "
                           "fraud indicators and repair network rules.",
        server_url=cfg.KB_MCP_URL,
        project_connection_id=cfg.KB_CONNECTION_NAME,
        allowed_tools=["knowledge_base_retrieve"],
        require_approval="never",
    )
    return PromptAgentDefinition(
        model=model or cfg.CHAT_DEPLOYMENT,
        instructions=INSTRUCTIONS,
        tools=[policy_tool],
        tool_choice="required",
        text={"format": {"type": "json_schema", "name": "claim_review",
                         "strict": True, "schema": RESPONSE_SCHEMA}},
    )


def create_agent(agent_name: str | None = None, model: str | None = None) -> str:
    project = AIProjectClient(endpoint=cfg.PROJECT_ENDPOINT, credential=AzureCliCredential())
    agent = project.agents.create_version(
        agent_name=agent_name or cfg.AGENT_NAME,
        definition=build_definition(model),
    )
    return agent.name


def review_claim(claim_package: dict[str, Any], agent_name: str | None = None) -> dict[str, Any]:
    """Send one prepared claim to the agent and return its structured review."""
    project = AIProjectClient(endpoint=cfg.PROJECT_ENDPOINT, credential=AzureCliCredential())
    client = project.get_openai_client(agent_name=agent_name or cfg.AGENT_NAME)

    prompt = (
        "Prepare this claim for handler review. Use the policy knowledge base for every rule "
        "you cite.\n\n```json\n" + json.dumps(claim_package, indent=2, default=str) + "\n```"
    )
    response = client.responses.create(input=prompt)

    try:
        review = json.loads(response.output_text)
    except json.JSONDecodeError:
        review = {
            "summary": response.output_text[:600],
            "findings_explained": [],
            "outstanding_items": ["The agent did not return the expected structure."],
            "recommended_next_steps": ["Review this claim manually."],
            "recommendation": "refer",
            "policy_citations": [],
        }
    review = _strip_markers(review)
    review["_telemetry"] = {
        "response_id": response.id,
        "knowledge_base_calls": sum(1 for item in (response.output or [])
                                    if getattr(item, "type", "") == "mcp_call"),
        "input_tokens": getattr(response.usage, "input_tokens", None),
        "output_tokens": getattr(response.usage, "output_tokens", None),
    }
    return review
