# Preparing the calibration PR

What maintainers actually ask for. **[PHL #63 review, jdebacker]** Ask before push and before
opening the PR, never in the same step; the user merges.

## Register: the PR reports what was done; the docs carry the discussion

State each change and its anchor in a line or two ("unmodelled recurring revenue is carried by the
nearest-equivalent instruments: property-type taxes on the wealth tax, state-asset income on the CIT
adjustment, fees on `tau_c`") and point to the calibration chapter for the derivation, the
alternatives and the caveats. Design-justification paragraphs ("worth review", "the honest carrier",
why-not-X) belong in the PR only when you are asking the maintainers to decide something; otherwise
they read as asking for a debate nobody requested. **[PHL #85 feedback]**

PR style: narrative, plain language, the why first, detail pushed to the docs. Include a
changed-parameters table, the goodness-of-fit table, and an example macro-results table.

## Always include the goodness-of-fit table

The standard close for any calibration PR: every calibrated moment, `Model | Target | Source`, one
row per anchor, revenue lines first, then the external and fiscal anchors. Read the model column from
the solved SS pickle, never from memory.

| Moment | Model | Target | Source |
|---|---|---|---|
| PIT/Y … each revenue instrument … | | | collections source (e.g. OECD RevStats) |
| total revenue/Y | | | |
| RM/Y, K_f/K, D/Y, D_f/D, r_gov | | | central bank / treasury anchors |

Follow it with the tested block (suite count, SS RC error, TPI RC error vs tolerance, debt-path
behaviour vs target, with min and max) and the reform percent-change table (Y/C/K/L/r/w by year +
SS), in the same format across the family (PHL #68/#85 are examples).

## Show the before/after of every calibrated object the PR changes

Upfront; do not make them ask. On PHL #63 the maintainer's first request was a new-vs-old
side-by-side of the `io_matrix`. For each changed array or matrix (`io_matrix`, `gamma`, `Z`, tax
parameters), put an old → new table in the PR (or a reply thread) with the largest shifts called out
and explained by mechanism. Example: household energy spending moving off manufacturing onto
electricity (54% → 4% / 11% → 74%), because the value-added method traces demand to the industry
that makes it, not to the numeraire. The diff of a packaged JSON is unreadable; the side-by-side is
how a reviewer verifies the change does what you claim.

## Pre-empt the gamma_g question

The maintainer flagged that the SAM books all non-labour income as capital with no public-capital
attribution, so subtracting `gamma_g` implicitly from labour is wrong. State the construction: rescale
the SAM's total capital shares to the economy-wide total, then subtract `gamma_g`, so public capital
comes out of capital (the SAM measures labour's share well). If `gamma_g = 0` (e.g. ZAF), say so
(private = total, no carve-out) so the reviewer need not raise it.

## PR-explanation visuals are not docs visuals

The maintainer asked that a figure's "what's changing in this PR" annotation (a dashed old-vs-new
line) be removed from the version committed to the docs. Keep before/after annotations in the PR
conversation; the docs figure shows the calibrated state cleanly, because the docs describe the
calibration as it is, not the PR's delta.

## Explain derived mechanical corrections in plain language

A non-obvious fix (the chi/`p_tilde` units conversion; a Z-level factor rescale) needs: what was off,
the arithmetic that causes it, and that the constant is derived, not fitted. The same goes for
version-driven fixes: if an ogcore bump broke the example and you regenerated demographics or
parameters to fix it, say so and give the before/after resource-constraint numbers.

## Wrap-up before the PR

`make format`; `uv run python -m pytest -m 'not local' -q`; a CHANGELOG entry (before → after +
citation); docs with values glued from the JSON; `uv.lock` and `.python-version` out of the diff.
