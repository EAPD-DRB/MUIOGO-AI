---
name: og-multi-industry-calibration
description: >-
  Builds or reviews a multi-industry (M>1) OG-Core country calibration from a SAM or input-output
  tables and keeps it consistent with the single-industry model. Use when deriving alpha_c,
  io_matrix, industry capital shares, sector TFP or sector tax rates; packaging the multisector
  overlay; solving a multi-industry steady state by continuation; or comparing single- and
  multi-industry results.
---

# Multi-industry calibration for an OG-Core country model

A multi-industry model is a second representation of the same economy as the single-industry
model. Most of the work is not deriving numbers from a SAM; it is making sure the two models still
describe the same country, and getting a stiff model to solve. OG-Core ships the machinery and no
guidance on any of this; the method here is the family's own.

**Prerequisite:** the single-industry calibration is settled first (og-country-calibration). The
multi model inherits every economy-wide value from it, and its fiscal and macro moments are judged
against it.

**Run rules:** follow [og-run-rules.md](references/og-run-rules.md): under ten minutes for a
healthy single-industry baseline, the example-script pattern, always parallel, Anderson with
`nu` ≤ 0.2, preflight, and the user's explicit go before any solve beyond a quick check.

## Which world

This skill acts on **one** world: the runtime installation reached by `muiogo-ai`,
unless the user explicitly asked for their own live one (`muiogo-live`). Never use
bare `muiogo`, and never fall back to it. Every command prints a `world:` line to
stderr — read it, and name that world when you report a result or a number. Worlds
hold different OG checkouts and different model registries, so the same country
model can exist in both at different commits. Locate the checkout you mean with
`muiogo-ai status` rather than assuming a path. Full rules:
`../WORLD_DISCIPLINE.md`.

## Where the worked code is

Three calibrations solved different parts of the problem. Read the code on each repo's
multi-industry branch, not only its docs; docs and code disagree in places in all three.

| Repo | Data | Read it for |
|---|---|---|
| OG-PHL (the reference) | IFPRI SAM, one activity per commodity | Builder, overlay and tests; the chi conversion; the continuation solver and `validate_ss`; the composite-price experiment; the practitioner guide `docs/single_multi_calibration_guide.md` |
| OG-ZAF | UNU-WIDER SAM, several activities per commodity | Make/use Leontief from a raw SAM; employment splits; the Z-level rescale to the single model's `factor`; a cold solve |
| OG-BRA (the most developed) | Input-output tables with a published domestic Leontief | The mixed-income split; exact domestic tracing; per-good `tau_c` and per-industry CIT; funded public capital; the M=1 equivalence test; the concordance test |

OG-IDN and OG-ETH carry only the upstream scaffold (naive `io_matrix`, one `gamma` copied to every
industry, `Z` = 1). Do not treat their multisector files as worked examples.

## The ladder

Each input has a minimal and a better rung. Take the highest the data supports, and say which in
the docs.

| Input | Minimal | Better | Best seen |
|---|---|---|---|
| `io_matrix` | direct-use shares | value-added trace through a Leontief inverse you build | published domestic tables, no import assumption (BRA) |
| `gamma_m` | single `gamma` everywhere | SAM factor shares rescaled to the single model's level | plus a per-industry mixed-income split (BRA) |
| `Z_m` | 1 everywhere | Solow residual with survey employment | same, with capital allocated consistently with `gamma` |
| taxes | single-model scalars | — | per-good `tau_c` from the use table, per-industry CIT from collections (BRA) |
| solve | cold | continuation from a flat anchor | — |

## What matters most

- **Ship a lean overlay**, loaded after the single-industry base and written by a builder. Loaded
  alone it silently falls back to US defaults.
- **Check that the mapping partitions the data.** Unmapped or misspelled codes vanish from every sum
  without an error; two of three repos shipped one.
- **The capital-goods producer goes last** (OG-Core's numeraire, and the only producer of investment
  and government goods). Fold real estate into a broader group.
- **Trace `io_matrix` through value added**, with algebra that fits the data (one producer per
  commodity or several). The naive matrix puts most goods on manufacturing.
- **Take `gamma`'s level from the single model** and the dispersion from the data.
- **Convert `chi_n` and `chi_b` by `k^(σ−1)`** for OG-Core's unnormalised composite price. In PHL it
  closed half to four fifths of the gaps to the single model.
- **Prove the plumbing with the equivalence test**: identical industries must reproduce M=1.
- **`factor` is the best single number for a level misalignment.** Use the Z level to align
  `factor`, never to close `r` or `K_f/K` gaps.
- **Try a cold solve; fall back to continuation** when relative prices spread widely.
- **Run the same reform through both models** and compare the percent-change tables.

## Checklist

Copy this into the work log.

```
- [ ] 1.  Single-industry model settled; note its gamma + gamma_g, tau_c, CIT, factor and seeds.
- [ ] 2.  Look for existing work first: the repo's multi-industry branch, open PRs, and open
          OG-Core work touching io_matrix or the composite price (alignment.md, "When OG-Core
          changes").
- [ ] 3.  Data: find the SAM or IO tables; check make structure, domestic vs total use, totals,
          year; validate against the national accounts (inputs.md).
- [ ] 4.  Concordances and industries: partition test + run-time assert; capital-goods producer
          last; real estate folded in.
- [ ] 5.  Inputs: alpha_c, gamma_m (mixed-income split if available, rescale to the single's
          level, then carve out gamma_g), io_matrix (value-added trace), L_m, Z_m; sector taxes
          only if published.
- [ ] 6.  Builder writes the overlay; chi conversion from alpha_c and the base sigma; Anderson
          and nu in the overlay; seeds stay in the base.
- [ ] 7.  Tests: overlay keys, JSON == builder, two-step load, chi conversion, concordance,
          row sums, equivalence test.
- [ ] 8.  Solve: cold first; continuation if it fails; structural checks after every solve.
- [ ] 9.  Align: comparison dashboard against the single; factor first; Z-level rescale only for
          factor.
- [ ] 10. Same reform through both models; signs and magnitudes agree.
- [ ] 11. Docs (sources and methods, interpretation caveats) and the PR (og-country-calibration's
          calibration-pr.md).
```

Loop-backs:
- **The equivalence test fails** → the overlay, the chi conversion or the mapping is wrong. Fix it
  before any calibrated solve; nothing downstream is interpretable until it passes.
- **`factor` is far off** → a level misalignment upstream (often the `gamma` target or the chi
  conversion). Fix it before reading any other gap.
- **The single model is recalibrated** → rebuild the overlay and re-solve both models in the same
  change; update any numbers one model's docs quote about the other.
- **One industry's Z is wildly out of line** → its employment number (step 5).
- **The reform disagrees in sign between the models** → back to step 9; do not ship.

## Reference files

| File | Read when |
|---|---|
| [inputs.md](references/inputs.md) | Packaging; finding and checking the data; concordances; defining industries and goods; deriving `alpha_c`, `gamma_m`, `io_matrix`, `L_m`, `Z_m`; sector taxes; public capital |
| [alignment.md](references/alignment.md) | How OG-Core treats industries; aligning in either direction; the chi conversion; the Z level; the equivalence test; continuation; checking the solved model; fault-finding; upstream changes; tests |
| [og-run-rules.md](references/og-run-rules.md) | Before any solve |

## Related skills

- `og-country-calibration`: the single-industry calibration this builds on, the fiscal dashboard,
  and the calibration PR format.
- `og-run`, `og-run-preflight`: launching solves.
- `og-solver-diagnosis`: a solve that will not converge.
- `og-clews-linked-run`: coupled OG-CLEWS work needs a multi-industry model with an electricity
  industry.

If one is not available to you, do the job directly and say which skill would have covered it.

## Approval gates

Build, derive, test and commit locally freely. Solves beyond a quick steady-state check, pushing,
opening PRs and anything across several repos are proposed and wait for the user. Ask before push
and before the PR, never in the same step. Never merge.
