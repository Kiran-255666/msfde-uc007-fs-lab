# F6 · Put a price on processing a claim

**Difficulty** Moderate · **Time** ~45 min · **Proves** it could survive a finance conversation

## The situation

Contoso processes thousands of motor claims a month. Before anyone commits, they will ask what
each one costs to prepare and how long it takes — and whether it is cheaper than the twenty
minutes a handler spends reading the file.

## What to do

1. **Measure the parts.** A claim costs five analyzer calls, a vision call per photograph, and
   one agent call whose input is large. `pipeline.py` already reports elapsed time; the agent
   returns token usage in `_telemetry`. Instrument the rest.
2. **Price it** using current published rates, per claim and per thousand. Content Understanding
   is priced per page, not per token — that is easy to miss and it is not small.
3. **Find the cheaper configuration.** Try `gpt-5.4-mini` for the agent, or fewer photographs, or
   skipping the agent entirely for claims the rules already resolve. Re-run `evaluate.py` for
   each and quantify what quality you lost.
4. **Compare with the human baseline** at a plausible loaded hourly rate.

## Acceptance test

A cost-and-latency table for at least two configurations, with evaluation scores beside them,
and a recommendation naming what you would ship and what you gave up.

## Worth thinking about

The most expensive claim in your sample is the one with the most evidence — which is also the one
a handler would take longest on. Does the saving scale with the cost, or against it?
