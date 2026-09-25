# UC007 · Claims Processing Agent — Lab

Microsoft FDE Use-Case Pack · Wipro AI Academy
**L300 · 4–5 hours · Microsoft Foundry, Azure OpenAI, Content Understanding, Python 3.12, React**

Build a motor claims workspace that takes mixed evidence — claim forms, police reports, repair
estimates, customer statements, policy schedules and damage photographs — extracts the facts
with source traceability, checks them against policy, explains what it found, and hands every
claim to a human.

> **Training environment.** Contoso Insurance, its policies, people, garages, police references
> and claims are fictional. Damage photographs are a mix of openly-licensed images and
> AI-generated ones (see `data/photo-credits.json`). Nothing here is a real claim.

## Start here

1. Open **[docs/lab-guide.md](docs/lab-guide.md)** and follow it from Part 0.
2. You need the **lab environment handout** from your trainer for the endpoints and
   subscription id. This repository ships placeholders only.

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\setup-windows.ps1
```

Then copy `backend\.env.example` to `backend\.env`, paste in the handout values, and set
`LAB_ALIAS` to your lab username.

## What you build

```
  claim evidence (PDFs + photographs)
        │
        ├── Content Understanding analyzers ──► fields + confidence + source span
        └── vision model ─────────────────────► visible damage + indicative repair band
                                  │
                                  ▼
                        validation rules ──────► findings, each citing its evidence
                                  │
                                  ▼
             claims agent, grounded on the policy corpus over MCP
                                  │
                                  ▼
          claims workspace (React) ──► handler accepts / amends / rejects
```

The workspace never approves, declines or pays a claim (CIP-CLM-200 section 5.2).

## The five sample claims

| Claim | What it exercises |
|---|---|
| CLM-2026-0431 | Complete and consistent |
| CLM-2026-0432 | Missing evidence — no crime reference, statement or photographs |
| CLM-2026-0433 | Contradictions — date, VIN and damage location disagree |
| CLM-2026-0434 | Policy exception — loss predates cover, estimate over authority |
| CLM-2026-0435 | Fraud indicators — $6,940 estimate for a light scuff |

## Layout

| Path | What it is |
|---|---|
| `docs/lab-guide.md` | The lab, part by part, with checkpoints |
| `backend/analyzers.py` | **TODO 1** — the claim-form extraction schema |
| `backend/vision.py` | **TODO 2** — damage photograph assessment |
| `backend/validation.py` | **TODO 3a–3c** — date, damage-location and estimate-vs-photo checks |
| `backend/claims_agent.py` | **TODO 4** — the grounded agent instructions |
| `backend/pipeline.py` | Orchestration: ingest → extract → assess → validate → summarise |
| `backend/api.py`, `backend/store.py` | FastAPI service and the claim/decision store |
| `frontend/` | The React claims workspace |
| `reference/policies/` | The four Contoso policy documents. **Read these first** |
| `data/claims/` | The five sample claims |
| `eval/evaluate.py` | Scores your pipeline against the ground truth |
| `solutions/` | Reference solutions — try it yourself first, then compare |
| `extensions/` | Seven deeper challenges for when the core lab is done |

## Commands

```powershell
cd backend
python config.py                             # show the names your alias generates
python pipeline.py --setup                   # create your Content Understanding analyzers
python pipeline.py --claim CLM-2026-0431     # process one claim
python pipeline.py --all --skip-agent        # rules only, no summary
python pipeline.py --all                     # the full pipeline
uvicorn api:app --port 8000                  # the API

cd ..\frontend
npm run dev                                  # the workspace on http://localhost:5173

cd ..\eval
python evaluate.py                           # score against the ground truth
```

## Finished the lab?

The core lab gets you a working claims workspace. **[extensions/](extensions/README.md)** takes it
from *working* to *defensible* — seven independent challenges covering new evidence types,
cross-claim patterns, subtle fraud, the verification queue, cost per claim and book-level metrics.
Each has an acceptance test, so you finish with evidence rather than an assertion.

Nobody is expected to do all seven. Pick the ones you would want to be asked about.

## Requirements

- A Windows lab VM with Python 3.12, the Azure CLI and VS Code (the lab image has these).
  **Node is not on the image** — `setup-windows.ps1` installs it for you.
- An account in the lab participant group, so you can create agents and analyzers in the
  shared backend.
