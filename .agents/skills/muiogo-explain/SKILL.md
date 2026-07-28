---
name: muiogo-explain
description: Explain a CLEWs or OG-Core model to a person — what this particular model contains, how it is calibrated, the underlying theory, and the intuition for why it behaves as it does. Use when asked what a model does or covers, what its assumptions are, why a result came out a certain way, what a parameter or variable means, to explain the theory or the maths, or to brief someone new. This skill DESCRIBES; use assess-clews-calibration to grade calibration quality, og-country-calibration to change it, and calibration-provenance to trace one number to its source.
---

# Explain a model, its calibration, and the intuition

The failure mode here is fluent generic economics: an explanation that sounds
authoritative and is not about the user's actual model. Everything you say should
be traceable either to a file in their installation or to the upstream
documentation. **Read the model, then explain it.** Do not describe a model from
memory of what such models usually contain.

## Which world

You are explaining a model in ONE world, and the same case name can exist in both.
Use the pinned launcher — `muiogo-ai` for the installed runtime, `muiogo-live` only
when the user explicitly asked for their own checkouts — never bare `muiogo`. Every
command prints a `world:` line to stderr: read it, and name that world when you
describe a model or quote anything from it. Full rules in
`../WORLD_DISCIPLINE.md`.

Orient first with `muiogo-ai status` (see `muiogo-workspace`) — you need to know
which family the question is about and where that model lives.

## Explaining a CLEWs model

### What this model contains

Read the case's `genData.json`. Get to it by asking for the case, never by typing a
relative path:

```bash
CASE="$(muiogo-ai case-path --case '<case>')"   # absolute, inside this world
```

`$CASE/genData.json` is the model's own description:

| Key | What it tells you |
|---|---|
| `osy-tech` | every technology, with names and ids |
| `osy-comm` | commodities — fuels, crops, water, land, services |
| `osy-emis` | the emissions accounted for |
| `osy-ts`, `osy-se`, `osy-dt`, `osy-dtb` | timeslices, seasons, day types, brackets |
| `osy-years` | the horizon |
| `osy-scenarios` | the policy overlays defined |
| `osy-constraints` | user-defined constraints such as a renewable target |
| `osy-currency` | the money units results are in |

`muiogo-ai scenarios --case "<case>"` gives the scenarios and runs in readable form.
For structure quality — orphaned ids, stranded commodities, missing sectors —
`clews-model-review` runs a real checker; use it rather than eyeballing.

Describe scope honestly: a "CLEWs" model may cover energy, land, and water, or
only some of those. Name the sectors present, and say which are absent.

### The theory, grounded

A CLEWs model in MUIOGO is an **OSeMOSYS** linear program: it chooses capacity
and operation to meet demand at least total discounted cost. The model file
shipped with the install is the authority — `WebAPP/SOLVERs/model.v.5.4.txt`, a
location inside the MUIOGO root that `muiogo-ai status` reports rather than a path
to type from your working directory — readable, about 66 named constraints. Its
objective minimises, over regions, technologies and years, the sum of capital cost
on new capacity, fixed cost on total capacity, and variable cost on activity, each
discounted, net of salvage value.

The constraint families you can point to by name in that file:

- **Energy balance** (`EBa*`, `EBb*`) — production must meet use in every
  timeslice and year. This is what makes it a systems model rather than a
  spreadsheet.
- **Capacity adequacy** (`CAa*`) — activity cannot exceed what installed capacity
  can deliver, given availability factors.
- **Capital and operating cost accounting** (`CC1`, `OC1`, `OC2`) and
  **salvage value** (`SV*`).
- **Emissions** (`E1`, `E2`) — emissions follow activity through emission
  activity ratios, and a penalty prices them.
- **Limits** (`NCC*`, `TAC1`, `LU1`, `LU2`) — build and activity bounds.
- **User-defined constraints** (`UDC`) — the policy targets a case adds.

For the formulation beyond what the file shows, cite the OSeMOSYS documentation
rather than reconstructing it from memory.

### The intuition

Say *why* the optimiser did what it did, in cost terms:

- It builds a technology when the discounted cost of building and running it
  beats the alternative for the service demanded — not because it is "clean".
- A carbon price works by adding cost to emitting activity, so substitution
  happens where the price exceeds the cost gap. That is why response is often
  step-like: nothing changes until a threshold, then a technology flips.
- Diminishing returns are expected: cheap abatement goes first. On the demo case,
  quadrupling the carbon price after doubling it adds only a few further points.
- A binding constraint, not a cost, may be driving the answer. If a target is
  already met by the cost-optimal solution, imposing it changes nothing — a real
  and reportable finding.

## Explaining an OG-Core model

### What this model is

OG-Core is an **overlapping-generations** general-equilibrium model: many age
cohorts alive at once, each saving and working over a lifetime, with firms and a
government. It answers fiscal and demographic questions — debt, deficits, tax
reform, pensions, ageing — not energy-system questions.

Two solution objects, and confusing them misleads people:

- a **steady state**, the long-run equilibrium the economy settles to;
- a **transition path** (TPI), the year-by-year adjustment from today to it.

A run produces a baseline and a reform (`OUTPUT_BASELINE/`, `OUTPUT_REFORM/`);
results are differences between them, not levels to read on their own.

### How this model is calibrated

Establish the calibration from the installation, not from assumption. The country
repo holds its calibration code and data, and its own README and docs describe
what was fitted. `og-country-calibration` is the authoritative playbook for what
each parameter block means and which values are defensible;
`calibration-provenance` traces an individual number to its source. Note whether
the model is **single-industry or multi-industry** — the link reports this, and it
determines whether energy channels can act at all.

When you explain a calibration, distinguish three things: what was **fitted to
country data**, what was **borrowed** from another country or the literature, and
what remains at a **default**. Users routinely assume everything is
country-specific; usually it is not. If you cannot tell which is which, say so.

### The intuition

- Effects arrive through **prices and the lifecycle**: a tax change alters
  after-tax returns to work and saving, households re-optimise across their
  remaining lifetime, and aggregate capital and labour move slowly.
- Long-run and short-run answers can have opposite signs. Always say which you
  are reporting.
- Debt-financed policy shifts burdens across generations; that redistribution is
  the point of using an OLG model rather than a representative-agent one.
- Cite the OG-Core documentation for the equations. Do not present remembered
  formulations as this model's.

## Explaining the linkage

Say which direction the signal travels and through which channel — the link names
them explicitly (`ogclews-link channels`, with `clews->og` and `og->clews`
labels). "The energy system affects the economy" is not an explanation; "the
CLEWS electricity price enters OG as a cost-push across industries" is. Different
channels give different answers to the same policy by design, so naming the
channel is part of naming the result.

## How to pitch it

Ask yourself who is listening, and adjust once:

- **A policymaker** wants what changes, by how much, by when, and how confident
  you are. Lead with the number and the direction; keep the mechanism to a
  sentence.
- **An analyst** wants the mechanism, the parameters that drive it, and where the
  model is weak.
- **A newcomer** wants the shape of the thing: what it decides, what it takes as
  given, what it cannot say.

Always volunteer the limits. An uncalibrated model, demo data, a single-industry
calibration, a missing sector, or a skipped channel changes what a result is worth
— and the user cannot see those from the numbers.

## Handing off

- Grading calibration quality rather than describing it →
  `assess-clews-calibration`.
- Structural defects → `clews-model-review`.
- Numbers, comparisons, charts → `muiogo-analyze`.
- Changing the calibration → `og-country-calibration`.
- Where a specific number came from → `calibration-provenance`.

## Approval gates

Explaining is read-only: read the model's files and the upstream docs, and say
what you found. Never state a parameter value, a calibration choice, or a result
you have not read. If a claim needs a solve to support it, propose the run rather
than asserting the answer.
