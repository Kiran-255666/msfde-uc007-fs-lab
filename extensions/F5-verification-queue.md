# F5 · Route low-confidence fields to a human

**Difficulty** Moderate · **Time** ~50 min · **Proves** confidence is used, not just displayed

## The situation

Every extracted field carries a confidence, and the workspace shows the low ones in red. That is
display, not workflow. A handler still has to notice them. Worse, a low-confidence *policy
number* and a low-confidence *incident location* are not equally serious, and right now they look
identical.

## What to do

1. Decide which fields actually matter when uncertain — the ones rules depend on, or that would
   change the outcome. A wrong policy number invalidates the whole check; a fuzzy location rarely
   does.
2. Build a verification step: for a claim with low confidence on a field that matters, produce an
   explicit list of "confirm these values against the source document" items, with the document
   and the extracted value.
3. Surface it in the workspace as its own section, and make the handler's confirmation part of
   the decision they record.
4. Make the claim's status reflect it — a claim awaiting field verification is not in the same
   state as one ready to assess.

## Acceptance test

- A claim with a low-confidence critical field shows a verification list naming the field, the
  value and the source document.
- A claim with only high-confidence fields shows none.
- The handler's confirmation is recorded with their decision, and survives a page reload.

## Worth thinking about

You have just added work for a handler in the name of safety. Count it: how many verification
items per claim on average, and would a real handler do them or start clicking through? A
control nobody follows is worse than no control, because it looks like one.
