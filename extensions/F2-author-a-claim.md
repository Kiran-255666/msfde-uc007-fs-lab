# F2 · Author a claim with a hidden defect, then swap

**Difficulty** Moderate · **Time** ~50 min · **Proves** your checks catch defects they were not designed around

## The situation

Your rules were written against five claims whose defects you already knew. That is the weakest
possible test. The real question is whether they catch a defect chosen by someone else.

## What to do

1. **Author a sixth claim.** Use `data/claims_source.py` as the model: a complete, internally
   consistent story, with exactly one or two defects planted deliberately. Generate the PDFs the
   same way the others were generated, and reuse a photograph if that suits the story.
2. **Write the ground truth for it** — the finding codes you expect and the recommendation — and
   keep it to yourself for now.
3. **Swap with someone else.** Run their claim through *your* pipeline without being told what is
   wrong with it.
4. **Compare.** Did your pipeline find their defect? Did it invent one that is not there?

## Acceptance test

- Your claim processes cleanly through another participant's pipeline.
- You report honestly what yours caught and missed on theirs.
- Anything you missed that a rule *should* have caught is fixed, and the full evaluation still
  passes.

## Worth thinking about

A miss and a false positive are not equally bad here. A missed inconsistency reaches a handler
as a clean claim; a false positive wastes their time and trains them to ignore your findings.
Which way should this system err, and does it currently?
