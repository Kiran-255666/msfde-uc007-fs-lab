"""Deterministic checks over the extracted claim data.

These are rules, not model judgement. A rule engine is used here because the checks must be
repeatable and explainable: every finding names the documents and values it came from, so a
handler can verify it in seconds. The model's job comes later - explaining the findings in
the claim summary.

Every finding is: code, severity, message, evidence[].


REFERENCE SOLUTION. Compare with your own version rather than starting here."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import config as cfg

INFO, WARNING, CRITICAL = "info", "warning", "critical"


def _finding(code: str, severity: str, message: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "evidence": evidence}


def _ev(document: str, field: str, value: Any) -> dict[str, Any]:
    return {"document": document, "field": field, "value": value}


def _value(extracted: dict[str, Any], doc_type: str, field: str) -> Any:
    return ((extracted.get(doc_type) or {}).get(field) or {}).get("value")


def _as_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %B %Y"):
        try:
            return datetime.strptime(str(value)[:24], fmt).date()
        except ValueError:
            continue
    return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


# --------------------------------------------------------------------- the checks

def check_completeness(extracted: dict, present_types: list[str]) -> list[dict]:
    loss_type = _value(extracted, "claim_form", "loss_type") or "Other"
    required = cfg.REQUIRED_DOCUMENTS.get(loss_type, cfg.REQUIRED_DOCUMENTS["Other"])
    missing = [d for d in required if d not in present_types]
    findings = []
    for document in missing:
        findings.append(_finding(
            "MISSING_DOCUMENT", CRITICAL,
            f"A {document.replace('_', ' ')} is required for a {loss_type.lower()} claim and is not on file "
            f"(CIP-CLM-200 section 1).",
            [_ev("claim_form", "loss_type", loss_type)],
        ))
    return findings


def check_dates(extracted: dict) -> list[dict]:
    form = _as_date(_value(extracted, "claim_form", "date_of_loss"))
    police = _as_date(_value(extracted, "police_report", "incident_date"))
    statement = _as_date(_value(extracted, "customer_statement", "stated_date_of_loss"))
    findings = []
    for name, other in (("police_report", police), ("customer_statement", statement)):
        if form and other and form != other:
            findings.append(_finding(
                "DATE_MISMATCH", CRITICAL,
                f"The date of loss differs between the claim form ({form}) and the "
                f"{name.replace('_', ' ')} ({other}); CIP-CLM-200 section 2.1 requires them to agree.",
                [_ev("claim_form", "date_of_loss", str(form)),
                 _ev(name, "date_of_loss", str(other))],
            ))
    return findings


def check_vehicle_identifiers(extracted: dict) -> list[dict]:
    findings = []
    for field in ("vin", "plate"):
        values = {doc: _value(extracted, doc, field)
                  for doc in ("claim_form", "policy_schedule", "repair_estimate", "police_report")}
        present = {d: str(v).strip().upper() for d, v in values.items() if v}
        distinct = set(present.values())
        if len(distinct) > 1:
            findings.append(_finding(
                "VEHICLE_MISMATCH", CRITICAL,
                f"The {field.upper()} is not the same across documents: "
                + "; ".join(f"{d} = {v}" for d, v in present.items())
                + " (CIP-CLM-200 section 2.2).",
                [_ev(d, field, v) for d, v in present.items()],
            ))
    return findings


def check_damage_consistency(extracted: dict, photo_assessments: list[dict]) -> list[dict]:
    sources = {
        "claim_form": _value(extracted, "claim_form", "damage_area"),
        "repair_estimate": _value(extracted, "repair_estimate", "damage_area"),
        "customer_statement": _value(extracted, "customer_statement", "stated_damage_area"),
    }
    for assessment in photo_assessments:
        if assessment.get("damage_area") not in (None, "None visible"):
            sources[f"photo:{assessment['file']}"] = assessment["damage_area"]
            break

    present = {d: str(v) for d, v in sources.items() if v and str(v) not in ("Not stated", "Other")}
    distinct = set(present.values())
    if len(distinct) > 1:
        return [_finding(
            "DAMAGE_LOCATION_MISMATCH", CRITICAL,
            "The damage location is not consistent across the evidence: "
            + "; ".join(f"{d} says {v}" for d, v in present.items())
            + " (CIP-CLM-200 section 2.3).",
            [_ev(d, "damage_area", v) for d, v in present.items()],
        )]
    return []


def check_cover_in_force(extracted: dict) -> list[dict]:
    loss = _as_date(_value(extracted, "claim_form", "date_of_loss"))
    start = _as_date(_value(extracted, "policy_schedule", "effective_from"))
    end = _as_date(_value(extracted, "policy_schedule", "effective_to"))
    if not loss or not start:
        return []
    if loss < start or (end and loss > end):
        return [_finding(
            "COVER_NOT_IN_FORCE", CRITICAL,
            f"The date of loss ({loss}) falls outside the period of cover "
            f"({start} to {end}). Cover applies only to losses inside the policy period "
            f"(CIP-POL-100 section 1.1). A coverage decision is for a senior adjuster "
            f"(CIP-CLM-200 section 3.2).",
            [_ev("claim_form", "date_of_loss", str(loss)),
             _ev("policy_schedule", "effective_from", str(start)),
             _ev("policy_schedule", "effective_to", str(end))],
        )]
    return []


def check_authority_limit(extracted: dict) -> list[dict]:
    total = _as_float(_value(extracted, "repair_estimate", "total_amount"))
    if total is None or total <= cfg.HANDLER_AUTHORITY_LIMIT:
        return []
    return [_finding(
        "EXCEEDS_AUTHORITY", WARNING,
        f"The estimate of ${total:,.2f} exceeds the ${cfg.HANDLER_AUTHORITY_LIMIT:,.0f} claims "
        f"handler authority limit, so the claim is referred upward (CIP-CLM-200 section 3).",
        [_ev("repair_estimate", "total_amount", total)],
    )]


def check_estimate_against_photos(extracted: dict, photo_assessments: list[dict]) -> list[dict]:
    total = _as_float(_value(extracted, "repair_estimate", "total_amount"))
    if total is None or not photo_assessments:
        return []
    ceilings = [c for c in (vision_band_ceiling(a) for a in photo_assessments) if c]
    if not ceilings:
        return []
    ceiling = max(ceilings)
    if total <= ceiling * 1.2:            # 20 percent tolerance
        return []
    worst = max(photo_assessments, key=lambda a: vision_band_ceiling(a) or 0)
    return [_finding(
        "ESTIMATE_EVIDENCE_MISMATCH", CRITICAL,
        f"The estimate of ${total:,.2f} is well above the indicative range for the damage "
        f"visible in the photographs (up to ${ceiling:,.0f} for {worst.get('severity')} "
        f"{worst.get('damage_area','').lower()} damage: {worst.get('visible_damage','')}). "
        f"See CIP-CLM-220 section 4 and CIP-CLM-210 section 2.1.",
        [_ev("repair_estimate", "total_amount", total),
         _ev(f"photo:{worst.get('file')}", "indicative_repair_band", worst.get("indicative_repair_band"))],
    )]


def vision_band_ceiling(assessment: dict) -> float | None:
    band = assessment.get("indicative_repair_band")
    if not band or band == "unknown":
        return None
    try:
        return float(str(band).split("-")[1])
    except (IndexError, ValueError):
        return None


def check_repairer(extracted: dict) -> list[dict]:
    repairer = _value(extracted, "repair_estimate", "repairer_name")
    if not repairer:
        return []
    for listed in cfg.ENHANCED_REVIEW_REPAIRERS:
        if listed.lower() in str(repairer).lower():
            return [_finding(
                "REPAIRER_ENHANCED_REVIEW", WARNING,
                f"{listed} is on the enhanced review list, so every estimate is checked line by "
                f"line and the claim is referred (CIP-CLM-220 section 2, CIP-CLM-210 section 2.3).",
                [_ev("repair_estimate", "repairer_name", repairer)],
            )]
    return []


def check_claim_frequency(claims_history: list[dict] | None) -> list[dict]:
    if not claims_history or len(claims_history) < cfg.CLAIM_FREQUENCY_THRESHOLD:
        return []
    return [_finding(
        "CLAIM_FREQUENCY", WARNING,
        f"{len(claims_history)} claims are recorded in the last 12 months, which meets the "
        f"referral threshold of {cfg.CLAIM_FREQUENCY_THRESHOLD} (CIP-CLM-210 section 2.3).",
        [_ev("claims_history", "claim_count", len(claims_history))],
    )]


def check_low_confidence_fields(extracted: dict, threshold: float = 0.6) -> list[dict]:
    findings = []
    for doc_type, fields in extracted.items():
        for name, field in (fields or {}).items():
            confidence = field.get("confidence")
            if confidence is not None and confidence < threshold:
                findings.append(_finding(
                    "LOW_CONFIDENCE_FIELD", INFO,
                    f"{name} was extracted from the {doc_type.replace('_', ' ')} with low "
                    f"confidence ({confidence:.2f}); a handler should verify it.",
                    [_ev(doc_type, name, field.get("value"))],
                ))
    return findings


def run_all(extracted: dict, present_types: list[str], photo_assessments: list[dict],
            claims_history: list[dict] | None = None) -> list[dict]:
    """Run every check and return the findings, most serious first."""
    findings: list[dict] = []
    findings += check_completeness(extracted, present_types)
    findings += check_dates(extracted)
    findings += check_vehicle_identifiers(extracted)
    findings += check_damage_consistency(extracted, photo_assessments)
    findings += check_cover_in_force(extracted)
    findings += check_authority_limit(extracted)
    findings += check_estimate_against_photos(extracted, photo_assessments)
    findings += check_repairer(extracted)
    findings += check_claim_frequency(claims_history)
    findings += check_low_confidence_fields(extracted)
    order = {CRITICAL: 0, WARNING: 1, INFO: 2}
    return sorted(findings, key=lambda f: order.get(f["severity"], 3))


def recommend(findings: list[dict]) -> str:
    """Map findings to a next step. Never an approve/decline decision (CIP-CLM-200 s5.2)."""
    codes = {f["code"] for f in findings}
    if codes & {"MISSING_DOCUMENT"}:
        return "request_information"
    # DAMAGE_LOCATION_MISMATCH is a fraud indicator in its own right (CIP-CLM-210 s2.1),
    # so it refers rather than merely asking the policyholder for more information.
    if codes & {"COVER_NOT_IN_FORCE", "EXCEEDS_AUTHORITY", "ESTIMATE_EVIDENCE_MISMATCH",
                "REPAIRER_ENHANCED_REVIEW", "CLAIM_FREQUENCY", "DAMAGE_LOCATION_MISMATCH"}:
        return "refer"
    if codes & {"DATE_MISMATCH", "VEHICLE_MISMATCH"}:
        return "request_information"
    return "proceed"
