"""`muiogo` CLI — thin commands over MuiogoClient/MuiogoServer.

Orientation (works with no server running):
  muiogo status                                      where everything is installed

Models and scenarios:
  muiogo cases                                       list cases
  muiogo scenarios --case NAME                       scenarios and runs in a case
  muiogo new-run --case NAME --run RUN --activate A,B create a scenario combination
  muiogo copy   --case NAME                          copy a case to NAME_copy
  muiogo delete --case NAME --yes                    delete a case

Running:
  muiogo serve  [--root PATH] [--port 5002]          headless server (foreground)
  muiogo run    --case NAME --run RUN [--solver cbc] generate + solve one run
  muiogo batch  --case NAME --runs A,B,C             generate + solve several (CBC)
  muiogo log    --case NAME --run RUN                solver log for a run

Results and analysis:
  muiogo results --case NAME --run RUN [--out DIR]   list result CSVs, or download all
  muiogo variables --case NAME --run RUN             what result variables exist
  muiogo compare --case NAME --runs A,B --var V      compare runs; --chart out.png
  muiogo verify --case NAME --run RUN [--resolve]     prove a result still reproduces

All commands take --url (default http://127.0.0.1:5002). Paths and ports come
from the installed workspace manifest when not given.
"""
import argparse
import sys

from muiogo_client import workspace
from muiogo_client.client import DEFAULT_URL, MuiogoClient, MuiogoError
from muiogo_client.server import MuiogoServer, ServerError


def _answers(url):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{url}/getSession", timeout=1.5):
            return True
    except (urllib.error.URLError, OSError):
        return False


def _resolve_url(args):
    """Explicit --url wins, then whichever candidate actually answers.

    The manifest records the port used at install time, but a server may be
    running on the default instead — so probe rather than assume, and fall back
    to the manifest's URL so an error message names the intended target.
    """
    if getattr(args, "url", None):
        return args.url
    try:
        preferred = workspace.summary()["muiogo_url"] or DEFAULT_URL
    except workspace.WorkspaceError:
        preferred = DEFAULT_URL
    for candidate in (preferred, DEFAULT_URL):
        if _answers(candidate):
            return candidate
    return preferred


def _client(args):
    return MuiogoClient(base_url=_resolve_url(args))


def _data_storage(args):
    """DataStorage path: explicit flag, else from the workspace manifest."""
    if getattr(args, "data_storage", None):
        return args.data_storage
    info = workspace.summary()
    if not info["data_storage"]:
        raise MuiogoError("manifest has no MUIOGO path; pass --data-storage")
    return info["data_storage"]


def cmd_status(args):
    """Orientation: what is installed and where. Needs no running server."""
    try:
        info = workspace.summary()
    except workspace.WorkspaceError as exc:
        print(f"No workspace found.\n{exc}", file=sys.stderr)
        return 1

    print(f"manifest      {info['manifest']}")
    print(f"workspace     {info['workspace']}")
    print(f"installed     {info['generated']}")
    print(f"MUIOGO        {info['muiogo_path']}  (ref {info['muiogo_ref']})")
    print(f"model data    {info['data_storage']}")
    print(f"server URL    {info['muiogo_url']}")

    client = MuiogoClient(base_url=info["muiogo_url"] or DEFAULT_URL, timeout=5)
    try:
        cases = client.list_cases()
        print(f"server        running — {len(cases)} case(s)")
    except Exception:
        cases = None
        print("server        not running   (start it: muiogo serve)")

    if cases is None:
        from pathlib import Path

        ds = info["data_storage"]
        if ds and Path(ds).is_dir():
            cases = sorted(
                p.name for p in Path(ds).iterdir()
                if (p / "genData.json").is_file()
            )
    for case in cases or []:
        print(f"  case        {case}")

    for model in info["og_models"]:
        print(f"  OG model    {model.get('key')}  {model.get('path')}")
    if info["link_path"]:
        print(f"  link        {info['link_path']}")
    solvers = info["solvers"]
    if solvers:
        print(f"  solvers     glpk={bool(solvers.get('glpsol'))} cbc={bool(solvers.get('cbc'))}")
    return 0


def cmd_cases(args):
    for case in _client(args).list_cases():
        print(case)
    return 0


def cmd_scenarios(args):
    client = _client(args)
    ds = _data_storage(args)
    scenarios = client.list_scenarios(args.case, ds)
    runs = client.list_runs(args.case, ds)

    print(f"scenarios in {args.case}:")
    for s in scenarios:
        base = "  (base)" if s.get("ScenarioId") == "SC_0" else ""
        print(f"  {s.get('Scenario'):<18} {s.get('Desc','')}{base}")
    print(f"\nruns in {args.case}:")
    for r in runs:
        active = [s["Scenario"] for s in r.get("Scenarios", []) if s.get("Active")]
        print(f"  {r.get('Case'):<18} activates: {', '.join(active)}")
    return 0


def cmd_new_run(args):
    client = _client(args)
    ds = _data_storage(args)
    activate = [a.strip() for a in (args.activate or "").split(",") if a.strip()]
    body = client.create_run(args.case, args.run, activate, ds, desc=args.desc or "")
    print(body.get("message", body))
    if body.get("status_code") == "exist":
        return 1
    print(f"Now solve it:  muiogo run --case \"{args.case}\" --run {args.run}")
    return 0


def cmd_copy(args):
    print(_client(args).copy_case(args.case).get("message", ""))
    return 0


def cmd_delete(args):
    if not args.yes:
        print("Refusing to delete without --yes.", file=sys.stderr)
        return 2
    print(_client(args).delete_case(args.case).get("message", ""))
    return 0


def _record_provenance(args, run, solver):
    """Write RUN.json beside a freshly solved run. Never fails the run itself."""
    from muiogo_client import provenance
    try:
        ds = _data_storage(args)
        muiogo_path = None
        try:
            muiogo_path = workspace.summary()["muiogo_path"]
        except workspace.WorkspaceError:
            pass
        path, record = provenance.write(ds, args.case, run,
                                        solver=solver, muiogo_path=muiogo_path)
        return record
    except Exception as exc:                                     # noqa: BLE001
        print(f"warning: could not record provenance: {exc}", file=sys.stderr)
        return None


def cmd_run(args):
    body = _client(args).run(args.case, args.run, solver=args.solver)
    print(f"status: {body.get('status_code')}")
    timer = (body.get("timer") or "").strip()
    if timer:
        print(timer)
    if not args.no_provenance:
        record = _record_provenance(args, args.run, args.solver)
        if record:
            print(f"provenance: objective={record['objective']} "
                  f"input={(record['input_sha256'] or '?')[:12]} "
                  f"results={(record['results_sha256'] or '?')[:12]}")
    return 0


def cmd_verify(args):
    """Re-check a recorded run against what is on disk, and optionally re-solve."""
    from muiogo_client import provenance
    ds = _data_storage(args)
    stored = provenance.read(ds, args.case, args.run)
    if stored is None:
        print(f"No provenance record for {args.case!r}/{args.run!r}. "
              f"Solve it once with `muiogo run` to create one.", file=sys.stderr)
        return 1

    print(f"recorded {stored['recorded']}  objective={stored['objective']}  "
          f"scenarios={stored.get('scenarios_active')}")

    if args.resolve:
        print("re-solving to confirm reproducibility…")
        _client(args).run(args.case, args.run, solver=stored.get("solver", "cbc"))
        fresh = provenance.build(ds, args.case, args.run, solver=stored.get("solver", "cbc"))
        same_obj = fresh["objective"] == stored["objective"]
        same_res = fresh["results_sha256"] == stored["results_sha256"]
        print(f"  objective: {stored['objective']} -> {fresh['objective']}  "
              f"{'MATCH' if same_obj else 'DIFFERENT'}")
        print(f"  results hash: {'MATCH' if same_res else 'DIFFERENT'}")
        if same_obj and same_res:
            print("\nReproduced exactly.")
            return 0
        print("\nDid NOT reproduce — the case's input data has changed since this "
              "run was recorded.", file=sys.stderr)
        return 1

    ok, diffs = provenance.compare_to_current(ds, args.case, args.run)
    if ok:
        print("On-disk results still match the record.")
        return 0
    for d in diffs:
        print(f"  MISMATCH {d}")
    print("\nThe stored results no longer match the record. Re-solve, or use "
          "--resolve to check reproducibility.", file=sys.stderr)
    return 1


def cmd_batch(args):
    runs = [r.strip() for r in args.runs.split(",") if r.strip()]
    if not runs:
        print("No runs given.", file=sys.stderr)
        return 2
    client = _client(args)
    body = client.batch_run(args.case, runs)
    if body.get("time"):
        print(f"elapsed: {float(body['time']):.1f}s")

    # /batchRun reports no per-run status_code, so verify each run on disk
    # rather than trusting the batch response.
    from muiogo_client import analysis
    ds = _data_storage(args)
    failed = []
    for run in runs:
        n = len(analysis.available_variables(ds, args.case, run))
        if n:
            rec = None if args.no_provenance else _record_provenance(args, run, "cbc")
            obj = f"  objective={rec['objective']}" if rec else ""
            print(f"  {run}: {n} result variables{obj}")
        else:
            print(f"  {run}: NO RESULTS — did not solve")
            failed.append(run)
    if failed:
        print(f"\n{len(failed)} of {len(runs)} run(s) produced nothing: "
              f"{', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def cmd_log(args):
    client = _client(args)
    if args.server:
        print(client.server_log() or "(server log empty)")
        return 0
    text = client.run_output(args.case, args.run, _data_storage(args))
    if not text:
        print(f"No solver output for run {args.run!r} — it has never produced results.\n"
              f"For the server's own log: muiogo log --server --case X --run Y")
        return 1
    print(text)
    return 0


def cmd_results(args):
    client = _client(args)
    if args.out:
        paths = client.download_all_csvs(args.case, args.run, args.out)
        print(f"Downloaded {len(paths)} CSVs to {args.out}")
    else:
        for name in client.list_result_csvs(args.case, args.run):
            print(name)
    return 0


def cmd_variables(args):
    """What result variables a solved run offers."""
    from muiogo_client import analysis
    names = analysis.available_variables(_data_storage(args), args.case, args.run)
    if not names:
        print(f"no results for run {args.run!r} — not solved, or the solve failed")
        return 1
    for n in names:
        print(n)
    return 0


def cmd_compare(args):
    """Compare runs on one result variable; optionally chart it."""
    from muiogo_client import analysis
    filters = {}
    for spec in args.filter or []:
        if "=" not in spec:
            print(f"bad --filter {spec!r}; want COLUMN=VALUE", file=sys.stderr)
            return 2
        col, val = spec.split("=", 1)
        filters[col] = val
    runs = [r.strip() for r in args.runs.split(",") if r.strip()]

    try:
        df, warnings = analysis.compare(
            _data_storage(args), args.case, runs, args.var, filters, args.by)
    except analysis.AnalysisError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    from muiogo_client import provenance
    for w in provenance.consistency(_data_storage(args), args.case, runs):
        print(f"warning: {w}", file=sys.stderr)

    if args.by and len(df.columns) > args.top:
        keep = df.sum().sort_values(ascending=False).head(args.top).index
        print(f"(showing the {len(keep)} largest of {len(df.columns)} groups)")
        df = df[keep]

    label = args.var + (
        "  [" + ", ".join(f"{k}={v}" for k, v in filters.items()) + "]" if filters else "")
    print(label)
    print(analysis.summarise(df).to_string(
        float_format=lambda v: f"{v:,.2f}" if abs(v) < 1000 else f"{v:,.0f}"))

    if args.table:
        print()
        print(df.to_string(float_format=lambda v: f"{v:,.2f}" if abs(v) < 1000 else f"{v:,.0f}"))

    if args.chart:
        title = f"{args.var} — {args.case}"
        if filters:
            title += " (" + ", ".join(f"{k}={v}" for k, v in filters.items()) + ")"
        out = analysis.chart(df, args.chart, title=title, ylabel=args.var, kind=args.kind)
        print(f"\nchart: {out}")
    return 0


def cmd_serve(args):
    root = args.root
    if not root:
        info = workspace.summary()
        root = info["muiogo_path"]
        if not root:
            raise ServerError("no MUIOGO path in the manifest; pass --root")
    port = args.port
    if port is None:
        try:
            port = workspace.summary()["muiogo_port"] or 5002
        except workspace.WorkspaceError:
            port = 5002
    server = MuiogoServer(root, port=port)
    server.start()
    print(f"MUIOGO serving headless on {server.url} — Ctrl+C to stop.")
    try:
        server.process.wait()
    except KeyboardInterrupt:
        server.stop()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="muiogo", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=None,
                        help=f"server URL (default: the workspace's, else {DEFAULT_URL})")
    parser.add_argument("--data-storage", help="MUIOGO DataStorage path (default: from manifest)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="where everything is installed (no server needed)"
                   ).set_defaults(func=cmd_status)
    sub.add_parser("cases", help="list cases").set_defaults(func=cmd_cases)

    p = sub.add_parser("scenarios", help="scenarios and runs defined in a case")
    p.add_argument("--case", required=True)
    p.set_defaults(func=cmd_scenarios)

    p = sub.add_parser("new-run", help="create a run activating chosen scenarios")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--activate", default="", help="scenario names, comma-separated (base is automatic)")
    p.add_argument("--desc", default="")
    p.set_defaults(func=cmd_new_run)

    p = sub.add_parser("copy", help="copy a case to <name>_copy")
    p.add_argument("--case", required=True)
    p.set_defaults(func=cmd_copy)

    p = sub.add_parser("delete", help="delete a case")
    p.add_argument("--case", required=True)
    p.add_argument("--yes", action="store_true", help="confirm deletion")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("run", help="generate data file and solve one run")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--solver", default="cbc", choices=["cbc", "glpk"],
                   help="cbc is the working default; glpk is broken upstream")
    p.add_argument("--no-provenance", action="store_true",
                   help="skip writing RUN.json beside the results")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("verify", help="check a run against its provenance record")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--resolve", action="store_true",
                   help="re-solve and confirm the objective and results reproduce")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("batch", help="generate and solve several runs (CBC)")
    p.add_argument("--case", required=True)
    p.add_argument("--runs", required=True, help="run names, comma-separated")
    p.add_argument("--no-provenance", action="store_true")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("log", help="a run's solver output (or --server for the app log)")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--server", action="store_true",
                   help="show MUIOGO's process-wide log instead of this run's output")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("results", help="list result CSVs, or download all with --out")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--out", help="directory to download all CSVs into")
    p.set_defaults(func=cmd_results)

    p = sub.add_parser("variables", help="result variables available for a solved run")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.set_defaults(func=cmd_variables)

    p = sub.add_parser("compare", help="compare runs on a result variable, and chart it")
    p.add_argument("--case", required=True)
    p.add_argument("--runs", required=True, help="run names, comma-separated")
    p.add_argument("--var", required=True, help="result variable (see: muiogo variables)")
    p.add_argument("--filter", action="append", metavar="COL=VALUE",
                   help="restrict rows, e.g. e=CO2 (repeatable)")
    p.add_argument("--by", help="break down by a dimension (t, f, e, ...) instead of totalling")
    p.add_argument("--top", type=int, default=8, help="with --by, keep the N largest groups")
    p.add_argument("--table", action="store_true", help="also print the full year-by-year table")
    p.add_argument("--chart", help="write a chart image here (.png)")
    p.add_argument("--kind", default="line", choices=["line", "area", "bar"])
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("serve", help="run a headless MUIOGO server in the foreground")
    p.add_argument("--root", help="MUIOGO checkout (default: from manifest)")
    p.add_argument("--port", type=int, default=None, help="default: the workspace's port, else 5002")
    p.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (MuiogoError, ServerError, workspace.WorkspaceError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
