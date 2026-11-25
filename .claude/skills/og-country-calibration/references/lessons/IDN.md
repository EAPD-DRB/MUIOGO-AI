<!-- GENERATED FILE - do not edit here.
     Source: docs/og-lessons/IDN.md
     Regenerate: python scripts/sync_shared.py -->

# Indonesia (IDN): lessons behind the OG skills

What happened behind lessons in the OG skills (og-country-calibration,
og-multi-industry-calibration, og-solver-diagnosis, og-run). The skills teach the method; these
are one country's numbers, kept here so the skills stay general. They record what was true when
written; check the country repo before relying on any of them. Do not copy them into another
country's calibration.

Contents (by the skill file each entry backs; search a file for its `###` headings)
- og-country-calibration/SKILL.md
- og-country-calibration/references/taxes-informality.md
- og-country-calibration/references/households-demographics.md
- og-country-calibration/references/validation-dashboard.md
- og-solver-diagnosis/references/solve-procedures.md

## og-country-calibration/SKILL.md

### The mental model: judge the joint steady state against data

- **Lesson:** most parameters are weakly identified alone, so the test is whether the joint steady
  state resembles the economy.
- **What happened:** OG-IDN's macro chapter says the parameters are "only weakly identified from
  the data on their own" and compares the packaged steady state with Indonesian data, next to the
  prior baseline. The recalibration moved `K_f/K` from 0.44 to 0.17 (data about 0.20), `r` from
  0.043 to 0.063, `K/Y` from 4.44 to 3.64, and `D/Y` to 0.40. IDN backs the joint-test half of the
  lesson. Its table leads with `K_f/K` and `r`, not fiscal rows, and has one revenue row
  (`REV/Y` 0.15); the fiscal-first framing is tagged to ZAF, not IDN.
- **Evidence:** https://github.com/EAPD-DRB/OG-IDN/commit/185c470053e75fda9abf12f108fe366aa2578eb1
  (https://github.com/EAPD-DRB/OG-IDN/pull/55); current text at
  https://github.com/EAPD-DRB/OG-IDN/blob/a52f2b9c557ee4a351458b9c4246080d9ea83ca2/docs/book/content/calibration/macro.md
- **When:** 2026-07 (OG-IDN 0.2.0); checked at upstream/main a52f2b9.

## og-country-calibration/references/taxes-informality.md

### Standing check: the bequest tax: IDN ships 0

- **Lesson:** compute `tau_bq` from collections over model bequest flows, and grep every port for
  it.
- **What happened:** the first OG-IDN commit shipped `tau_bq = 0.2`. PR #12 set it to 0.0 in
  August 2024, and the taxes chapter says wealth and bequest taxes are zero in the default
  calibration. upstream/main ships 0.0 in both the single-industry and the multisector JSON. Zero
  was set by statement, not derived from collections.
- **Evidence:** 0.2 in https://github.com/EAPD-DRB/OG-IDN/commit/621769f755e48e2acc470857782872d7ac108383;
  0.0 in https://github.com/EAPD-DRB/OG-IDN/commit/3c6901666dd93c9f43aceb6ea1f75edf47c00146
  (https://github.com/EAPD-DRB/OG-IDN/pull/12); current JSON at
  https://github.com/EAPD-DRB/OG-IDN/blob/a52f2b9c557ee4a351458b9c4246080d9ea83ca2/ogidn/ogidn_default_parameters.json
- **When:** 2024-06 (0.2), 2024-08 (0.0); checked at upstream/main a52f2b9 on 2026-10-19.

### Informality: the maturity ladder: a structural two-sector demo ("Option B")

- **Lesson:** OG-Core's multi-industry machinery with an informal industry (no CIT, no VAT, lower
  capital intensity, its own consumption share) is illustrative, not revenue-anchored.
- **What happened:** a UN-tutorial script, `run_og_idn_informal.py`, sets `M = I = 2` with the
  first industry informal: `gamma` 0.1 against 0.41, `cit_rate` 0 against 0.22, `tau_c` 0 against
  0.11, `alpha_c` 0.36 and 0.64 (36% of GDP, from a World Bank document), and an identity
  `io_matrix`. The reform formalizes it (informal `gamma` to 0.3, full CIT and VAT, `alpha_c` 0.25).
  Nothing is anchored to revenue. The "Option B" label comes from OG-ETH's informality assessment,
  which calls this OG-IDN script the richest explicit treatment in the family.
- **Evidence:** https://github.com/EAPD-DRB/OG-IDN/commit/71383e69a6df2df99a4ad2c2b74ec94c2f08c797
  (https://github.com/EAPD-DRB/OG-IDN/pull/29); script at
  https://github.com/EAPD-DRB/OG-IDN/blob/a52f2b9c557ee4a351458b9c4246080d9ea83ca2/docs/book/content/UNtutorial/materials/PrevReformsNotebooks/run_scripts/run_og_idn_informal.py;
  assessment at
  https://github.com/marcelolafleur/OG-ETH/blob/356673faefe0e072abf5d5f7cb45b66bf0803930/INFORMALITY.md
- **When:** 2025-03 (script); 2026-07 (ETH assessment).

## og-country-calibration/references/households-demographics.md

### Earnings (the e ability matrix): the Gini tilt to 38.3

- **Lesson:** the family reuses OG-USA's `e` matrix with a single-scalar exponential tilt to the
  country's Gini.
- **What happened:** OG-IDN's `get_e_interp` tilts the OG-USA matrix to `gini_to_match=38.3`,
  which its docstring gives as Indonesia's 2023 World Bank Gini (`SI.POV.GINI`). `calibrate.py`
  calls it with the default. Only the tilt ships; there is no age-shape step. The earnings
  chapter describes the same method.
- **Evidence:** https://github.com/EAPD-DRB/OG-IDN/commit/014b3ea2b3baed29813c617e0cce0af01f6c83f7
  (https://github.com/EAPD-DRB/OG-IDN/pull/10); current code at
  https://github.com/EAPD-DRB/OG-IDN/blob/a52f2b9c557ee4a351458b9c4246080d9ea83ca2/ogidn/income.py
- **When:** 2024-08; still true at upstream/main a52f2b9.

### Demographics: method and country_id: one named constant

- **Lesson:** use a single named constant (`UN_COUNTRY_CODE`) at both call sites, not an inline
  literal.
- **What happened:** OG-IDN added `country_id="360"` in June 2024. Inside PR #12 a commit changed
  both call sites to "710" (South Africa); the next day, in the same PR, `UN_COUNTRY_CODE = "360"`
  replaced the literals, so main never shipped 710. The constant is now also used by
  `update_baseline_demographics.py`. There is no test that pins it to 360.
- **Evidence:** https://github.com/EAPD-DRB/OG-IDN/commit/d1c42082742b8b8b59bc6091de40b6b81e4dbae6
  (360); https://github.com/EAPD-DRB/OG-IDN/commit/af8abdc35a0765098ecd7dd05a35e84b20ab67f1 (710);
  https://github.com/EAPD-DRB/OG-IDN/commit/96cdac53fbcf1cc43982ddab2fe8065799632cb3 (constant);
  https://github.com/EAPD-DRB/OG-IDN/pull/12.
- **When:** 2024-06 to 2024-08.

### Pensions: the factor seed is pinned at the validator cap

- **Lesson:** for a high-denomination currency, express `mean_income_data` in millions, and check
  that the factor seed sits in the validator range; a seed of exactly 500,000 was probably clipped.
- **What happened:** OG-IDN upstream/main ships `initial_guess_factor_SS` exactly 500,000.0,
  OG-Core's validator maximum, with `mean_income_data` 77,205,806 rupiah (about 7.72e7). PR #55
  raised the seed from 71,707 and says the true model-to-rupiah factor is about 1e8, so the seed is
  pinned at the cap and the `r` and `TR` guesses carry the speed-up. The multisector JSON still
  ships 71,707. OG-Core's `SS_fsolve` divides the factor residual by 1,000,000.
- **Evidence:** https://github.com/EAPD-DRB/OG-IDN/pull/55;
  https://github.com/EAPD-DRB/OG-IDN/commit/99160b80d10c60c21cf26e9d8a80dcac744f81f8; CHANGELOG
  0.2.0 at
  https://github.com/EAPD-DRB/OG-IDN/blob/a52f2b9c557ee4a351458b9c4246080d9ea83ca2/CHANGELOG.md;
  JSON at
  https://github.com/EAPD-DRB/OG-IDN/blob/a52f2b9c557ee4a351458b9c4246080d9ea83ca2/ogidn/ogidn_default_parameters.json;
  `mean_income_data` from https://github.com/EAPD-DRB/OG-IDN/commit/e0c5fc52820672ae2de4f5167c0486704c3b0440
  (https://github.com/EAPD-DRB/OG-IDN/pull/16); cap at
  https://github.com/PSLmodels/OG-Core/blob/81f45496b9aec37bc82dc22aeebba31f055ca5e2/ogcore/default_parameters.json
  and residual scaling in
  https://github.com/PSLmodels/OG-Core/blob/81f45496b9aec37bc82dc22aeebba31f055ca5e2/ogcore/SS.py
- **When:** 2026-07 (seed, OG-IDN 0.2.0); checked at upstream/main a52f2b9 on 2026-10-19; cap
  checked on OG-Core master 81f4549 (v0.21.2).

## og-country-calibration/references/validation-dashboard.md

### The steady-state dashboard: a data-comparison table in macro.md

- **Lesson:** put a table in `macro.md` comparing the solved steady state with data targets, each
  with a source.
- **What happened:** OG-IDN's macro chapter has a seven-row table: `K_f/K`, `r`, `K/Y`, `C/Y`,
  `I/Y`, `D/Y` and `REV/Y`, each with prior baseline, recalibrated value, Indonesian data and
  source (BI IIP, World Bank, IMF WEO). It has no PIT, CIT, `TR/Y` or `NX/Y` rows and is not tiered
  fiscal first.
- **Evidence:** https://github.com/EAPD-DRB/OG-IDN/commit/185c470053e75fda9abf12f108fe366aa2578eb1;
  https://github.com/EAPD-DRB/OG-IDN/pull/55.
- **When:** 2026-07.

## og-solver-diagnosis/references/solve-procedures.md

### Warm-starting the steady state: the right factor seed cannot be entered as a parameter

- **Lesson:** `initial_guess_factor_SS` is capped at 500,000, while a high-denomination currency
  needs far more, so pass `factor` directly.
- **What happened:** OG-IDN's true factor is about 1e8, roughly 200 times the cap, so its shipped
  seed sits at 500,000. Details and evidence are in the Pensions entry above.
- **Evidence:** https://github.com/EAPD-DRB/OG-IDN/pull/55.
- **When:** 2026-07.
