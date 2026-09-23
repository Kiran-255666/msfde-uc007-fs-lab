"""Content Understanding analyzer definitions for the claim document types.

One analyzer per document type. Fields use:
  extract  - copy a value that appears in the document (gives confidence + source span)
  classify - choose from a fixed list
  generate - write a short summary from the document

Analyzer ids may not contain hyphens, so each participant's analyzers are suffixed with
their alias using underscores, for example claim_form_fdeuser7.


REFERENCE SOLUTION. Compare with your own version rather than starting here."""
from __future__ import annotations

from typing import Any

CLAIM_FORM: dict[str, Any] = {
    "claim_reference": {"type": "string", "method": "extract",
                        "description": "Claim reference such as CLM-2026-0431"},
    "policy_number": {"type": "string", "method": "extract"},
    "claimant_name": {"type": "string", "method": "extract"},
    "date_of_loss": {"type": "date", "method": "extract",
                     "description": "Date of loss / date of the incident"},
    "incident_location": {"type": "string", "method": "extract"},
    "loss_type": {"type": "string", "method": "classify",
                  "enum": ["Collision", "Theft", "Attempted theft", "Vandalism",
                           "Weather", "Glass", "Other"]},
    "damage_area": {"type": "string", "method": "classify",
                    "enum": ["Front", "Rear", "Side", "Roof", "Glass", "Underbody",
                             "Multiple", "Other"]},
    "vehicle_make": {"type": "string", "method": "extract"},
    "vehicle_model": {"type": "string", "method": "extract"},
    "vehicle_year": {"type": "string", "method": "extract"},
    "vin": {"type": "string", "method": "extract"},
    "plate": {"type": "string", "method": "extract", "description": "Registration plate"},
    "police_reference": {"type": "string", "method": "extract",
                         "description": "Police or crime reference; empty when not provided"},
    # CIP-CLM-200 section 1 requires third-party details for a third-party collision, so the
    # schema has to extract them - otherwise the agent correctly reports them as missing.
    "third_party_details": {"type": "string", "method": "extract",
                            "description": "Third party name, vehicle and insurer; empty when none reported"},
    "incident_summary": {"type": "string", "method": "generate",
                         "description": "One sentence describing what happened"},
}

POLICE_REPORT: dict[str, Any] = {
    "report_reference": {"type": "string", "method": "extract"},
    "incident_date": {"type": "date", "method": "extract"},
    "incident_location": {"type": "string", "method": "extract"},
    "reporting_officer": {"type": "string", "method": "extract"},
    "vin": {"type": "string", "method": "extract",
            "description": "VIN exactly as written in the report"},
    "vehicle_description": {"type": "string", "method": "extract"},
    "damage_area": {"type": "string", "method": "classify",
                    "enum": ["Front", "Rear", "Side", "Roof", "Glass", "Underbody",
                             "Multiple", "Other", "Not stated"]},
    "narrative_summary": {"type": "string", "method": "generate",
                          "description": "One sentence summary of the officer's narrative"},
}

REPAIR_ESTIMATE: dict[str, Any] = {
    "repairer_name": {"type": "string", "method": "extract"},
    "estimate_reference": {"type": "string", "method": "extract"},
    "estimate_date": {"type": "date", "method": "extract"},
    "vin": {"type": "string", "method": "extract"},
    "vehicle_description": {"type": "string", "method": "extract"},
    "total_amount": {"type": "number", "method": "extract",
                     "description": "Total estimate amount in dollars, digits only"},
    "damage_area": {"type": "string", "method": "classify",
                    "enum": ["Front", "Rear", "Side", "Roof", "Glass", "Underbody",
                             "Multiple", "Other"]},
    "includes_panel_replacement": {"type": "string", "method": "classify",
                                   "enum": ["Yes", "No"],
                                   "description": "Does the estimate replace a panel, door skin or bumper cover?"},
    "includes_adas_recalibration": {"type": "string", "method": "classify",
                                    "enum": ["Yes", "No"],
                                    "description": "Does the estimate include ADAS or sensor recalibration?"},
    "operations_summary": {"type": "string", "method": "generate",
                           "description": "The main repair operations, in one sentence"},
}

CUSTOMER_STATEMENT: dict[str, Any] = {
    "claim_reference": {"type": "string", "method": "extract"},
    "statement_date": {"type": "date", "method": "extract"},
    "stated_date_of_loss": {"type": "date", "method": "extract",
                            "description": "Date the policyholder says the incident happened"},
    "stated_damage_area": {"type": "string", "method": "classify",
                           "enum": ["Front", "Rear", "Side", "Roof", "Glass", "Underbody",
                                    "Multiple", "Other", "Not stated"]},
    "stated_cause": {"type": "string", "method": "generate",
                     "description": "How the policyholder says the damage happened, one sentence"},
}

POLICY_SCHEDULE: dict[str, Any] = {
    "policy_number": {"type": "string", "method": "extract"},
    "cover_type": {"type": "string", "method": "classify",
                   "enum": ["Comprehensive", "Third Party Fire and Theft", "Third Party Only", "Other"]},
    "effective_from": {"type": "date", "method": "extract",
                       "description": "Start of the period of cover"},
    "effective_to": {"type": "date", "method": "extract",
                     "description": "End of the period of cover"},
    "policyholder_name": {"type": "string", "method": "extract"},
    "named_drivers": {"type": "string", "method": "extract"},
    "vin": {"type": "string", "method": "extract"},
    "plate": {"type": "string", "method": "extract"},
    "collision_deductible": {"type": "number", "method": "extract",
                             "description": "Collision deductible amount in dollars"},
    "sum_insured": {"type": "number", "method": "extract"},
}

# document type -> (analyzer base name, field schema, filename stem it is used for)
ANALYZERS: dict[str, dict[str, Any]] = {
    "claim_form": {"schema": CLAIM_FORM, "matches": ["claim-form"]},
    "police_report": {"schema": POLICE_REPORT, "matches": ["police-report"]},
    "repair_estimate": {"schema": REPAIR_ESTIMATE, "matches": ["repair-estimate"]},
    "customer_statement": {"schema": CUSTOMER_STATEMENT, "matches": ["customer-statement"]},
    "policy_schedule": {"schema": POLICY_SCHEDULE, "matches": ["policy-schedule"]},
}

# documents that carry no extraction schema but are still recognised
OTHER_DOCUMENT_TYPES = ["claims_history"]


def classify_by_filename(filename: str) -> str:
    """Map an uploaded file to a document type by its name.

    A production system would classify by content; filenames keep the lab focused on the
    extraction and reasoning steps.
    """
    stem = filename.lower().rsplit("/", 1)[-1]
    if stem.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return "damage_photo"
    for doc_type, spec in ANALYZERS.items():
        if any(token in stem for token in spec["matches"]):
            return doc_type
    if "claims-history" in stem:
        return "claims_history"
    return "unknown"
