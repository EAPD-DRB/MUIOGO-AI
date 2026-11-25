<!-- GENERATED FILE - do not edit here.
     Source: docs/og-lessons/THA.md
     Regenerate: python scripts/sync_shared.py -->

# Thailand (THA): lessons behind the OG skills

What happened behind lessons in the OG skills (og-country-calibration,
og-multi-industry-calibration, og-solver-diagnosis, og-run). The skills teach the method; these
are one country's numbers, kept here so the skills stay general. They record what was true when
written; check the country repo before relying on any of them. Do not copy them into another
country's calibration.

Source: a timed dry run that built OG-THA from OG-PHL `calib/remittances` with the installed
skills, 2026-10-19 (12:21 to 14:29), on ogcore 0.21.2 from PyPI. The repo `OG-THA-demo` (branch
`calib/tha-bootstrap`) is a local test repo and is not published; commits below are its hashes.
Its `DEMO_LOG.md` (timed steps) and `PROGRESS.md` (running log) are the written record.

Contents (by the skill file each entry backs; search a file for its `###` headings)
- og-country-calibration/references/bootstrap.md
- og-country-calibration/references/macro-open-economy.md
- og-country-calibration/references/validation-dashboard.md
- og-country-calibration/references/households-demographics.md
- og-country-calibration/references/fiscal-consistency.md
- og-solver-diagnosis/references/failure-taxonomy.md
- og-solver-diagnosis/references/solve-procedures.md
- og-run-preflight/SKILL.md

## og-country-calibration/references/bootstrap.md

### De-siblinging: the sibling's solver seeds stalled the first steady state

- **Lesson:** the sibling's `initial_guess_*` are its solution, not neutral defaults; seed from the
  new country's own first converged solve.
- **What happened:** the first steady state of the packaged Thai parameters failed twice in the same
  way. og-solver-diagnosis class H pointed at the seeds: inherited from PHL, they put Thai GDP at
  nearly twice its solved size. Seeded from Thailand's own converged solve, the same parameters
  solved in 40 seconds.
- **Evidence:** OG-THA-demo commit 8d4c00e ("Seed the steady state from Thailand's own first
  converged solve"); `DEMO_LOG.md` rows for r01-r03 (local, unpublished).
- **When:** 2026-10, ogcore 0.21.2.

### De-siblinging: the inherited example reform changed nothing

- **Lesson:** check that the example reform inherited from the sibling actually changes a parameter
  for the new country.
- **What happened:** OG-PHL's example sets `cit_rate` to 0.20, a cut for the Philippines. Thailand's
  statutory CIT is already 20%, so the inherited reform was a no-op. Replaced by a cut from 20% to
  15% (long-run GDP +1.9%, capital +4.1%, wages +2.4%).
- **Evidence:** OG-THA-demo commit cc5b1e5 ("Thai CIT reform in the example") (local, unpublished).
- **When:** 2026-10.

## og-country-calibration/references/macro-open-economy.md

### Capital share: the informality adjustment used as a lever was a dead end

- **Lesson:** adjust the capital share for self-employment once, when sourcing it; never move it to
  close a `K/Y` gap.
- **What happened:** the solved `K/Y` was 4.0 against a PWT 2.6, with investment at 37% of GDP. A
  lower, informality-adjusted capital share was tried to close it. It pushed the domestic return
  below the world rate and foreign capital vanished, so it was rejected and the measured share
  restored. The `K/Y` overshoot is the family trait the dashboard reference names.
- **Evidence:** `DEMO_LOG.md` probe r06 and the 13:04 entry of `PROGRESS.md` (local, unpublished).
- **When:** 2026-10.

## og-country-calibration/references/validation-dashboard.md

### Score consumption at producer prices

- **Lesson:** compare the model's consumption with national-accounts consumption on the same price
  basis; the model's `C` excludes the consumption tax.
- **What happened:** the first dashboard counted consumption with its sales tax, which made net
  exports look like −11% of GDP; on a consistent basis the figure was about +0.4%.
- **Evidence:** OG-THA-demo commit cc5b1e5 ("dashboard C at producer prices") (local, unpublished).
- **When:** 2026-10.

## og-country-calibration/references/households-demographics.md

### Pensions: a maturing scheme overpays today's retirees at the mature rate

- **Lesson:** for a scheme still maturing, put the accrual rate on a time path from today's value
  to the mature value over the maturing period; keep the steady state at the mature system.
- **What happened:** with the mature `alpha_db` from the start, the model paid 4.8% of GDP in
  pensions in 2025 against an actual 2.1%, ran a primary deficit of 3.4% of GDP against a planned
  0.6%, and took debt to a 95% peak. With `alpha_db` rising over 25 years (the Social Security
  Fund's maturing period), pensions started at 2.1%, the primary balance followed the plan within
  0.3 points in 2025 and 2027, and debt peaked at 68.7%.
- **Evidence:** OG-THA-demo commit b0eed91 ("Phase the SSF pension in from today's 2.1% of GDP");
  sources cited there: World Bank, "The macroeconomic and fiscal impact of aging in Thailand"
  (https://worldbank.org/en/country/thailand/publication/the-macroeconomic-and-fiscal-impact-of-aging-in-thailand).
- **When:** 2026-10.

## og-country-calibration/references/fiscal-consistency.md

### Fiscal path: debt below the plan while the primary balance matches

- **Lesson:** when the primary balance follows the plan but debt does not, compare near-term real
  interest and growth with the model's long-run values.
- **What happened:** debt ran 3 to 7 points of GDP below the plan's path while the primary balance
  matched. Thailand's near-zero inflation raises its real borrowing cost and lowers its real growth
  in the plan years relative to the model's long-run values. Not resolved in the dry run.
- **Evidence:** OG-THA-demo commit 3c8b79b (fiscal path panel) and the 14:12 entry of
  `PROGRESS.md` (local, unpublished).
- **When:** 2026-10.

## og-solver-diagnosis/references/failure-taxonomy.md

### Class C: an Anderson stall that came with a debt overshoot

- **Lesson:** a stall together with a drifting fiscal path points at the fiscal setup; fix it, then
  retry Anderson before shipping the damped fallback.
- **What happened:** run 1 (Anderson, `nu` 0.2) reached a distance of about 1e-4 and then bounced
  between 1e-4 and 1e-2, with debt drifting to 95% of GDP. It was stopped; the packaged default was
  switched to damped iteration, which converged in 55 iterations. The pension phase-in found later
  removed the overshoot, but Anderson was not retried, so OG-THA would ship the fallback.
- **Evidence:** OG-THA-demo commit bee2b36 ("damped TPI after the Anderson stall"); run logs
  `OG-THA-demo-runs/logs/example_run1.log` and `example_run2.log` (local, unpublished).
- **When:** 2026-10, ogcore 0.21.2.

### Class M: the start-cohort check was skipped

- **Lesson:** check the start cohorts' solves before attributing an early-year consumption jump to
  initial wealth.
- **What happened:** the baseline showed a one-year retiree consumption jump in 2026. It was
  attributed to OG-Core's default initial-wealth rescale (a 72% windfall per household) without
  checking the start cohorts, although ogcore 0.21.2 does not check or retry those solves
  (PSLmodels/OG-Core#1247). The cause is therefore unproven.
- **Evidence:** `DEMO_LOG.md` final rows and `RUN_SHEET.md` "Fragile points" (local, unpublished);
  https://github.com/PSLmodels/OG-Core/issues/1247.
- **When:** 2026-10, ogcore 0.21.2.

## og-solver-diagnosis/references/solve-procedures.md

### Run time with the damped fallback

- **Lesson:** the damped fallback is slower than the run rules' guide; record the time per
  iteration and do not treat it as a failure.
- **What happened:** with damped iteration each scenario's transition took 15 to 17 minutes (55
  iterations, about 17 seconds each, 10-core machine), against the 5 to 7 minutes the run rules
  give for a healthy baseline.
- **Evidence:** `DEMO_LOG.md` rows for runs 2 and 3 (local, unpublished).
- **When:** 2026-10.

## og-run-preflight/SKILL.md

### "Which world": "skip it" read as "skip the preflight"

- **Lesson:** a standalone OG repo skips only the "Which world" section, never the preflight.
- **What happened:** the agent read the section's "skip it" as permission to skip the preflight for
  an installer copy, and reported the two skills as conflicting. It ran the preflight anyway.
- **Evidence:** the agent's skill notes in `DEMO_LOG.md` (local, unpublished).
- **When:** 2026-10.
