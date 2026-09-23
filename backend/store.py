"""Claim records and the handler review queue, backed by Azure Table Storage.

The workspace never decides a claim. It stores the prepared view and the recommendation, and
a named handler records accept / amend / reject against it (CIP-CLM-200 section 5.5).
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Any

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.data.tables import TableClient
from azure.identity import AzureCliCredential

import config as cfg

ENDPOINT = f"https://{cfg.STORAGE_ACCOUNT}.table.core.windows.net"

PREPARED = "prepared"          # waiting for a handler
ACCEPTED = "accepted"
AMENDED = "amended"
REJECTED = "rejected"
DECISIONS = (ACCEPTED, AMENDED, REJECTED)

# Table Storage entities cap each property at 64 KB, so large blocks are chunked.
_CHUNK = 30_000


def _client(table_name: str) -> TableClient:
    client = TableClient(endpoint=ENDPOINT, table_name=table_name, credential=AzureCliCredential())
    try:
        client.create_table()
    except ResourceExistsError:
        pass
    return client


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _pack(entity: dict[str, Any], key: str, value: Any) -> None:
    text = json.dumps(value, default=str)
    for index in range(0, max(len(text), 1), _CHUNK):
        entity[f"{key}_{index // _CHUNK}"] = text[index:index + _CHUNK]


def _unpack(entity: dict[str, Any], key: str) -> Any:
    parts = [entity[k] for k in sorted((k for k in entity if k.startswith(f"{key}_")),
                                       key=lambda k: int(k.rsplit("_", 1)[1]))]
    if not parts:
        return None
    try:
        return json.loads("".join(parts))
    except json.JSONDecodeError:
        return None


def save_claim(result: dict[str, Any]) -> str:
    """Store a prepared claim, replacing any previous preparation of the same claim."""
    claim_id = result["claim_id"]
    review = result.get("review") or {}
    entity: dict[str, Any] = {
        "PartitionKey": PREPARED,
        "RowKey": claim_id,
        "status": PREPARED,
        "prepared_at": _now(),
        "documents_present": ",".join(result.get("documents_present", [])),
        "finding_count": len(result.get("findings", [])),
        "critical_count": sum(1 for f in result.get("findings", []) if f["severity"] == "critical"),
        "rule_recommendation": result.get("rule_recommendation", ""),
        "agent_recommendation": review.get("recommendation", ""),
        "summary": (review.get("summary") or "")[:_CHUNK],
        "handler": "",
        "handler_note": "",
        "decided_at": "",
    }
    _pack(entity, "findings", result.get("findings", []))
    _pack(entity, "extracted", result.get("extracted", {}))
    _pack(entity, "photos", result.get("photo_assessments", []))
    _pack(entity, "review", review)

    with _client(cfg.CLAIM_TABLE) as table:
        for partition in (PREPARED, *DECISIONS):
            try:
                table.delete_entity(partition, claim_id)
            except ResourceNotFoundError:
                pass
        table.create_entity(entity)
    return claim_id


def list_claims(status: str | None = None) -> list[dict[str, Any]]:
    with _client(cfg.CLAIM_TABLE) as table:
        query = f"PartitionKey eq '{status}'" if status else None
        entities = list(table.query_entities(query) if query else table.list_entities())
    claims = []
    for entity in entities:
        claims.append({
            "claim_id": entity["RowKey"],
            "status": entity.get("status"),
            "prepared_at": entity.get("prepared_at"),
            "documents_present": (entity.get("documents_present") or "").split(","),
            "finding_count": entity.get("finding_count"),
            "critical_count": entity.get("critical_count"),
            "rule_recommendation": entity.get("rule_recommendation"),
            "agent_recommendation": entity.get("agent_recommendation"),
            "summary": entity.get("summary"),
            "handler": entity.get("handler"),
            "handler_note": entity.get("handler_note"),
            "decided_at": entity.get("decided_at"),
        })
    return sorted(claims, key=lambda c: c["claim_id"])


def get_claim(claim_id: str) -> dict[str, Any] | None:
    with _client(cfg.CLAIM_TABLE) as table:
        for entity in table.query_entities(f"RowKey eq '{claim_id}'"):
            return {
                "claim_id": entity["RowKey"],
                "status": entity.get("status"),
                "prepared_at": entity.get("prepared_at"),
                "documents_present": (entity.get("documents_present") or "").split(","),
                "rule_recommendation": entity.get("rule_recommendation"),
                "agent_recommendation": entity.get("agent_recommendation"),
                "findings": _unpack(entity, "findings") or [],
                "extracted": _unpack(entity, "extracted") or {},
                "photo_assessments": _unpack(entity, "photos") or [],
                "review": _unpack(entity, "review") or {},
                "handler": entity.get("handler"),
                "handler_note": entity.get("handler_note"),
                "decided_at": entity.get("decided_at"),
            }
    return None


def record_decision(claim_id: str, *, decision: str, handler: str, note: str = "") -> None:
    """A named handler accepts, amends or rejects the prepared claim."""
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {DECISIONS}")
    if not handler.strip():
        raise ValueError("a handler name is required - decisions are never anonymous")

    with _client(cfg.CLAIM_TABLE) as table:
        entity = next(iter(table.query_entities(f"RowKey eq '{claim_id}'")), None)
        if entity is None:
            raise KeyError(claim_id)
        old_partition = entity["PartitionKey"]
        entity.update({
            "PartitionKey": decision,
            "status": decision,
            "handler": handler.strip(),
            "handler_note": note,
            "decided_at": _now(),
        })
        table.create_entity(entity)
        table.delete_entity(old_partition, claim_id)


def counts() -> dict[str, int]:
    result = {}
    with _client(cfg.CLAIM_TABLE) as table:
        for status in (PREPARED, *DECISIONS):
            result[status] = sum(1 for _ in table.query_entities(
                f"PartitionKey eq '{status}'", select=["RowKey"]))
    return result
