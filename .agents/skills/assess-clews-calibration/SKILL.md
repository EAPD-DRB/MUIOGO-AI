---
name: assess-clews-calibration
description: Evaluate how well an OSeMOSYS or full CLEWs model is calibrated to a country, identify strong and weak points, classify it as Not assessable, Unacceptable, Acceptable, Good, or Excellent, and judge fitness for a stated use. Use when auditing a country model, reviewing a historical/base-year calibration, checking whether results are reproduced independently rather than forced, comparing modeled values with observations, or assessing a MUIOGO model folder. This grades CALIBRATION QUALITY: for structural and referential defects use clews-model-review, and to describe a model and its calibration to someone rather than grade it use muiogo-explain.
---

# Assess CLEWs Calibration

Evaluate calibration as an evidence-based claim, not as visual plausibility. Keep three conclusions separate:

1. **Technical validity** — the model is internally coherent and solves.
2. **Historical adequacy** — it reproduces country observations at the resolution relevant to its purpose.
3. **Fitness for purpose** — its structure, evidence, resolution, and uncertainty treatment support the proposed use.

A model matching a historical year is not necessarily calibrated when demands, capacities, activity, or shares were fixed to those same observations. Forced matches must not earn the same credit as endogenous reproduction.

## Required workflow

1. Establish the claimed scope, country, calibration period, held-out validation period, and intended use. If these are not documented, record the gap; do not invent them.
2. Read [references/assessment-protocol.md](references/assessment-protocol.md), [references/calibration-rubric.md](references/calibration-rubric.md), and [references/forcing-classification.md](references/forcing-classification.md).
3. If reviewing MUIOGO data, also read [references/muiogo-data-format.md](references/muiogo-data-format.md). Run:

   ```bash
   python scripts/audit_muiogo_model.py <model-folder> --output <inventory.json>
   ```

4. Build a historical-comparison CSV using [references/evidence-schema.md](references/evidence-schema.md). Use observed data from traceable sources and retain units, geography, period, and uncertainty. Run:

   ```bash
   python scripts/compare_history.py <comparisons.csv> --output <history.json>
   ```

5. Inspect the actual constraints and assign every scored outcome `E`, `J`, or `H` using the forcing reference. Spot-check automated findings against the source model.
6. Complete an assessment JSON following the evidence schema. Score it with:

   ```bash
   python scripts/score_assessment.py <assessment.json> \
     --output-json <scorecard.json> --output-markdown <scorecard.md>
   ```

7. Apply the critical gates and caps before issuing a grade. Never upgrade a model merely because its weighted score is high.
8. Report the evidence coverage, uncertainty, forcing share, failures, strengths, weaknesses, grade, confidence, and suitability by use. Distinguish observed facts, script findings, and reviewer judgment.

## Non-negotiable rules

- Use **Not assessable** when the evidence needed to test country calibration is absent or untraceable.
- Treat solver optimality as necessary, never sufficient.
- Do not score history-fixed (`H`) outcomes as successful reproduction.
- Give justified real-world constraints (`J`) partial interpretive credit only when their source and rationale are documented.
- Require both physical cross-links and historical tests of cross-sector flows for a claimed full CLEWs model.
- Check several historical outputs, not one aggregate: stocks, annual flows, temporal/seasonal patterns where relevant, sector shares, resource balances, emissions, and nexus transfers.
- Reserve **Excellent** for a model with held-out validation and documented robustness testing.
- Grade calibration and fitness for purpose independently. A sound annual planning model may still be unfit for reliability or operational questions.
- Do not conceal contradictory observations by averaging them. Report data conflicts and lower confidence.
- Do not claim that the rubric is a universal academic standard. It operationalizes recurring good practices from the literature; see [references/scientific-basis.md](references/scientific-basis.md).

## Output contract

Lead with a decision-ready summary:

- **Calibration grade:** Not assessable / Unacceptable / Acceptable / Good / Excellent
- **Confidence:** Low / Medium / High
- **Critical gates:** pass/fail with evidence
- **Forcing profile:** share of scored evidence classified E/J/H
- **Domain results:** energy, land, water, climate, and cross-nexus links, limited to claimed scope
- **Strong points and weak points**
- **Fitness for stated use:** suitable / conditionally suitable / unsuitable
- **Required improvements:** ordered by which change could alter the grade

Include the score as supporting information, not as a substitute for the grade rationale.

## Related skills

- `clews-model-review` — structural and referential integrity.
- `muiogo-explain` — describing the model and its calibration to a person.
- `build-clews-model` — building the model in the first place.

These live in the MUIOGO-AI collection; if one is not available to you,
do the job directly and say which skill would have covered it.
