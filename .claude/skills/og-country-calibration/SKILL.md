---
name: og-country-calibration
description: >-
  Calibrates or reviews an OG-Core overlapping-generations country model (OG-USA/PHL/ZAF/IDN/BRA/ETH
  or a new port). Use when setting or checking macro and open-economy parameters, gamma, the
  earnings matrix, demographics, pensions, initial wealth, chi_n, taxes or informality; when porting
  the model to a new country; or when validating a steady state or transition path against country
  data. Multi-industry work has its own skill. Methods and pitfalls, not one country's numbers.
---

# Calibrating an OG-Core country model

Transferable lessons from the OG-Core country family. A method-and-pitfall playbook, not a table of
values: every number here is an example; derive your own.

**Tags.** `[family]` done the same way across most repos; `[emerging]` good practice in one or two;
`[net-new]` done nowhere yet, do it anyway. A country tag (`[PHL]`) records where a lesson was
learned, never where it applies; a conditional method states its condition as a country
characteristic (informal, remittance-dependent, net creditor, distressed sovereign). What happened
behind each tag, with its numbers and evidence, is in Model-tools
[`docs/og-lessons/<CODE>.md`](https://github.com/EAPD-DRB/Model-tools/tree/main/docs/og-lessons);
a `(history: XXX)` marker points there. The history is for investigation, not input. When your
country teaches something new, record it as the maintenance guide in that repo says
(`docs/og-skills-maintenance.md`).

**Best effort on every block, graded honestly.** Each block has a ladder from minimal to ideal. Use
the highest rung the data supports; otherwise take a lower one and say so. A documented fallback is
a legitimate calibration; an undocumented placeholder is the error this skill exists to prevent.
For every number, start with the national institution that owns it.

Verify every claim against the checked-out ref of the repo in front of you, and check what your
installed ogcore has: parameters appear, get renamed or change shape between releases.

## Which world

This applies when you work through MUIOGO. For a standalone OG repo installed with OG-Core's
installer (no `muiogo-ai` involved), skip it: the checkout you were given is the world. **[KOR]**

This skill acts on **one** world: the runtime installation reached by `muiogo-ai`,
unless the user explicitly asked for their own live one (`muiogo-live`). Never use
bare `muiogo`, and never fall back to it. Every command prints a `world:` line to
stderr — read it, and name that world when you report a result or a number. Worlds
hold different OG checkouts and different model registries, so the same country
model can exist in both at different commits. Locate the checkout you mean with
`muiogo-ai status` rather than assuming a path. Full rules:
`../WORLD_DISCIPLINE.md`.

## The mental model

1. **The packaged `og<xxx>_default_parameters.json` is the source of truth.** `Calibration(p,
   update_from_api=False)` fetches nothing. But an example may call `update_from_api=True` whenever
   online (OG-PHL's does), refreshing a curated few values over the JSON. Read your example before
   trusting that a hand-set value survives a run. **[family]**
2. **Anything you do not set stays American.** The defaults that bite hardest: `delta_annual` 0.05,
   `beta_annual` 0.96, `mean_income_data` in US dollars (it scales `factor`, so taxes and pensions
   run at US income levels), `pension_system` US Social Security, `alpha_db` 0.0, `tax_func_type`
   `DEP`, `cit_rate` 0.21, `p_wealth` 0.0, `zeta_D` 0.4, `debt_ratio_ss` 2.0, the `initial_guess_*`
   set. Count what your `Calibration` actually delivers. **[net-new: JPN]**
3. **Lead the dashboard with fiscal data.** Collections by instrument, debt, its foreign share and
   the effective rate on debt are published precisely, map one-to-one onto model ratios, and
   self-check through the budget identity. `K_f/K` is first-tier too: published, and a lever on
   `K/Y`; settle gross vs net `K_f` first. Production and earnings moments are the second tier.
   **[emerging: IDN, ETH; fiscal-first: ZAF; K_f/K: JPN]**
4. **Calibrate effective, not statutory, quantities:** rate = actual collections ÷ the model-wide
   base, for every instrument. **[family]**
5. **Single-industry first;** multi-industry is an overlay built afterwards
   (og-multi-industry-calibration). **[family]**
6. **Find every lever before tuning.** Write the model's own closed form for each target moment and
   list every parameter in it; a lever that runs out of road is the wrong lever, not a structural
   gap ([method.md](references/method.md)). **[net-new: JPN]**

## Running the model

Follow the model owner's run rules ([og-run-rules.md](references/og-run-rules.md)): OG-Core's
official installer, the shipped example unchanged, everything parallel, Anderson with `nu` ≤ 0.2,
validation runs offline, preflight first, and launch only on the user's go. uv, not conda;
`AGENTS.md` is the setup source of truth; never commit a `uv.lock` change from calibration work.
Detail: [solving-tuning.md](references/solving-tuning.md).

## End-to-end sequence for a new country

Copy this into the work log and tick it off.

```
- [ ] -1. Check for existing work: open PRs and branches that touch this block, and the current
          solve's gaps with their direction. Existing work changes the job to review or finish.
- [ ] 0a. Plan two dashboards: the near-term fiscal PATH (debt, primary balance, revenue, public
          investment vs actuals and the country's program) and the steady state.
- [ ] 0.  Step zero: moment x lever table from OG-Core's equations (references/method.md).
- [ ] 1.  Bootstrap from the closest sibling, then de-sibling it (references/bootstrap.md).
- [ ] 2.  Environment from the official installer; note the resolved ogcore; run og-run-preflight.
- [ ] 3.  Demographics: country_id as a named constant + regression test; data window to the last
          usable year; cache the arrays; check g_n_ss against the UN projection's growth.
- [ ] 4.  Earnings: Gini on the same welfare concept as the US reference; solve the tilt; add the
          NTA age shape if available.
- [ ] 5.  Macro: start_year (latest observed year), debt (measured initial, anchored SS), zeta_D,
          zeta_K tuned to the IIP K_f/K level, world rate (open vs distressed), g_y per hour and
          consistent with the debt anchor, remittances/aid if material, r_gov shift to the
          treasury's effective real rate (and r_gov_floor if real rates are negative), centered
          debt-elastic premium, initial_Kg_ratio if gamma_g > 0, initial wealth, alpha_T cash only.
          K/Y target and delta on PRIVATE capital: PWT less public capital, CFC less government's.
- [ ] 6.  Capital share: 1 - labour share, Gollin-adjusted if agrarian/informal; take gamma out of
          the live-API path.
- [ ] 7.  Taxes: every rate effective = collections / the model's base, by instrument, from the
          OECD Revenue Statistics country note (never statutory): GS progressive PIT;
          effective VAT/CIT/payroll/bequest; non-tax revenue on nearest-margin instruments;
          informality rung. Close the budget identity:
          alpha_G + alpha_T + alpha_I + pensions/Y + UBI/Y = revenue/Y - pb*.
- [ ] 8.  Pensions in local currency (alpha_db if DB); chi_n borrowed-and-documented or re-tilted.
- [ ] 9.  beta against private K/Y, only after sourced parameters settle.
- [ ] 10. Validate: SS dashboard, revenue by instrument, value-pinning test, AND a baseline TPI
          with the fiscal path panel.
- [ ] 11. Ship a warm-start seed from the FIRST converged solve, before tuning; regenerate it after
          large moves.
- [ ] 12. Optional multi-industry: og-multi-industry-calibration.
- [ ] 13. Final standalone solve of the packaged JSON, no overrides.
- [ ] 14. Wrap up: format; tests; CHANGELOG (before -> after + citation); docs with
          glue-from-JSON; goodness-of-fit table. Ask before push; ask before PR.
```

Loop-backs. Do not move forward past a failed check:

- **After any tax change, re-tune `zeta_K` (step 5).** Taxes move domestic saving, which moves
  `K_f/K` at a fixed `zeta_K`.
- **After any sourced-parameter change, redo the tax dials (step 7), then `beta` (step 9).** Every
  tuned dial was fitted against the old base.
- **If the standalone solve of the packaged JSON fails (step 13),** go back to the overrides you
  just folded in.
- **If the baseline TPI resource-constraint error is not small and monotone (step 10),** triage it
  by period before any tuning (og-solver-diagnosis).
- **If the steady state is right but the transition runs away,** check the fiscal identity before
  any solver setting.

## House rules

- **uv only, run as a user would;** keep `uv.lock` and `.python-version` out of the PR diff.
- **Non-destructive:** the single-industry default keeps working; multi-industry ships as its own
  builder-regenerated file.
- **Document every calibrated value with a source;** no undocumented placeholders and no
  `NEEDS TUNING` at release. Pin the decision in a test.
- **Approval gates:** calibrate, edit and commit locally freely. Solves beyond a quick SS check,
  pushes, PRs and anything fleet-scale wait for the user. Ask before push and before the PR, never
  in the same step. Never merge.
- **PR style:** narrative, plain language, the why first, detail in the docs
  ([calibration-pr.md](references/calibration-pr.md)).

## Reference files

Read the one for the block you are working on. Each is self-contained.

| File | Read when |
|---|---|
| [method.md](references/method.md) | Before tuning: the moment × lever table, finding every lever, dashboard completeness, why the transition is validated |
| [bootstrap.md](references/bootstrap.md) | Copying a sibling repo for a new country: what the copy carries and what replaces each inherited value |
| [macro-open-economy.md](references/macro-open-economy.md) | `start_year`, debt, `zeta_D`, `zeta_K`, world rate, `g_y`, `r_gov`, remittances/aid, debt premium, `initial_Kg_ratio`, initial wealth, `delta`, `beta`, `alpha_T`, `gamma`; gross vs net `K_f` |
| [fiscal-consistency.md](references/fiscal-consistency.md) | Spending shares; the budget identity; debt runs away on the transition; the fiscal path panel and `alpha_G` glide |
| [taxes-informality.md](references/taxes-informality.md) | Any tax rate; the PIT form (GS/HSV); payroll and bequest checks; informality; non-tax revenue |
| [households-demographics.md](references/households-demographics.md) | The `e` matrix and Gini; demographics, data window, the population breaks; pensions; `chi_n` |
| [validation-dashboard.md](references/validation-dashboard.md) | Building or scoring the dashboard; sourcing data anchors; reading pickles; tests that pin values |
| [solving-tuning.md](references/solving-tuning.md) | Environment; the evidence behind the run rules; the tuning loop and its order |
| [calibration-pr.md](references/calibration-pr.md) | Writing the calibration PR |
| [og-run-rules.md](references/og-run-rules.md) | Before any solve |

Related skills: `og-run` (launching solves), `og-run-preflight` (the go/no-go check),
`og-solver-diagnosis` (a solve that fails, stalls or looks wrong), `calibration-provenance` (tracing
a parameter to its source), `muiogo-explain` (explaining the calibration to a person),
`og-multi-industry-calibration`, `og-clews-linked-run`. If one is not
available, do the job directly and say which skill would have covered it.

## The traps that cost the most

Each shipped in a real repo; the reference has the detail.

- **Budget does not balance at the debt target:** the transition runs away while the steady state
  looks fine. [fiscal-consistency.md](references/fiscal-consistency.md)
- **Statutory rates in effective slots:** `tau_bq`, payroll on top of the ETR function, a flat PIT.
  [taxes-informality.md](references/taxes-informality.md)
- **Placeholder `zeta_K`** (0.9 drives domestic capital negative; 0.10 left gaps open for fourteen
  rounds): tune it to the IIP `K_f/K`. [macro-open-economy.md](references/macro-open-economy.md)
- **`r_gov` from the cross-country intercept:** re-anchor to the treasury's effective real rate.
  [macro-open-economy.md](references/macro-open-economy.md)
- **Wrong `initial_debt_ratio`:** invisible to the steady state, obvious in period one of the path
  panel. [fiscal-consistency.md](references/fiscal-consistency.md)
- **A consumption spike in the first years:** rule out unsolved start cohorts (og-solver-diagnosis,
  class M) before blaming the initial-wealth condition.
  [macro-open-economy.md](references/macro-open-economy.md)
- **Short demographic window:** sets the long-run growth rate silently.
  [households-demographics.md](references/households-demographics.md)
- **Live-API clobber** of a hand-triangulated value: take curated parameters off the live path.
  [macro-open-economy.md](references/macro-open-economy.md)
- **Cold-start steady state:** suspect the seed first; warm-start (og-solver-diagnosis).
- **Remittances or aid left off** where they matter: a spurious trade surplus and a fiscal squeeze.
  [macro-open-economy.md](references/macro-open-economy.md)
