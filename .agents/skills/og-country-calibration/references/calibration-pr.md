# The calibration PR

A calibration PR reports how the calibrated model fits the country's data. Reviewers and later
users take it as the baseline's description, so it shows the fit; it does not tell how the
calibration was reached. Follow the repo's own PR conventions and the maintainers' earlier
calibration PRs for length and layout.

## What it contains

**Rule.** In this order, in plain language:
1. One paragraph: what the calibration is anchored to (the start year, the GDP basis, the main
   sources) and where the docs give each derivation.
2. A table of the calibration: each block, what sets it, and the source.
3. The fit: model against data for every scored moment, each with its source
   (validation-dashboard.md), steady state and early transition labelled; then the gaps that
   remain, each with its measured cause.
4. The figures that show the fit: the fiscal path panel, and by-age fits (hours, consumption,
   wealth) where calibrated.
5. The changed parameters, old value against new; for a changed array or matrix (`io_matrix`,
   `gamma` by industry, tax parameters) a side-by-side with the largest shifts explained by
   mechanism, since the packaged JSON's diff is unreadable. [PHL]
6. What it requires (an unreleased ogcore change, a data file), if anything.

**Check.**
- Every number and figure comes from the final run and the packaged JSON through the repo's doc
  tooling; none is typed by hand.
- Parameter changes are shown old against new (item 5); results are not compared with earlier
  runs, tuning rounds, other countries or alternatives tried, unless the maintainers' convention
  asks for a comparison with the previous release; no
  reform results (a calibration is judged by its fit; reform results belong to scenario work); no
  internal labels ("round", "dial", "official run"); no test counts or run times (the repo's CI
  reports them).
- Every term a reader outside the project would not know is explained where it first appears.
- Before the push, an independent reviewer checks every number and claim against the run and the
  sources, and the findings are fixed. [ETH]

**Why.** A fit report lets a reviewer judge the baseline quickly; history, alternatives and policy
results invite debates nobody asked for and go stale. A review of a text its author had already
checked found a dozen problems, two serious. [ETH, PHL]

## What the docs carry

The calibration chapters hold the derivations, alternatives considered and caveats; the PR points
to them. Docs describe the calibration as it is: a figure annotated to show what a PR changed
belongs in the PR conversation, not in the committed docs. [PHL]

## Explaining a derived correction

For a non-obvious fix (a units conversion, a rescaled level), state what was off, the arithmetic
that causes it, and that the constant is derived, not fitted. For a fix forced by an ogcore
upgrade, say what broke and give the resource-constraint error before and after.

## The multi-industry overlay

A multi-industry calibration ships as its own generated file and leaves the single-industry
default working. Its PR states how the capital shares were built (rescaled to the economy-wide
share, with public capital taken out of capital, or `gamma_g` zero) so the reviewer need not ask
(og-multi-industry-calibration). [PHL, ZAF]
