# UC007 · Claims Processing Agent — Participant Lab Guide

**Microsoft FDE Use-Case Pack · Wipro AI Academy**
Complexity L300 · Duration 4–5 hours · Technology: Microsoft Foundry, Azure OpenAI, Content
Understanding, Python 3.12, React/Node

---

## What you are building

A claims team receives repair estimates, damage photographs, police reports, customer
statements, policy documents and claim forms. Reviewing them by hand is slow and
inconsistent: it is easy to miss a document, and easy to miss that two documents disagree.

You will build a **claims workspace** that:

1. **Organises mixed evidence** against a single claim record.
2. **Extracts structured claim data** — claimant, policy, incident, vehicle, damage and repair
   cost — each value carrying a **confidence and a source span**, so a handler can verify it.
3. **Assesses damage photographs** with a vision model and estimates an indicative repair band.
4. **Checks completeness, policy alignment and cross-document consistency** with rules.
5. **Writes a grounded claim summary** with findings, outstanding items and next steps, citing
   the policy documents it relied on.
6. **Hands every claim to a human**. It never approves, declines or pays a claim.

> **Training environment.** Contoso Insurance, the policies, people, garages and police
> references are fictional. The damage photographs are a mix of openly-licensed photos and
> AI-generated images. Nothing here is a real claim.

### The evidence set

Five claims, each built to exercise something different:

| Claim | What it is |
|---|---|
| **CLM-2026-0431** | Complete and consistent. A rear-end collision with everything on file. |
| **CLM-2026-0432** | Theft claim with **missing evidence** — no crime reference, no statement, no photographs. |
| **CLM-2026-0433** | **Contradictory evidence** — the dates, the VIN and the damage location disagree. |
| **CLM-2026-0434** | **Policy exception** — the loss predates the start of cover, and the estimate exceeds the handler's authority. |
| **CLM-2026-0435** | **Fraud indicators** — a $6,940 estimate for damage the photographs show as a light scuff, from a repairer on the enhanced review list, third claim in 12 months. |

### The policy corpus

Four documents in `reference/policies/`, indexed into a shared knowledge base your agent
queries. **Read them before you start** — they define every rule you implement:

- **CIP-POL-100** Motor Policy Wording — what is covered, exclusions, period of cover
- **CIP-CLM-200** Claims Handling Standards — required evidence, data quality checks, authority limits, what an automated system may and may not do
- **CIP-CLM-210** Fraud Indicators and SIU Referral — indicators, and the rule that you observe and refer rather than accuse
- **CIP-CLM-220** Repair Network and Estimate Validation — enhanced review list, estimate rules, **indicative repair bands**

---

## Part 0 · Set up (25 min)

**1.** Open PowerShell **as Administrator** and clone or copy this repository to `C:\uc007`.

**2.** Run the setup script:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
cd C:\uc007
.\setup-windows.ps1
```

It installs anything missing — the lab image has Python 3.12, the Azure CLI and VS Code, but
**not Node**, so the script installs that — then creates the Python environment, installs the
frontend packages with `npm install`, and sets UTF-8 output. Expect it to take a few minutes.

**3.** Copy `backend\.env.example` to `backend\.env`, paste in the values from the **lab
environment handout**, and set your alias to your lab username:

```
LAB_ALIAS=fdeuser7
```

**4.** Sign in to Azure and select the subscription:

```powershell
az login --use-device-code
az account set --subscription <SUBSCRIPTION_ID from the handout>
az account show --query "{user:user.name, subscription:name}" -o table
```

**5.** Check your configuration:

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
python config.py
```

> **Checkpoint 0** — `python config.py` prints your agent name, analyzer suffix and table
> names, all built from your alias, and `az account show` matches the handout.

---

## Part 1 · Extract claim data from documents (60 min)

Open **`backend/analyzers.py`**.

Content Understanding analyzers read a document and return fields. Unlike asking a chat model
to read a PDF, each field comes back with a **confidence** and a **source span** — which is
what makes the result auditable for a claims handler.

### TODO 1 — define the claim form schema

Every field the rules need must be in the schema. Work out which fields those are by reading
`validation.py` and `config.py`, and remember that CIP-CLM-200 section 1 requires third-party
details for a third-party collision.

Methods:

| method | use it for |
|---|---|
| `extract` | a value printed in the document (gives confidence and source) |
| `classify` | one of a fixed `enum`, e.g. the loss type |
| `generate` | a short written summary |

> **Trap:** analyzer ids may not contain hyphens. Yours are suffixed with your alias, e.g.
> `claim_form_fdeuser7`.

### Create the analyzers and extract

```powershell
python pipeline.py --setup
python pipeline.py --claim CLM-2026-0431 --skip-agent
```

Each analyzer takes about 30 seconds to create, once.

> **Checkpoint 1** — the extracted claim form shows `claimant_name`, `date_of_loss`, `vin`,
> `plate` and `police_reference` with confidences above 0.9. If a field comes back empty,
> improve its `description` — that is the instruction the extractor follows.

---

## Part 2 · Assess the damage photographs (40 min)

Open **`backend/vision.py`**.

### TODO 2 — write the photograph assessment instructions

The assessment feeds a rule that compares the repair estimate against what the photographs
actually show, so it has to be conservative: describe only what is visible, never infer cause
or fault, and map the damage to an indicative band from **CIP-CLM-220 section 4**.

```powershell
python pipeline.py --claim CLM-2026-0435 --skip-agent
```

> **Checkpoint 2** — the two photographs on CLM-2026-0435 come back as **minor** side damage
> in the **300-900** band. That is what will later contradict the $6,940 estimate.

---

## Part 3 · Check the claim (60 min)

Open **`backend/validation.py`**. Rules here are deterministic and quote their evidence, so a
handler can verify a finding in seconds. Three are yours to write.

**TODO 3a — `check_dates`.** The date of loss must agree across the claim form, the customer
statement and any police report (CIP-CLM-200 section 2.1).

**TODO 3b — `check_damage_consistency`.** The damage location must be consistent across the
claim form, the repair estimate, the statement and the photographs (section 2.3).

**TODO 3c — `check_estimate_against_photos`.** Compare the estimate total against the
indicative band for the damage the photographs show (CIP-CLM-220 section 4). Allow a tolerance
— a genuine estimate can exceed a band slightly — then raise `ESTIMATE_EVIDENCE_MISMATCH`.

```powershell
python pipeline.py --all --skip-agent
```

> **Checkpoint 3** — CLM-2026-0431 raises no critical findings; 0432 raises three missing
> documents; 0433 raises the date, VIN and damage-location mismatches; 0434 raises cover not in
> force and the authority limit; 0435 raises the estimate/evidence mismatch, the repairer and
> the claim frequency.

---

## Part 4 · The grounded claims agent (60 min)

Open **`backend/claims_agent.py`**.

### TODO 4 — write the agent instructions

The agent receives the extracted fields, the photo assessments and the findings, and produces
the claim summary a handler reads. Your instructions must cover grounding, honesty about gaps,
the output it must produce, the decision boundary, and the recommendation precedence. The
comment in the file lists each requirement.

The hardest part is the boundary: the agent must explain a fraud indicator **without alleging
fraud** (CIP-CLM-210 section 4.2), and must never approve, decline or pay.

```powershell
python -c "import claims_agent; print(claims_agent.create_agent())"
python pipeline.py --all
```

> **Checkpoint 4** — every claim gets a summary, each finding is explained with a policy
> reference, and the recommendations are: 0431 proceed, 0432 request_information, 0433 refer,
> 0434 refer, 0435 refer.

---

## Part 5 · The workspace and the human decision (45 min)

Start the API and the React workspace in two terminals:

```powershell
# terminal 1
cd backend
..\.venv\Scripts\Activate.ps1
uvicorn api:app --port 8000

# terminal 2
cd frontend
npm run dev
```

Open http://localhost:5173.

> **No `npm install` needed** — `setup-windows.ps1` installed the frontend packages in Part 0.
> If `npm run dev` complains that `vite` is not recognised, the install did not happen on this
> copy of the folder; run `npm install` once in `frontend` and start it again.

Work through a claim as a handler would: read the summary, open a finding and check the
evidence chips against the source PDF, look at the photographs, expand the extracted data and
notice the low-confidence values, then record **accept**, **accept with amendments** or
**reject** with your name and a note.

> **Checkpoint 5** — your decision appears against the claim with your name and timestamp, and
> the claim moves out of the prepared queue. Note that nothing in the workspace can approve,
> decline or pay the claim.

---

## Part 6 · Evaluate (40 min)

```powershell
cd ..\eval
python evaluate.py
```

The evaluation scores three things against the ground truth:

| Measure | What it checks |
|---|---|
| Extraction accuracy | did the analyzers pull the right values out of the documents |
| Finding detection | were the planted defects found, and were clean claims left alone |
| Recommendation and safety | the right next step, and never approve / decline / pay / allege fraud |

Any failure is a bug in your schema, your rules or your instructions. Fix and re-run.

> **Checkpoint 6** — extraction 45/45, findings 10/10 with no spurious findings,
> recommendations 5/5, safety violations 0.

---

## Part 7 · Demo and defence (25 min)

| Criterion | Show this |
|---|---|
| Solution design & architecture | evidence → extraction with confidence and source → photo assessment → rules → grounded agent → handler decision; why rules and model are separate |
| Technical implementation | a finding whose evidence chips match the source PDF; the fraud claim where photos contradict the estimate |
| Deployment readiness | keyless managed identity, per-field confidence, the evaluation suite, the audit trail of handler decisions |
| Business value | time per claim, consistency, fewer missed inconsistencies, an auditable file |
| Innovation | grounded reasoning over mixed document and image evidence, measured rather than demonstrated |
| Presentation & defence | your evaluation numbers, and the failures you fixed |

**Questions to expect**

- Why use Content Understanding for documents and a vision model for photographs?
- What stops the agent inventing a policy rule?
- A handler disagrees with a finding. What does the audit trail show?
- Why does the workspace refuse to decide, when it clearly "knows" the answer?
- What would you change before this touched a real claims system?

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `The 'analyzerId' cannot contain '-'` | Analyzer ids use underscores. Keep the alias-suffixed names. |
| `This analyzer needs a 'completion' model deployment` | The analyzer body must set `models.completion`; `content_understanding.py` does this for you. |
| `Missing required query parameter 'audience'` | The knowledge base connection was updated rather than created. Re-run the connection step. |
| `403` from Search, Storage or the project | Your account is not in the participant group yet, or membership has not propagated. Wait a few minutes and `az login` again. |
| `UnicodeEncodeError ... charmap` | Your console is not UTF-8. Run `setup-windows.ps1`, or `chcp 65001` in the current window. |
| The workspace shows "Cannot reach the API" | `uvicorn` is not running on port 8000, or you started the frontend from the wrong folder. |
| A rule never fires | Check the field it depends on is actually in your analyzer schema — an unextracted field looks like missing evidence. |
