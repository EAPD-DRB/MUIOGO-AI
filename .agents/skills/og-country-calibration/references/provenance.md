# Tracing where a calibrated value came from

Use this when someone asks where a number comes from, whether a value is still right, or before
re-calibrating a parameter of unclear origin. The rest of this skill sets values; this file
documents where existing ones came from.

In the EAPD-DRB repos many values were derived in standalone notebooks and hard-coded with no trace
back. Where the notebooks are available, look for a survey of which notebook derives which
parameter (for example, Model-tools keeps a dated one in `docs/`); re-verify any row before relying on
it.

## The three provenance patterns (classify first)

The same parameter can have different traceability in different repos:

1. **Live-recomputed:** code queries an API under `update_from_api=True`. The value's provenance is
   whatever the API returned on the last calibration date: record the endpoint, series ID and the
   access date implied by the JSON's git history (`git log -p -S <value> -- <json>`). Snapshots of
   one series drift between vintages.
2. **Frozen with a derivation function:** a documented function re-derives the value and the JSON
   is its output. Check that the arithmetic reproduces the shipped float exactly; an exact match
   closes the link, a mismatch is a finding, not a rounding issue.
3. **Frozen with a comment, or nothing:** the value sits in the JSON with at best a citation. Most
   tracing work is here, and so are undocumented placeholders.

## Tracing protocol

1. **Start from the shipped value.** The exact float is the strongest search key. JSON arrays put
   values on their own line, so grep the bare float (`grep -rn "0.24484763593657788"`), not the
   `"key": [...]` pattern (verified: the compact pattern misses). A float that is byte-identical in
   two country repos means a country-independent constant (paper regression, copied default), and
   that reshapes the search. Then walk the value's history; it is often the quickest guide.

   ```bash
   for c in $(git log --format=%h -- <path/to/params.json>); do
     echo "$c $(git show $c:<path/to/params.json> | python3 -c 'import json,sys; print(json.load(sys.stdin).get("<param>"))')"
   done
   ```
2. **Find the writer.** In-repo first: the modules and builder scripts that assemble the
   parameters; check whether the live-API path can overwrite the value. Then outward: notebooks,
   archived parameter scripts, R or Stata pipelines, `git log -S` on the JSON. Where the repo's own
   code has since moved to a live API, follow the repo's writer before an older notebook chain.
3. **Walk to the ultimate source.** Intermediate CSVs are links, not sources; find who wrote
   them. Several are manual downloads with the URL only in a notebook comment, and some have no
   identified producer; record that plainly. Sources bottom out at: an official
   API + series ID + date; a manually-downloaded official file + URL + vintage; a paper's
   published coefficients + full citation; or "underived placeholder" (say so).
4. **Check lineage traps:**
   - **Silent fallbacks**: the demographics path falls back from the UN API to the
     `EAPD-DRB/Population-Data` GitHub mirror when the API fails, so the actual source of a given
     vintage may be the mirror. Look for fallback messages in the code rather than assuming.
   - **Forked calibration states**: scratch dirs (e.g. `notebooks/usaid_testing/`) contain
     modified copies of `og*_default_parameters.json`. Confirm you are tracing the canonical
     repo's file, by path, before concluding anything.
   - **Vintage traps**: API revisions and GDP rebasing move ratios with no real change; record
     the vintage next to the value (the Gini concept: households-demographics.md; the GDP basis:
     validation-dashboard.md).
   - **Series that stopped reporting**: a series can be zero-filled, blank, or last reported
     years before the target year, and a "latest available year" fallback then silently returns
     an old value (one IMF social-benefits series had data only for 2002). Check the series has
     data near the target year; a silent fall back to an old year is a provenance break.
   - **Concept**: record whether the series matches the concept the model needs (for `alpha_T`,
     cash transfers only; macro-open-economy.md).
   - **Secrets**: notebooks in the tracing path contain live bearer tokens in cells and
     `un_api_token.txt` files. Do not quote, copy, or commit them; flag them for rotation when
     you find them.

## Recording the chain (the deliverable)

Write the chain into the repo you traced, not into the notebooks dir: the repo's parameter docs
(`docs/.../macro.md` etc. per family convention) or the derivation docstring. Per parameter:

```
<param> = <value>  [pattern: live-API | derived-frozen | frozen]
  <- <in-repo writer: file/function, or "hand-set in JSON">
  <- <notebook/script + cell/section that derived it>       (if any)
  <- <intermediate file + its producer>                     (if any)
  <- SOURCE: <institution/API/paper, series ID, URL, vintage/access date>
  verified: <arithmetic check done / value re-fetched / not verifiable — why>
```

For numbers quoted in prose, recommend reading them from the JSON in the docs
(validation-dashboard.md, keeping numbers true to the run). If the trace ends at "no source
found", the record is `PLACEHOLDER — undocumented, needs recalibration`, which is exactly
the state this skill exists to fix.

Scope: draft the provenance record in the repo you traced, following the project's rules.
Re-verifying a chain by solving is a separate model run, outside this scope.
