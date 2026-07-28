#!/usr/bin/env python3
"""Create a new scenario in a MUIOGO case, through MUIOGO's HTTP API.

Why a script: a scenario is not one edit. Every scenario carries a COMPLETE
slice of every parameter (with zeros where it does not override), so a new
scenario must be seeded from an existing one or the generated model input will
be wrong. This does that mechanically, then you set the few values that define
the policy.

    python3 new_scenario.py --case "My Case" --name High_CO2_tax \
        --copy-from CO2_tax --data-storage <path> [--url http://127.0.0.1:5002]

It registers the scenario, copies a complete parameter slice from --copy-from
(default: the base scenario), and prints what to edit next. Use --set to apply a
multiplier to one parameter in one file at the same time:

    --set RYE.json:EP:EMI_6ku9o:x4        multiply that row's yearly values by 4
    --set RYC.json:SAD:COM_abc:x1.15      15% higher demand

Verified against MUIOGO 3db8b816.
"""
import argparse
import glob
import json
import os
import sys
import urllib.error
import urllib.request

BASE_SCENARIO = "SC_0"


def post(url, payload, timeout=120, cookie=None):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if cookie:
        req.add_header("Cookie", cookie)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
        set_cookie = resp.headers.get("Set-Cookie")
        try:
            return json.loads(raw), set_cookie
        except ValueError:
            return raw, set_cookie


def next_scenario_id(existing):
    n = 1
    used = {s.get("ScenarioId") for s in existing}
    while f"SC_new{n}" in used:
        n += 1
    return f"SC_new{n}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", required=True)
    ap.add_argument("--name", required=True, help="scenario name, e.g. High_CO2_tax")
    ap.add_argument("--desc", default="")
    ap.add_argument("--copy-from", default=None,
                    help="scenario name to seed the parameter slice from (default: base)")
    ap.add_argument("--data-storage", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:5002")
    ap.add_argument("--set", action="append", default=[],
                    metavar="FILE:PARAM:ROWID:xFACTOR",
                    help="multiply a row's yearly values, e.g. RYE.json:EP:EMI_6ku9o:x4")
    args = ap.parse_args()

    case_dir = os.path.join(args.data_storage, args.case)
    gen_path = os.path.join(case_dir, "genData.json")
    if not os.path.isfile(gen_path):
        sys.exit(f"no case at {case_dir}")

    # The session cookie carries the active case; every write endpoint needs it.
    _, cookie = post(f"{args.url}/setSession", {"case": args.case})
    cookie = (cookie or "").split(";")[0] or None

    with open(gen_path, encoding="utf-8") as f:
        gen = json.load(f)
    scenarios = gen.get("osy-scenarios", [])
    if not scenarios:
        sys.exit("case defines no scenarios")

    by_name = {s.get("Scenario"): s for s in scenarios}
    if args.name in by_name:
        sys.exit(f"scenario {args.name!r} already exists")

    src_id = BASE_SCENARIO
    if args.copy_from:
        src = by_name.get(args.copy_from)
        if not src:
            sys.exit(f"no scenario named {args.copy_from!r}; have: {', '.join(by_name)}")
        src_id = src["ScenarioId"]

    new_id = next_scenario_id(scenarios)
    gen["osy-scenarios"].append({
        "ScenarioId": new_id,
        "Scenario": args.name,
        "Desc": args.desc or f"copied from {args.copy_from or 'base'}",
        "Active": True,
    })
    resp, _ = post(f"{args.url}/saveCase", {"data": gen}, cookie=cookie)
    status = resp.get("status_code") if isinstance(resp, dict) else resp
    if status not in ("success", "edited"):
        sys.exit(f"saveCase refused: {resp}")
    print(f"registered scenario {args.name} ({new_id}), seeded from {src_id}")

    # Parse --set directives into {(file, param, rowid): factor}
    factors = {}
    for spec in args.set:
        try:
            fname, param, rowid, mult = spec.split(":")
            factors[(fname, param, rowid)] = float(mult.lstrip("xX"))
        except ValueError:
            sys.exit(f"bad --set {spec!r}; want FILE:PARAM:ROWID:xFACTOR")

    written, applied = 0, 0
    for path in sorted(glob.glob(os.path.join(case_dir, "R*.json"))):
        fname = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            continue
        for param, by_scen in data.items():
            if not isinstance(by_scen, dict) or src_id not in by_scen:
                continue
            rows = json.loads(json.dumps(by_scen[src_id]))       # deep copy
            for row in rows:
                rowid = next((row[k] for k in row if k.endswith("Id")), None)
                factor = factors.get((fname, param, rowid))
                if factor is None:
                    continue
                for key, val in list(row.items()):
                    if key.isdigit() and isinstance(val, (int, float)):
                        row[key] = round(val * factor, 6)
                applied += 1
            by_scen[new_id] = rows
            resp, _ = post(f"{args.url}/updateData",
                           {"param": param, "data": by_scen, "dataJson": fname},
                           cookie=cookie)
            if not (isinstance(resp, dict) and resp.get("status_code") == "success"):
                sys.exit(f"updateData refused for {fname}:{param}: {resp}")
            written += 1

    print(f"wrote {written} parameter slices; applied {applied} --set change(s)")
    if not factors:
        print("\nNothing changed yet -- this scenario is a copy. Edit the parameters that\n"
              "define your policy (see the skill's parameter table), then:")
    else:
        print("\nNext:")
    print(f'  muiogo new-run --case "{args.case}" --run <RUNNAME> --activate {args.name}')
    print(f'  muiogo run --case "{args.case}" --run <RUNNAME>')


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as exc:
        sys.exit(f"cannot reach MUIOGO at the given --url ({exc}). Is `muiogo serve` running?")
