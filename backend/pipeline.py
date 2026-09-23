"""The claim processing pipeline: evidence in, prepared claim out.

    ingest -> classify -> extract -> assess photos -> validate -> summarise

Run it over the sample claims:
    python pipeline.py --claim CLM-2026-0433
    python pipeline.py --all
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import pathlib
import re
import sys
import time
from typing import Any

import analyzers
import claims_agent
import config as cfg
import validation
import vision
from content_understanding import ContentUnderstandingClient

def _find_repo_dir(name: str) -> pathlib.Path:
    """Locate a top-level folder by walking up from this file.

    The same code runs from the source tree (app/backend/) and from the participant
    repository (backend/), so the depth is not fixed.
    """
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / name
        if candidate.exists():
            return candidate
    return here.parent / name


DATA_DIR = _find_repo_dir("data") / "claims"
OUT_DIR = _find_repo_dir("data").parent / "out"


def _cu() -> ContentUnderstandingClient:
    return ContentUnderstandingClient(cfg.FOUNDRY_ENDPOINT, cfg.CU_API_VERSION, cfg.CHAT_DEPLOYMENT)


def analyzer_id(doc_type: str) -> str:
    return f"{doc_type}_{cfg.ANALYZER_SUFFIX}"


def ensure_analyzers(only: list[str] | None = None) -> None:
    """Create one analyzer per document type. Takes about 30 seconds each, once."""
    cu = _cu()
    existing = set(cu.list_analyzers())
    for doc_type, spec in analyzers.ANALYZERS.items():
        if only and doc_type not in only:
            continue
        name = analyzer_id(doc_type)
        if name in existing:
            print(f"  = {name}")
            continue
        print(f"  + {name} ...", flush=True)
        cu.create_analyzer(name, spec["schema"], description=f"Contoso {doc_type}")


def parse_claims_history(pdf_path: pathlib.Path) -> list[dict[str, Any]]:
    """Read the claim references out of the claims history PDF.

    Uses pypdf so this works the same on Windows, macOS and Linux. Shelling out to
    pdftotext would silently return nothing on a Windows lab VM, and the claim frequency
    indicator would then never fire.
    """
    try:
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    except Exception as exc:  # noqa: BLE001 - history is optional, but say so
        print(f"  ! could not read {pdf_path.name}: {exc}")
        return []
    rows = re.findall(r"(CLM-\d{4}-\d+)", text)
    return [{"reference": r} for r in dict.fromkeys(rows)]


def process_claim(claim_dir: pathlib.Path, agent_name: str | None = None,
                  skip_agent: bool = False) -> dict[str, Any]:
    started = time.time()
    cu = _cu()
    claim_id = claim_dir.name

    # ---- ingest and classify
    documents, photos = [], []
    for path in sorted(claim_dir.rglob("*")):
        if not path.is_file():
            continue
        doc_type = analyzers.classify_by_filename(path.name)
        if doc_type == "damage_photo":
            photos.append(path)
        else:
            documents.append((doc_type, path))

    present_types = sorted({t for t, _ in documents} | ({"damage_photo"} if photos else set()))

    # ---- extract, in parallel
    extracted: dict[str, Any] = {}

    def extract_one(item):
        doc_type, path = item
        if doc_type not in analyzers.ANALYZERS:
            return doc_type, None
        result = cu.analyze_file(analyzer_id(doc_type), str(path))
        return doc_type, cu.flatten_fields(result)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for doc_type, fields in pool.map(extract_one, documents):
            if fields is not None:
                extracted[doc_type] = fields

    # ---- assess photographs, in parallel
    photo_assessments: list[dict[str, Any]] = []
    if photos:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            photo_assessments = list(pool.map(vision.analyse_photo, photos))

    # ---- claims history, when supplied
    history_pdf = claim_dir / "claims-history.pdf"
    claims_history = parse_claims_history(history_pdf) if history_pdf.exists() else []

    # ---- validate
    findings = validation.run_all(extracted, present_types, photo_assessments, claims_history)
    rule_recommendation = validation.recommend(findings)

    package = {
        "claim_id": claim_id,
        "documents_present": present_types,
        "extracted": {doc: {k: {"value": v["value"], "confidence": v["confidence"]}
                            for k, v in fields.items()}
                      for doc, fields in extracted.items()},
        "photo_assessments": photo_assessments,
        "claims_history_count": len(claims_history),
        "findings": findings,
        "rule_recommendation": rule_recommendation,
    }

    # ---- summarise with the grounded agent
    review = None
    if not skip_agent:
        review = claims_agent.review_claim(package, agent_name=agent_name)

    return {
        **package,
        "review": review,
        "elapsed_seconds": round(time.time() - started, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", help="claim id, e.g. CLM-2026-0433")
    parser.add_argument("--all", action="store_true", help="process every sample claim")
    parser.add_argument("--skip-agent", action="store_true", help="rules only, no summary")
    parser.add_argument("--setup", action="store_true", help="create the analyzers and exit")
    parser.add_argument("--agent", default=None)
    args = parser.parse_args()

    if args.setup:
        print("Creating analyzers")
        ensure_analyzers()
        return 0

    claim_dirs = sorted(d for d in DATA_DIR.iterdir() if d.is_dir())
    if args.claim:
        claim_dirs = [d for d in claim_dirs if d.name == args.claim]
        if not claim_dirs:
            return print(f"no such claim: {args.claim}") or 1
    elif not args.all:
        parser.error("pass --claim <id> or --all")

    print("Checking analyzers")
    ensure_analyzers()

    OUT_DIR.mkdir(exist_ok=True)
    for claim_dir in claim_dirs:
        print(f"\n=== {claim_dir.name}")
        result = process_claim(claim_dir, agent_name=args.agent, skip_agent=args.skip_agent)
        (OUT_DIR / f"{claim_dir.name}.json").write_text(json.dumps(result, indent=2, default=str))

        print(f"  documents : {', '.join(result['documents_present'])}")
        print(f"  findings  : {len(result['findings'])}  -> rules say {result['rule_recommendation']}")
        for finding in result["findings"]:
            print(f"    [{finding['severity']:<8}] {finding['code']}: {finding['message'][:110]}")
        if result.get("review"):
            review = result["review"]
            print(f"  agent     : {review['recommendation']}  "
                  f"(kb calls {review['_telemetry']['knowledge_base_calls']})")
            print(f"  summary   : {review['summary'][:220]}")
        print(f"  {result['elapsed_seconds']}s")
    print(f"\nresults written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
