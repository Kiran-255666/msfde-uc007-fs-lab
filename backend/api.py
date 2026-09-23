"""FastAPI service behind the claims workspace.

    GET  /api/health
    GET  /api/claims                     list claims with their status
    GET  /api/claims/{id}                the full prepared claim
    GET  /api/claims/{id}/evidence       the files on file for a claim
    GET  /api/claims/{id}/file/{name}    stream one evidence file
    POST /api/claims/{id}/process        run the pipeline for a claim
    POST /api/claims/{id}/decision       a handler records accept / amend / reject

Run it:  uvicorn api:app --reload --port 8000
"""
from __future__ import annotations

import pathlib
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import config as cfg
import pipeline
import store

def _find_repo_dir(name: str) -> pathlib.Path:
    """Locate a top-level folder by walking up: the source tree and the participant
    repository nest this file at different depths."""
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / name
        if candidate.exists():
            return candidate
    return here.parent / name


DATA_DIR = _find_repo_dir("data") / "claims"

app = FastAPI(title="Contoso Claims Workspace", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

_processing: set[str] = set()


class Decision(BaseModel):
    decision: str
    handler: str
    note: str = ""


def _claim_dir(claim_id: str) -> pathlib.Path:
    # never let a claim id escape the data directory
    if not claim_id.replace("-", "").isalnum():
        raise HTTPException(400, "invalid claim id")
    path = DATA_DIR / claim_id
    if not path.is_dir():
        raise HTTPException(404, f"no evidence folder for {claim_id}")
    return path


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "alias": cfg.ALIAS, "agent": cfg.AGENT_NAME,
            "claim_table": cfg.CLAIM_TABLE, "counts": store.counts()}


@app.get("/api/claims")
def list_claims() -> dict[str, Any]:
    if not DATA_DIR.is_dir():
        raise HTTPException(500, f"claim evidence folder not found at {DATA_DIR}")
    stored = {c["claim_id"]: c for c in store.list_claims()}
    claims = []
    for folder in sorted(d for d in DATA_DIR.iterdir() if d.is_dir()):
        claim_id = folder.name
        record = stored.get(claim_id)
        claims.append(record or {
            "claim_id": claim_id, "status": "not_processed",
            "documents_present": [], "finding_count": None,
            "agent_recommendation": None, "summary": None,
        })
    return {"claims": claims, "processing": sorted(_processing)}


@app.get("/api/claims/{claim_id}")
def get_claim(claim_id: str) -> dict[str, Any]:
    record = store.get_claim(claim_id)
    if record is None:
        raise HTTPException(404, f"{claim_id} has not been processed yet")
    return record


@app.get("/api/claims/{claim_id}/evidence")
def list_evidence(claim_id: str) -> dict[str, Any]:
    import analyzers
    folder = _claim_dir(claim_id)
    files = []
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            relative = path.relative_to(folder).as_posix()
            files.append({
                "name": relative,
                "type": analyzers.classify_by_filename(path.name),
                "size_kb": round(path.stat().st_size / 1024),
            })
    return {"claim_id": claim_id, "files": files}


@app.get("/api/claims/{claim_id}/file/{name:path}")
def get_file(claim_id: str, name: str) -> FileResponse:
    folder = _claim_dir(claim_id)
    path = (folder / name).resolve()
    if not str(path).startswith(str(folder.resolve())) or not path.is_file():
        raise HTTPException(404, "file not found")
    return FileResponse(path)


@app.post("/api/claims/{claim_id}/process")
def process(claim_id: str, background: BackgroundTasks) -> dict[str, Any]:
    folder = _claim_dir(claim_id)
    if claim_id in _processing:
        return {"claim_id": claim_id, "status": "already_processing"}

    def run() -> None:
        _processing.add(claim_id)
        try:
            result = pipeline.process_claim(folder)
            store.save_claim(result)
        finally:
            _processing.discard(claim_id)

    background.add_task(run)
    return {"claim_id": claim_id, "status": "processing"}


@app.post("/api/claims/{claim_id}/decision")
def decide(claim_id: str, body: Decision) -> dict[str, Any]:
    if body.decision not in store.DECISIONS:
        raise HTTPException(400, f"decision must be one of {store.DECISIONS}")
    try:
        store.record_decision(claim_id, decision=body.decision,
                              handler=body.handler, note=body.note)
    except KeyError:
        raise HTTPException(404, f"{claim_id} has not been prepared") from None
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    return {"claim_id": claim_id, "status": body.decision, "handler": body.handler}
