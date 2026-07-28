---
name: og-clews-linked-run
description: Run coupled OG-CLEWS analyses through ogclews-link — connect a country's CLEWs energy scenarios to its OG-Core macroeconomic model and report the economy-wide results. Use when asked about the economic or macroeconomic effects of an energy, climate, or CLEWs policy; to link, couple, or connect the two models; to run a named linkage experiment or channel (energy price, carbon, health, investment, demand); or when a question spans both the energy system and the economy — for example what an electricity price rise or a carbon price does to GDP, welfare, or revenue.
---

# Run coupled OG-CLEWS analyses

The link is a separate tool with its own environment. It is deliberately
ogcore-free: it never imports the macro model, it **subprocesses the OG model's
own interpreter**. So three environments are in play and must stay separate —
MUIOGO's, each OG country model's, and the link's.

Orient first (`muiogo status`, see `muiogo-workspace`). It reports whether a link
and OG models are installed; without both, a coupled run is impossible and you
should say so rather than improvise.

## Check the prerequisites before anything else

This is where coupled runs actually fail, so check first:

```bash
cd <link path>
.venv/bin/ogclews-link models list
```

**Always `cd` into the link's directory first.** The registry is
`./og_model_registry.json`, resolved relative to the working directory (or
`$OGCLEWS_MODEL_REGISTRY`), so running from anywhere else reports "no OG models
registered" even when one is registered — verified.

You need a registered OG model whose calibration is **multi-industry**. Register
one with:

```bash
.venv/bin/ogclews-link models register --path <path to OG-XXX>
```

Read what it prints — that output is the answer, and it varies by checkout:

```
electricity isolated as its own industry -- couplable on energy
[x] og-phl  ogphl  0.1.0  calib=ogphl_multisector_default_parameters.json  couplable=1
```

`couplable=1` means the energy channels can act. `couplable=0` with

```
single-industry calibration -- no electricity industry; energy channels skip
```

means they would silently do nothing.

**Check before concluding anything.** A *freshly installed* country model is
single-industry, so a brand-new install will report `couplable=0`. But a checkout
someone has been working in may already be on a multi-industry calibration branch
and report `couplable=1` — that is common, because multi-industry work is exactly
what people do on these repos. Never assume from the fact of installation; run
`models register` (or `models list`) and read the flag.

Also read the qualifiers in that output, not just the flag. A model can be
couplable and still approximate — for example a route-A good that is only partly
electricity is reported as DILUTED, meaning the demand-side wedge is a proxy. Pass
that caveat on when you report results.

If it really is `couplable=0`, say so plainly rather than running anyway:

> The installed OG-PHL is a single-industry calibration, so the energy channels
> would silently skip. A coupled energy-price run needs the multi-industry
> calibration, which is a multi-hour solve. Shall I set that up?

Building it is `examples/run_og_<xxx>_multi_industry.py` — see `og-run`.

## What you can run

```bash
.venv/bin/ogclews-link list          # the named experiments
.venv/bin/ogclews-link channels      # the transmission channels and their direction
```

Experiments compose channels into a question. The ones that ship:

| Experiment | The question it answers |
|---|---|
| `coupled` | the full soft-link: CLEWS electricity price into OG, and OG's response back |
| `energy_price` | the demand-response channel at the country's real electricity price |
| `energy_price_tfp` | a controlled price rise via the electricity industry's productivity |
| `energy_cost_push` | the same rise as an inter-industry cost-push |
| `energy_full` | cost-push plus a recycled final-good wedge, both halves together |
| `clean_incidence` | who bears the electricity price — distributional incidence, revenue recycled |
| `carbon` | a carbon price as a shared lever: OG consumption tax and CLEWS emissions penalty |
| `health` | CLEWS PM2.5 changes through a dose-response into mortality and morbidity |
| `investment` | grid and transmission capex into public investment and public capital |
| `capital_intensity` | a permanent rise in the energy industry's capital share |
| `energy_capex` | a generation buildout financed by an investment tax credit |
| `demand`, `discount_rate`, `forward` | the OG→CLEWS direction in isolation, for testing the emit path |

Channels carry a direction — `clews->og` for a signal entering the economy,
`og->clews` for one returning to the energy system. The `og->clews` emitters run
*after* the reform solve, because they need its equilibrium.

## Running one

```bash
cd <link path>
.venv/bin/ogclews-link run coupled \
    --country phl \
    --clews-base   <MUIOGO>/WebAPP/DataStorage/<case>/res/<base run>/csv \
    --clews-reform <MUIOGO>/WebAPP/DataStorage/<case>/res/<reform run>/csv \
    --out ./ogclews_runs
```

Note what those two flags take: **the path to a solved run's `csv` directory**,
not a run name. Take the `<MUIOGO>` part from `muiogo status`.

Other options: `--countries` for your own country definitions (see
`ogclews_countries.example.json`), `--workers` for the OG solve's worker
processes, `--no-figures` to skip the results deck, `--rebuild-baseline` to
discard the cached baseline.

The CLEWs side comes from a MUIOGO install. Point the link at it and name the
runs:

```bash
export OGCLEWS_MUIOGO_HOME=<MUIOGO path from muiogo status>
export OGCLEWS_CLEWS_CASE=<case>
```

Both CLEWs runs must be **solved before you start** — the link consumes their
results, it does not run them. Solve them with `muiogo-run` first and confirm
each has results.

**A coupled run is a long computation** — the OG side is a transition-path solve,
tens of minutes at least, and the first run builds a baseline that later runs
reuse. This is an approval gate: propose the command and the expected duration,
and let the user launch it. Never fire one off on your own initiative.

## Reading the outcome

The run writes into `--out`, and unless you pass `--no-figures` it builds a
figure deck. When interpreting:

- **Say which channel produced the effect.** "Higher electricity prices reduce
  household consumption" is only meaningful with the transmission named — a TFP
  channel and a cost-push channel give different answers to the same price rise,
  by design.
- **Check the channels did not skip.** A single-industry model silently skips the
  energy channels; if the macro effect is suspiciously near zero, verify
  `couplable` rather than reporting "no effect".
- **Direction matters.** A `clews->og` result is the economy responding to the
  energy system. An `og->clews` result is the energy system responding to the
  economy. Do not describe one as the other.
- The link ships `VALIDATION.md` and `STATUS.md` in its checkout — read them
  before making strong claims about what is validated.

## Handing off

- Solving the CLEWs runs the link needs → `muiogo-run`.
- Building the CLEWs scenarios first → `muiogo-scenarios`.
- Interpreting the CLEWs half → `muiogo-analyze`.
- Building or checking an OG calibration → `og-country-calibration`,
  and `og-run` to produce the multi-industry calibration.
- An OG solve that will not converge → `og-solver-diagnosis`.
- Explaining what the linkage means conceptually → `muiogo-explain`.

## Approval gates

Propose, draft, and prepare; the user decides. Registering a model and inspecting
experiments and channels is free. **Stop and ask before launching any coupled run
or any OG solve** — propose the command and the expected duration. Also stop
before pushing, PR-ing, merging, or deleting anything.
