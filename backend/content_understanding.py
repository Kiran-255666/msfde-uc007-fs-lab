"""Azure Content Understanding client: create analyzers and extract fields from documents.

Content Understanding gives per-field values *with confidence and a source span*, which is
what makes extraction auditable - a claims handler can see which part of which document a
value came from. That traceability is why this is used for documents rather than asking a
chat model to read the PDF.
"""
from __future__ import annotations

import json
import time
from typing import Any

import requests
from azure.identity import AzureCliCredential

SCOPE = "https://cognitiveservices.azure.com/.default"
_credential = AzureCliCredential()


class ContentUnderstandingError(RuntimeError):
    pass


class ContentUnderstandingClient:
    def __init__(self, endpoint: str, api_version: str = "2025-11-01", completion_model: str = "gpt-5.5"):
        self.endpoint = endpoint.rstrip("/")
        self.api_version = api_version
        self.completion_model = completion_model

    # ------------------------------------------------------------------ plumbing
    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {_credential.get_token(SCOPE).token}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _url(self, path: str) -> str:
        return f"{self.endpoint}/contentunderstanding/{path.lstrip('/')}?api-version={self.api_version}"

    @staticmethod
    def _json(response: requests.Response) -> dict[str, Any]:
        if not response.content:
            return {}
        # Service messages can contain raw control characters.
        return json.loads(response.content.decode("utf-8", errors="replace"), strict=False)

    def _poll(self, operation_url: str, timeout_s: int = 300) -> dict[str, Any]:
        deadline = time.time() + timeout_s
        delay = 2.0
        while time.time() < deadline:
            try:
                response = requests.get(operation_url, headers=self._headers(), timeout=60)
            except requests.RequestException:
                time.sleep(delay)          # transient network problem - keep polling
                continue
            payload = self._json(response)
            status = (payload.get("status") or "").lower()
            if status in {"succeeded", "failed", "canceled"}:
                if status != "succeeded":
                    raise ContentUnderstandingError(json.dumps(payload.get("error", payload))[:600])
                return payload
            time.sleep(delay)
            delay = min(delay * 1.4, 10)
        raise ContentUnderstandingError(f"operation timed out after {timeout_s}s")

    # ------------------------------------------------------------------ analyzers
    def list_analyzers(self) -> list[str]:
        response = requests.get(self._url("analyzers"), headers=self._headers(), timeout=60)
        return [a.get("analyzerId") for a in self._json(response).get("value", [])]

    def delete_analyzer(self, analyzer_id: str) -> None:
        requests.delete(self._url(f"analyzers/{analyzer_id}"), headers=self._headers(), timeout=60)

    def create_analyzer(self, analyzer_id: str, field_schema: dict[str, Any], *,
                        base: str = "prebuilt-document", description: str = "",
                        replace: bool = True) -> dict[str, Any]:
        """Create (or replace) a custom analyzer.

        `analyzer_id` may contain letters, digits, dots and underscores - NOT hyphens.
        """
        if "-" in analyzer_id:
            raise ValueError("analyzer ids cannot contain '-': use underscores")
        if replace:
            self.delete_analyzer(analyzer_id)

        body = {
            "baseAnalyzerId": base,
            "description": description or analyzer_id,
            # models.completion must be set explicitly; the resource defaults alone are not enough
            "models": {"completion": self.completion_model},
            "config": {"returnDetails": True, "estimateFieldSourceAndConfidence": True},
            "fieldSchema": {"fields": field_schema},
        }
        response = requests.put(self._url(f"analyzers/{analyzer_id}"),
                                headers=self._headers("application/json"), json=body, timeout=120)
        if response.status_code >= 400:
            raise ContentUnderstandingError(f"{response.status_code}: {response.text[:600]}")
        operation = response.headers.get("operation-location")
        if operation:
            self._poll(operation)
        return self._json(response)

    # -------------------------------------------------------------------- analyze
    def analyze_file(self, analyzer_id: str, path: str, content_type: str = "application/pdf",
                     timeout_s: int = 300) -> dict[str, Any]:
        with open(path, "rb") as handle:
            data = handle.read()
        response = requests.post(self._url(f"analyzers/{analyzer_id}:analyzeBinary"),
                                 headers=self._headers(content_type), data=data, timeout=180)
        if response.status_code >= 400:
            raise ContentUnderstandingError(f"{response.status_code}: {response.text[:600]}")
        operation = response.headers.get("operation-location")
        if not operation:
            return self._json(response)
        return self._poll(operation, timeout_s=timeout_s)

    @staticmethod
    def flatten_fields(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Turn the analyze result into {field: {value, confidence, source}}."""
        contents = (result.get("result") or {}).get("contents") or []
        fields = contents[0].get("fields", {}) if contents else {}
        flat: dict[str, dict[str, Any]] = {}
        for name, field in fields.items():
            value = next((field[k] for k in
                          ("valueString", "valueDate", "valueNumber", "valueInteger", "valueBoolean")
                          if k in field), None)
            flat[name] = {
                "value": value,
                "confidence": field.get("confidence"),
                "source": field.get("source"),
            }
        return flat
