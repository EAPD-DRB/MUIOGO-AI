"""Read, compare, and chart MUIOGO CLEWs results.

Result CSVs are tidy long format — the last column is the value, the leading
columns are OSeMOSYS dimensions (r region, t technology, f fuel, e emission,
y year, l timeslice, m mode, s storage). Everything here works off those files
directly; nothing re-runs a model.
"""
from pathlib import Path

import pandas as pd

DIMENSION_NAMES = {
    "r": "region", "t": "technology", "f": "fuel", "e": "emission",
    "y": "year", "l": "timeslice", "m": "mode", "s": "storage",
}


class AnalysisError(RuntimeError):
    pass


def results_dir(data_storage, case, run):
    return Path(data_storage) / case / "res" / run / "csv"


def available_variables(data_storage, case, run):
    """Result variable names present for a run (file names without .csv)."""
    d = results_dir(data_storage, case, run)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.csv"))


def load(data_storage, case, run, var):
    """One run's results for one variable, as a DataFrame."""
    path = results_dir(data_storage, case, run) / f"{var}.csv"
    if not path.is_file():
        have = available_variables(data_storage, case, run)
        if not have:
            raise AnalysisError(
                f"run {run!r} of {case!r} has no results — it was never solved, "
                f"or the solve failed"
            )
        raise AnalysisError(
            f"{var!r} is not a result of run {run!r}. Available: {', '.join(have[:12])}"
            + (" …" if len(have) > 12 else "")
        )
    df = pd.read_csv(path)
    if df.empty:
        raise AnalysisError(f"{path} has no rows")
    return df


def compare(data_storage, case, runs, var, filters=None, by=None):
    """Year-indexed comparison across runs.

    filters: {column: value} to restrict rows (e.g. {"e": "CO2"}).
    by:      a dimension to break down by instead of totalling.
    Returns (DataFrame indexed by year, list of warnings).
    """
    filters = filters or {}
    frames, warnings = {}, []

    for run in runs:
        try:
            df = load(data_storage, case, run, var)
        except AnalysisError as exc:
            warnings.append(str(exc))
            continue

        missing = [c for c in list(filters) + ([by] if by else []) if c not in df.columns]
        if missing:
            raise AnalysisError(
                f"{var}.csv has no column(s) {', '.join(missing)}; "
                f"columns are {', '.join(df.columns)}"
            )

        for col, val in filters.items():
            df = df[df[col].astype(str) == str(val)]
        if df.empty:
            warnings.append(f"no rows left for run {run} after filtering")
            continue

        value_col = df.columns[-1]
        if by:
            grouped = df.groupby(["y", by])[value_col].sum().unstack(by)
            for group in grouped.columns:
                frames[f"{run}:{group}"] = grouped[group]
        else:
            frames[run] = df.groupby("y")[value_col].sum()

    if not frames:
        raise AnalysisError(
            "nothing to compare. " + (" ".join(warnings) if warnings else "")
        )
    out = pd.DataFrame(frames).sort_index()
    out.index.name = "year"
    return out, warnings


def summarise(df):
    """Totals and change-versus-first-column, as a DataFrame for printing."""
    totals = df.sum()
    first = totals.iloc[0] if len(totals) else 0
    return pd.DataFrame({
        "first_year": df.iloc[0],
        "last_year": df.iloc[-1],
        "total": totals,
        "vs_first_series_%": [
            float("nan") if first == 0 else (t / first - 1) * 100 for t in totals
        ],
    })


def chart(df, path, title="", ylabel="", kind="line"):
    """Write a chart of a comparison frame. Returns the path written."""
    import matplotlib
    matplotlib.use("Agg")            # headless: no display needed
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9.5, 5.0), dpi=140)
    if kind == "area":
        ax.stackplot(df.index, *[df[c] for c in df.columns], labels=list(df.columns), alpha=.85)
    elif kind == "bar":
        df.plot(kind="bar", ax=ax, width=.8)
    else:
        for col in df.columns:
            ax.plot(df.index, df[col], marker="o", markersize=3.2, linewidth=2.0, label=col)

    ax.set_title(title or "MUIOGO results", fontsize=12, loc="left", pad=12)
    ax.set_xlabel("year")
    ax.set_ylabel(ylabel or "")
    ax.grid(True, axis="y", alpha=.28, linewidth=.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if len(df.columns) > 1 or kind == "area":
        ax.legend(frameon=False, fontsize=9, loc="best")
    ax.margins(x=.02)
    fig.tight_layout()

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out
