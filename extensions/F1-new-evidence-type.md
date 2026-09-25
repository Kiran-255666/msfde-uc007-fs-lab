# F1 · Handle a new document type end to end

**Difficulty** Moderate · **Time** ~60 min · **Proves** the pipeline extends rather than being a fixed demo

## The situation

Claims rarely stay still. Contoso starts covering hire cars while a vehicle is repaired, so a
**hire car invoice** now arrives with some claims — a daily rate, a number of days, a total, and
the dates it covers. Nothing in your pipeline knows what to do with it.

## What to do

1. **Create the evidence.** Add a hire car invoice to one of the sample claims. Match the house
   style of the other documents so extraction is a fair test, and make its dates and vehicle
   agree with the rest of the claim — except where you *want* a defect.
2. **Write the analyzer.** A new field schema in `analyzers.py`, registered so
   `classify_by_filename` recognises the file, with a sensible mix of `extract` and `classify`.
3. **Write the rule.** Something worth checking: the hire period should not start before the
   date of loss, and should not run past the repair completion. Decide the severity and which
   policy section justifies it.
4. **Extend the ground truth** in `data/ground-truth.json` so the evaluation scores it.

## Acceptance test

- The new analyzer extracts the daily rate, days and total with confidence above 0.8.
- Your new rule fires on a claim that breaches it, and stays silent on one that does not.
- `python evaluate.py` passes, including your new expectations.

## Worth thinking about

You had to decide whether a hire car invoice is *required* evidence. For which claim types?
Getting that wrong makes every claim of that type incomplete — a small change to
`REQUIRED_DOCUMENTS` with a large operational effect.
