# F3 · Find patterns across claims, not within one

**Difficulty** Hard · **Time** ~60 min · **Proves** real fraud signal usually lives between claims

## The situation

Every rule you have looks *inside* one claim. Organised claim fraud does not look wrong inside a
single file — it looks wrong across a book of them: the same vehicle appearing under two
policyholders, the same repairer across unrelated claimants, three incidents at the same car park
in a month, the same phone number on two claims.

## What to do

1. Process all the claims so you have their extracted data to work with.
2. Write a cross-claim analysis that looks for at least **three** patterns of your choosing —
   repeated VIN or plate across different policyholders, a repairer concentrated across
   unrelated claims, incidents clustered at one location or date, repeated contact details.
3. Report each hit with the claims involved and the evidence, in the same style as the existing
   findings: observation, not accusation.
4. Decide where this belongs — a pass over the book, or something a claim triggers when it
   arrives. Both are defensible; say which you chose.

## Acceptance test

- Running it over the sample claims surfaces at least one real pattern, with the claim ids and
  the shared value named.
- It produces **no** hit that is merely a coincidence of the sample (all five claims are in
  Springfield — location alone is not a pattern).
- Per-claim behaviour is unchanged: `python evaluate.py` still passes.

## Worth thinking about

Cross-claim analysis needs data from claims the current handler may have no business reading.
That is a real governance question, not a technical one. What would you need in place before
running this across a live book?
