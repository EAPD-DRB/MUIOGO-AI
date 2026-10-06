---
name: calibration-provenance
description: "Traces a calibrated parameter in an OG-Core country repo back to its source (notebooks, intermediate files, R/Stata pipelines, live APIs or cited papers) and records the chain in the repo. Use when asked where a number comes from, whether a value is still right, or what the source of gamma, zeta_K, r_gov_shift or the e-matrix is, and before recalibrating a parameter of unclear origin. og-country-calibration sets values; this skill documents where existing ones came from."
---

# Calibration provenance

24+ loose notebooks in the user's notebooks directory (`~/Projects/notebooks` on the machine
the map was surveyed on) derive parameters that get hard-coded into country
repos with no trace back — and the notebooks dir has no README. This skill is the tracing
protocol plus the map of what's already known (`references/notebook-map.md` — read it before
searching blind; it lists which notebook derives which parameter, the intermediate-file
producer/consumer graph, and two fully-worked chains).

## Which world

This skill acts on **one** world: the runtime installation reached by `muiogo-ai`,
unless the user explicitly asked for their own live one (`muiogo-live`). Never use
bare `muiogo`, and never fall back to it. Every command prints a `world:` line to
stderr — read it, and name that world when you report a result or a number. Worlds
hold different OG checkouts and different model registries, so the same country
model can exist in both at different commits. Locate the checkout you mean with
`muiogo-ai status` rather than assuming a path. Full rules:
`../WORLD_DISCIPLINE.md`.

## The three provenance patterns (classify first)

The same parameter shows different traceability across sibling repos — verified live for
`r_gov_scale`/`r_gov_shift` (identical regression constant `0.24484763593657788` in ZAF and ETH):

1. **Live-recomputed** (ZAF's `gamma`): code in `macro_params.py` queries an API under
   `update_from_api=True`. The JSON value's provenance is "whatever the API returned on the last
   calibration date" — the notebooks only prototype the query. Record the API endpoint, series
   ID, and the *access date implied by the JSON's git history* (`git log -p -S <value> --
   <json>`), not the notebook's printed value (observed drift: 0.4136 → 0.43608 → 0.47164 across
   snapshots of the same ILOSTAT series).
2. **Frozen + derivation function** (ETH's `estimate_r_gov`): a documented function re-derives
   the value; the JSON is its output. Verify the arithmetic actually reproduces the shipped
   value (worked check: `-0.03376625... - 0.04·0.3² = -0.03736625...`, exact match to the JSON).
   An exact match closes the link; a mismatch is a finding, not a rounding issue.
3. **Frozen + comment (or nothing)** (PHL's `r_gov_shift`): the value sits in the JSON with at
   best a docstring citation. This is where real tracing work lives — and where the
   undocumented-placeholder pitfall (`zeta_K = 0.9`) hides.

## Tracing protocol

1. **Start from the shipped value.** The exact float is the strongest search key — but JSON
   arrays put values on their own line, so grep the bare float (`grep -rn "0.24484763593657788"`),
   not the `"key": [...]` pattern (verified: the compact pattern misses). A float appearing
   byte-identical in two country repos means a country-independent constant (paper regression,
   copied default) — that reshapes the search. Then walk the value's history: it often tells the
   story fastest.

   ```bash
   for c in $(git log --format=%h -- <path/to/params.json>); do
     echo "$c $(git show $c:<path/to/params.json> | python3 -c 'import json,sys; print(json.load(sys.stdin).get("<param>"))')"
   done
   ```
2. **Find the writer.** In-repo first: `macro_params.py`, `calibrate.py`, `income.py`, builder
   scripts; check whether the live-API path can *overwrite* the value (the gamma-clobber bug
   class). Then outward: the notebooks directory (use the map), `archive/macro_params.py` (the
   notebooks' consolidation point), R pipelines (`factor_j/`, `e_adj_factors/`), Stata `.do`
   files, `git log -S` on the JSON. The notebook map is a dated survey: where the repo's own code
   has since moved to a live API (ZAF's `alpha_T`/`alpha_G` after the 2026 SDMX rewrite), check
   `git log -S` on the repo's writer before following the map's older notebook chain.
3. **Walk to the ultimate source.** Intermediate CSVs are links, not sources — find who wrote
   them (several are manual downloads with the URL only in a notebook comment; some have *no
   identified producer* — record that honestly). Sources bottom out at: an official
   API + series ID + date; a manually-downloaded official file + URL + vintage; a paper's
   published coefficients + full citation; or "underived placeholder" — say so.
4. **Check lineage traps:**
   - **Silent fallbacks**: the demographics path falls back from the UN API to the
     `EAPD-DRB/Population-Data` GitHub mirror when the API fails — the *actual* source of a given
     vintage may be the mirror. Look for fallback messages in the code, don't assume.
   - **Forked calibration states**: scratch dirs (e.g. `notebooks/usaid_testing/`) contain
     modified copies of `og*_default_parameters.json`. Confirm you are tracing the canonical
     repo's file, by path, before concluding anything.
   - **Vintage traps**: API revisions and GDP rebasing move ratios with no real change; record
     the vintage next to the value (the Gini-concept and GDP-vintage rules in
     `og-country-calibration` apply here verbatim).
   - **Series that stopped reporting**: a series can be zero-filled, blank, or last reported
     years before the target year, and a "latest available year" fallback then silently returns
     an old value (ETH's IMF social-benefits series has data only for 2002). Check the series has
     data near the target year; a silent fall back to an old year is a provenance break.
   - **Concept**: record whether the series matches the concept the model needs (for `alpha_T`,
     cash transfers only; see `og-country-calibration`).
   - **Secrets**: notebooks in the tracing path contain live bearer tokens in cells and
     `un_api_token.txt` files. Never quote, copy, or commit them; flag them for rotation when
     encountered.

## Recording the chain (the deliverable)

Write the chain into the repo you traced, not into the notebooks dir — the repo's parameter docs
(`docs/.../macro.md` etc. per family convention) or the derivation docstring. Per parameter:

```
<param> = <value>  [pattern: live-API | derived-frozen | frozen]
  <- <in-repo writer: file/function, or "hand-set in JSON">
  <- <notebook/script + cell/section that derived it>       (if any)
  <- <intermediate file + its producer>                     (if any)
  <- SOURCE: <institution/API/paper, series ID, URL, vintage/access date>
  verified: <arithmetic check done / value re-fetched / not verifiable — why>
```

Recommend (don't auto-create) a value-pinning test for chain ends that should never drift
silently, and the `{glue:text}` docs pattern for numbers quoted in prose — both are established
family practice (see og-country-calibration → Validation). If the trace ends at "no source
found", the honest record is `PLACEHOLDER — undocumented, needs recalibration`, which is exactly
the state og-country-calibration exists to fix.

Scope of action: drafting the provenance record and committing it locally is this skill's job
(if an open branch or PR already rewrites the same doc section, ask which branch first);
pushing it or opening a PR against a country repo is the user's call, asked separately
(long computations, pushes and PRs each need the user's explicit go). Never re-run a calibration or launch a solve to
"re-verify" a chain — propose it.
