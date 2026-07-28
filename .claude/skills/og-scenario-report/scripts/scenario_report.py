#!/usr/bin/env python3
"""Build the standard OG-Core baseline-vs-reform comparison tables + narrative skeleton.

Reads OUTPUT_BASELINE / OUTPUT_REFORM pickles directly (numpy + stdlib only — run it
with the country repo's own venv python) and writes a markdown report containing:

  * the house macro table (pct change: Y, C, K, L, r, w — yearly window + SS)
  * a fiscal table (pct change: D, TR, total_tax_revenue)
  * steady-state revenue by instrument as % of GDP, baseline vs reform
  * key ratios (D/Y, revenue/Y) at the SS
  * a narrative skeleton with the computed numbers filled in and TODO slots
    for interpretation

Complements (does not replace) ogcore's own post-processing:
`ogcore.output_tables.macro_table` (CSV) and `ogcore.output_plots.plot_all` (~30 PNGs).

Usage:
  <repo-venv-python> scenario_report.py --base <...>/OUTPUT_BASELINE \
      --reform <...>/OUTPUT_REFORM --out report.md [--num-years 10] [--start-year 2025]
"""

from __future__ import annotations

import argparse
import os
import pickle
import sys

import numpy as np

MACRO_VARS = ["Y", "C", "K", "L", "r", "w"]
FISCAL_VARS = ["D", "TR", "total_tax_revenue"]
REV_INSTRUMENTS = [
    ("iit_revenue", "PIT"),
    ("business_tax_revenue", "CIT"),
    ("cons_tax_revenue", "Consumption/VAT"),
    ("payroll_tax_revenue", "Payroll"),
    ("bequest_tax_revenue", "Bequest"),
    ("wealth_tax_revenue", "Wealth"),
]


class _RestrictedUnpickler(pickle.Unpickler):
    """Unpickling is code execution; OG output pickles need only numpy + builtin
    containers, so refuse everything else rather than trust the file."""

    def find_class(self, module, name):
        if module.split(".")[0] == "numpy":
            return super().find_class(module, name)
        raise pickle.UnpicklingError(
            f"refusing to unpickle {module}.{name}: OUTPUT pickles should contain only "
            "numpy objects. If this dir is trusted and genuinely needs more, extend "
            "_RestrictedUnpickler deliberately."
        )


def load(d: str, which: str):
    path = os.path.join(d, which)
    with open(path, "rb") as f:
        return _RestrictedUnpickler(f).load()


def get(d: dict, key: str):
    """Fetch key tolerating the 'Yss'/'rss' naming variant across ogcore versions."""
    if key in d:
        return d[key]
    for alt in (key + "ss", key + "_ss"):
        if alt in d:
            return d[alt]
    return None


def agg(x):
    """First aggregate dimension of a TPI array (T[,M...] -> T)."""
    x = np.asarray(x, dtype=float)
    return x if x.ndim == 1 else x.reshape(x.shape[0], -1).sum(axis=1)


def scalar(x):
    x = np.asarray(x, dtype=float)
    return float(x.sum())  # multi-industry SS values sum across industries


def pct(r, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        return 100.0 * (r - b) / np.abs(b)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--reform", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--num-years", type=int, default=10)
    ap.add_argument("--start-year", type=int, default=None)
    a = ap.parse_args()

    btpi = load(a.base, "TPI/TPI_vars.pkl")
    rtpi = load(a.reform, "TPI/TPI_vars.pkl")
    bss = load(a.base, "SS/SS_vars.pkl")
    rss = load(a.reform, "SS/SS_vars.pkl")

    start_year = a.start_year
    if start_year is None:
        # model_params.pkl is an ogcore Specifications object, which the restricted
        # unpickler (rightly) refuses -- pass --start-year for calendar labels.
        start_year = 0  # t-indexing fallback
    years = [start_year + t for t in range(a.num_years)]
    ylab = [str(y) if start_year else f"t={y}" for y in years]

    missing: list[str] = []
    L: list[str] = []
    L.append("# Scenario comparison: reform vs baseline\n")
    L.append(f"- Baseline: `{os.path.abspath(a.base)}`")
    L.append(f"- Reform:   `{os.path.abspath(a.reform)}`")
    L.append(f"- Window: {ylab[0]}–{ylab[-1]} (first {a.num_years} years) + steady state\n")
    L.append("> TODO: one paragraph on what the reform *is* (the changed parameters and "
             "their real-world policy meaning). Read it from the reform run script — "
             "the pickles don't carry it.\n")

    # --- Macro table -------------------------------------------------------
    L.append("## Macro aggregates (% change from baseline)\n")
    header = "| Variable | " + " | ".join(ylab) + " | 10-yr window | SS |"
    L.append(header)
    L.append("|" + "---|" * (len(ylab) + 3))
    impact: dict[str, tuple[float, float]] = {}
    for v in MACRO_VARS + FISCAL_VARS:
        b, r = get(btpi, v), get(rtpi, v)
        bs, rs = get(bss, v), get(rss, v)
        if b is None or r is None or bs is None or rs is None:
            missing.append(v)
            continue
        b, r = agg(b)[: a.num_years], agg(r)[: a.num_years]
        yearly = pct(r, b)
        window = 100.0 * (r.sum() - b.sum()) / abs(b.sum())
        ss_chg = pct(scalar(rs), scalar(bs))
        impact[v] = (float(yearly[0]), float(ss_chg))
        row = " | ".join(f"{x:.2f}" for x in yearly)
        L.append(f"| {v} | {row} | {window:.2f} | {ss_chg:.2f} |")
        if v == MACRO_VARS[-1]:
            L.append("")
            L.append("## Fiscal aggregates (% change from baseline)\n")
            L.append(header)
            L.append("|" + "---|" * (len(ylab) + 3))
    L.append("")

    # --- Revenue by instrument at the SS ----------------------------------
    L.append("## Steady-state revenue by instrument (% of GDP)\n")
    L.append("| Instrument | Baseline | Reform | Δ (pp) |")
    L.append("|---|---|---|---|")
    yb, yr = scalar(get(bss, "Y")), scalar(get(rss, "Y"))
    for key, label in REV_INSTRUMENTS:
        b, r = get(bss, key), get(rss, key)
        if b is None or r is None:
            missing.append(key)
            continue
        pb, pr = 100 * scalar(b) / yb, 100 * scalar(r) / yr
        L.append(f"| {label} | {pb:.2f} | {pr:.2f} | {pr - pb:+.2f} |")
    for key, label in [("D", "Debt / GDP"), ("total_tax_revenue", "Total revenue / GDP")]:
        b, r = get(bss, key), get(rss, key)
        if b is None or r is None:
            continue
        pb, pr = 100 * scalar(b) / yb, 100 * scalar(r) / yr
        L.append(f"| {label} | {pb:.2f} | {pr:.2f} | {pr - pb:+.2f} |")
    L.append("")

    # --- Narrative skeleton ------------------------------------------------
    L.append("## Narrative skeleton (numbers filled; interpretation is yours)\n")

    def word(x, up="raises", down="lowers"):
        return up if x > 0 else down

    if "Y" in impact:
        y0, yss = impact["Y"]
        L.append(
            f"The reform {word(y0)} GDP by {abs(y0):.2f}% in the first year and "
            f"{word(yss)} it by {abs(yss):.2f}% in the long run. "
            "TODO: mechanism — which margin (labor supply, capital accumulation, "
            "foreign capital inflow) drives this, and does the sign flip over time?"
        )
    if "K" in impact and "L" in impact:
        L.append(
            f"Long-run capital moves {impact['K'][1]:+.2f}% and labor "
            f"{impact['L'][1]:+.2f}%. TODO: relate to the factor-price changes "
            f"(r {impact.get('r', (0, 0))[1]:+.2f}%, w {impact.get('w', (0, 0))[1]:+.2f}% at SS)."
        )
    if "D" in impact:
        L.append(
            f"Government debt ends {impact['D'][1]:+.2f}% from baseline at the SS. "
            "TODO: is the fiscal adjustment doing the work (closure rule), or the tax base? "
            "State which closure (`budget_balance`, `baseline_spending`, tG1/tG2) was active."
        )
    L.append(
        "\nTODO: distributional paragraph — read the by-j ability_bar PNGs from plot_all "
        "(PctChange_Cons/Labor/Income) and describe who gains and who loses."
    )
    L.append("\nTODO: caveats — model-unit levels are not currency; ratios and % changes "
             "are the comparable objects. Note any binding guards seen in the solve log "
             "(e.g. `K_d has negative elements`).")

    if missing:
        L.append(f"\n*Variables not found in these pickles (skipped): {sorted(set(missing))}*")

    with open(a.out, "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"wrote {a.out}" + (f" (missing keys: {sorted(set(missing))})" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
