# Bootstrapping from a sibling repo

## De-siblinging a bootstrap copy

A copied repo carries its sibling's country in the code as well as the JSON, and the code copies
fail silently. **[KOR]** Before any solve:

- **Search, do not trust the rename.** After renaming the package, grep code, tests and docs for the
  sibling's ISO code, UN code, country name and demonym, and currency symbol; list every hit in the
  work log and resolve each. Known carriers: the UN `country_id`; ISO codes defaulted inside
  live-download functions (`macro_params`); survey-derived constants (a Gini default in
  `get_e_interp`, remittance-allocation shares in the demographics tool); currency labels; SAM/IO
  data; sibling-specific tests, which either fail or, worse, pass on the sibling's numbers.
- **Make the new example offline.** If the sibling's example calls `Calibration(p,
  update_from_api=True)` when online, the copy downloads data with the sibling's codes and writes it
  over the new country's values. The new country's example reads the packaged JSON only.
- **Audit every inherited JSON value** (mental model 1b): diff the JSON against the sibling's and
  list each key as sourced, tuned to a named moment, or defaulted with a reason. Include solver
  settings (`TPI_outer_method`, `nu`, `initial_guess_*`): a sibling can predate a run rule (KOR
  inherited `nu` 0.4 with Anderson from PHL). The seeds are the sibling's solution, not neutral
  defaults: ogcore guesses GDP as `initial_guess_TR_SS / alpha_T`, so a sibling's TR seed against
  the new `alpha_T` put KOR's GDP guess 4.6x too high and stalled the solve. What replaces each
  inherited value:

  | Inherited | Replace with |
  |---|---|
  | `start_year` | the latest year with observed data |
  | demographic window | the archive's last year minus one; check `g_n_ss` against the UN growth |
  | every tax rate, `tau_bq` included | effective = collections / the model's base, by instrument |
  | `alpha_G`, `alpha_T`, `alpha_I`, pensions | the budget identity at `debt_ratio_ss` (step 7) |
  | `K/Y` target, `delta` | private capital: PWT less public capital; CFC less government's |
  | `zeta_K`, world rate, `r_gov_shift` | IIP gross `K_f/K`; a sourced world rate; the treasury's effective rate |
  | `nu`, `TPI_outer_method`, `initial_guess_*` | the run rules; seeds from the new country's own first solve |
  | the example reform | a change that is real for the new country; check it moves a parameter from its baseline value |

- **Replace the sibling's example reform** with one that means something for the new country (for
  example, a reform the new country has enacted, not the sibling's). A reform that sets a rate to
  the new country's current value changes nothing. **[KOR, THA]** (history: KOR, THA)
