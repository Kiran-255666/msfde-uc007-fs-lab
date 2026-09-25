# Extensions — going deeper on UC007

Your workspace prepares five claims correctly. These challenges take it from *working* to
*defensible*: what a claims operations lead and an evaluation panel will actually ask.

Each is independent. Pick what interests you — nobody is expected to do all seven.

| # | Challenge | Difficulty | Rough time | What it proves |
|---|---|---|---|---|
| [F1](F1-new-evidence-type.md) | Handle a new document type end to end | Moderate | 60 min | The pipeline extends, rather than being a fixed demo |
| [F2](F2-author-a-claim.md) | Author a claim with a hidden defect, then swap | Moderate | 50 min | Your checks catch defects you did not design them around |
| [F3](F3-cross-claim-patterns.md) | Find patterns across claims, not within one | Hard | 60 min | Real fraud signal usually lives between claims |
| [F4](F4-subtle-fraud.md) | Break your own pipeline with a subtle claim | Hard | 60 min | It catches more than the obvious case |
| [F5](F5-verification-queue.md) | Route low-confidence fields to a human | Moderate | 50 min | Confidence is used, not just displayed |
| [F6](F6-cost-and-latency.md) | Put a price on processing a claim | Moderate | 45 min | It could survive a finance conversation |
| [F7](F7-batch-metrics.md) | Report on a book of claims, not one | Moderate | 45 min | An operations lead can see the shape of the work |

## The rule that applies to all of them

**Finish with evidence.** Every challenge has an acceptance test, and the evaluation is already
written:

```powershell
cd ..\eval
python evaluate.py
```

Extraction 45/45, findings 10/10, recommendations 5/5, safety violations 0 — that is your
baseline, and it must still hold after your change. If you add claims or rules, extend the
ground truth with them; a check that scores your own new work as correct by definition proves
nothing.

## The boundary that does not move

Whatever you add, the workspace still never approves, declines or pays a claim, and never
alleges fraud (CIP-CLM-200 §5.2, CIP-CLM-210 §4.2). Several of these challenges make it
tempting. Don't.

## How these are assessed

| Criterion | Challenges that speak to it |
|---|---|
| Solution design & architecture | F1, F3, F5 |
| Technical implementation | F1, F2, F4 |
| Deployment readiness | F6, F7 |
| Business value | F6, F7 |
| Innovation | F3, F4 |
| Presentation & defence | all of them — bring the numbers |
