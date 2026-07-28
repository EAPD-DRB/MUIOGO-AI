# Calibration rubric

Score each dimension from 0 to 100 using the anchors below, then apply the weights. Scores between anchors require written justification.

| Dimension | Weight | 0–39 | 40–59 | 60–79 | 80–100 |
|---|---:|---|---|---|---|
| Evidence and provenance | 10 | Core data absent/untraceable | Patchy sources or transformations | Most core data traceable; uncertainty incomplete | Complete register, transformations, conflicts, and uncertainty documented |
| Country representation | 10 | Generic template or material omissions | Partial national structure | Most material national features represented | Material technologies, resources, policies, trade, and institutions verified |
| Historical initial state | 10 | Stocks/boundaries absent or implausible | Partial initialization | Main inherited stocks and boundaries matched | Audited asset/resource/land/water starting state with reconciled sources |
| Physical and accounting integrity | 10 | Broken references, units, or balances | Major unresolved warnings | Coherent with minor documented limitations | Independent balance/unit tests pass at relevant resolution |
| Historical reproduction | 20 | Core outcomes fail or are untested | Aggregate fit only or repeated large errors | Most important outcomes within declared tolerances | Strong multi-layer fit across stocks, flows, shares, and time patterns |
| Nexus fidelity | 10 | Claimed links absent | Links exist but are generic/untested | Material links parameterized and partly tested | Cross-sector flows and feedbacks tested against country evidence |
| Independence from forcing | 15 | Outcomes mostly fixed or undisclosed | Heavy tuning/constraint dependence | Mostly endogenous with justified constraints disclosed | Core historical behavior independently reproduced; forcing sensitivity tested |
| Held-out validation | 10 | Held-out evidence fails | Minimal or weakly independent test | At least one meaningful held-out period | Multiple held-out tests or strong cross-validation at relevant resolution |
| Robustness and reproducibility | 5 | Cannot reproduce; key uncertainty ignored | Partial rerun or sensitivity evidence | Reproducible case plus main sensitivities | Automated rerun, versioned evidence, uncertainty and structural sensitivity |

## Weighted score and preliminary bands

- **Unacceptable:** below 50
- **Acceptable:** 50–69
- **Good:** 70–84
- **Excellent:** 85–100

These bands are preliminary. Critical gates, domain floors, forcing, held-out validation, and reproducibility caps override them.

## Domain floors

Define core domains from the claimed scope. For full CLEWs use energy, land, water, climate, and cross-nexus links.

- Any core domain below 40: Unacceptable.
- Any core domain below 60: maximum Acceptable.
- Any core domain below 70: maximum Good.
- A missing claimed domain or material nexus link: scope gate fails.

The domain score summarizes historical adequacy and structural realism for that domain; it is not a duplicate count in the weighted total.

## Grade caps and overrides

- Critical executable, referential-integrity, physical/accounting, or scope gate failure: Unacceptable.
- Historical evidence or forcing disclosure gate failure: Not assessable.
- No meaningful held-out validation: maximum Good.
- Materially incomplete reproducibility: maximum Acceptable.
- Apply history-fixed forcing caps from `forcing-classification.md`.
- An out-of-sample failure on a decision-critical outcome can make the result Unacceptable regardless of aggregate score.
- Excellent additionally requires: all critical gates pass, high-confidence evidence, no core domain below 80, at least one meaningful held-out test, and documented robustness tests.

## Confidence

Confidence describes evidence behind the grade, not model quality.

- **Low:** core evidence sparse/conflicting; forcing or transformations hard to trace; few observations; major reviewer inference.
- **Medium:** most evidence traceable and core comparisons present; some uncertainty, coverage, or independence gaps.
- **High:** comprehensive traceable evidence, forcing audit, held-out tests, reproducible workflow, and uncertainty characterization.

A model can receive a Good grade with Medium confidence. Do not use High confidence when the comparison relies on a single aggregate year.

## Fitness for purpose

Assess separately:

| Use | Minimum expectation |
|---|---|
| Teaching / workflow demonstration | Technical validity; limitations clearly disclosed |
| Exploratory national scenario analysis | Acceptable calibration, relevant domain coverage, transparent assumptions |
| Policy option comparison | Good calibration, relevant held-out/robustness evidence, stakeholder/data review |
| Investment or official planning support | Good or Excellent, high decision-variable coverage, uncertainty and constraint sensitivities |
| Operational adequacy / reliability | Temporal, network, and reliability representation validated for that purpose; an annual CLEWs model normally fails this gate |

Use **suitable**, **conditionally suitable**, or **unsuitable**, and name the conditions.

## Tolerances

There is no universal error threshold for all CLEWs variables. Set tolerances before examining the model result, based on:

- measurement uncertainty;
- aggregation and temporal resolution;
- materiality to the decision;
- expected structural approximation;
- accepted domain practice.

The comparison script treats tolerance as a declared evaluation threshold, not a scientific constant. Every tolerance needs a rationale.
