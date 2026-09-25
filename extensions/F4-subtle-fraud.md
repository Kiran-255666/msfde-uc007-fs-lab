# F4 · Break your own pipeline with a subtle claim

**Difficulty** Hard · **Time** ~60 min · **Proves** it catches more than the obvious case

## The situation

CLM-2026-0435 is not subtle: a $6,940 estimate for a light scuff, a listed repairer, and three
claims in a year. A competent fraudster would not do any of that. Build the claim they *would*
submit, and find out whether your pipeline notices.

## What to do

1. **Author a claim that is individually plausible.** An estimate just inside the indicative
   band, an unlisted repairer, a first claim, documents that all agree with each other. Hide the
   signal somewhere your current rules do not look — the timing relative to cover starting, a
   repair that does not match the damage described, a part that does not exist for that model,
   photographs whose surroundings do not match the stated location.
2. **Run it.** Be honest about the result: most first attempts sail straight through with
   `proceed`, which is the point of the exercise.
3. **Add the detection you were missing**, grounded in the policy corpus — CIP-CLM-210 §2.2
   lists circumstance indicators your rules almost certainly do not implement yet.
4. **Re-run everything.** New claim caught, old claims unchanged.

## Acceptance test

- A claim that passed cleanly before now raises a finding that names the real signal.
- No new findings on the five original claims.
- `python evaluate.py` passes with your new expectations included.

## Worth thinking about

There is a limit to what any rule set can see. Some of what you just built is really a
*question for a human* rather than a detection — and CIP-CLM-210 §1 is explicit that an
indicator is a reason to look closer, never a conclusion. Where is the honest edge of what this
system should claim to do?
