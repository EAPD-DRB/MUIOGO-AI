# MUIOGO on-disk results contract (observed)

What lands where when a case run solves. Observed against MUIOGO @ `3db8b816`
(2026-07-27), CLEWs Demo case, CBC solver. Analysis skills should read these
files (directly or via the download endpoints), never scrape the GUI.

## Layout

```
WebAPP/DataStorage/
├── Parameters.json, Variables.json,        # app-level definitions
│   Duals.json, Indicators.json
└── <case>/                                 # e.g. "CLEWs Demo"
    ├── genData.json                        # case definition (osy-casename, ...)
    ├── R.json, RY*.json, RT*.json, ...     # parameter data by dimension group
    ├── view/                               # saved GUI views
    └── res/
        └── <run>/                          # e.g. REF, CO2TAX (one per scenario run)
            ├── data.txt                    # generated MathProg data (generateDataFile)
            ├── data_processed.txt          # preprocessor output (CBC path)
            ├── lp.lp                       # LP file built by glpsol --check (CBC path)
            ├── results.txt                 # raw solver solution
            └── csv/                        # parsed results, one CSV per variable (32 for demo)
```

## Result CSVs

- One file per OSeMOSYS output variable: `NewCapacity.csv`,
  `AnnualTechnologyEmission.csv`, `Demand.csv`, `RateOfActivity.csv`,
  `TotalCapacityAnnual.csv`, ... (32 for the demo case).
- Long/tidy format. Header = dimension letters + variable name; one row per
  index combination. Examples observed:
  - `NewCapacity.csv`: `r,t,y,NewCapacity` → `RE1,MINCOA,2020,473.04`
  - `AnnualTechnologyEmission.csv`: `r,t,e,y,AnnualTechnologyEmission` →
    `RE1,MINCOA,CO2,2020,24583.04`
- Dimension letters follow OSeMOSYS sets: `r` region, `t` technology, `f` fuel,
  `e` emission, `y` year, `l` timeslice, `m` mode, `s` storage.

## Lifecycle facts that matter to tooling

- `POST /run` deletes the run's previous results before solving; a missing
  `results.txt`/`csv/` after a run means the solve failed even if HTTP was 200.
- `data.txt` regeneration is deterministic: regenerated file was byte-identical
  to the shipped demo one.
- Timestamps on `res/<run>/` files are the reliable "when did this last solve"
  signal.
- Case names may contain spaces ("CLEWs Demo") — always quote/encode paths.
