# F7 · Report on a book of claims, not one

**Difficulty** Moderate · **Time** ~45 min · **Proves** an operations lead can see the shape of the work

## The situation

Your workspace is built for one claim at a time. The person who decides whether to fund this
does not handle claims — they run the team, and they want to know what the queue looks like,
what is holding claims up, and whether the thing is behaving.

## What to do

1. Aggregate across all processed claims: the recommendation mix, the most common finding codes,
   how many claims are missing which document, the distribution of estimate values, and the
   average time to prepare a claim.
2. Surface it in the workspace as an overview a manager would actually read — the summary before
   the detail, and state encoded in form as well as number, not a wall of counts.
3. Include at least one operational metric, not just a technical one: how many claims are waiting
   on the policyholder, how many need a senior adjuster, what proportion cleared without a
   finding.

## Acceptance test

- The overview renders from real processed claims, not hard-coded numbers.
- Every figure is traceable to the claims behind it — a manager can click or filter through to
  the ones that make up a number.
- It still reads sensibly with one claim processed, and with all five.

## Worth thinking about

Which single number would tell this manager the system is going wrong? Referral rate climbing,
extraction confidence drifting down, the same finding code suddenly dominating — pick one and
justify it. That is the metric worth alerting on in production.
