"""`muiogo` CLI — thin commands over MuiogoClient/MuiogoServer.

muiogo cases                                       list cases
muiogo copy   --case NAME                          copy a case to NAME_copy
muiogo delete --case NAME --yes                    delete a case
muiogo run    --case NAME --run RUN [--solver cbc] generate + solve, print status
muiogo results --case NAME --run RUN [--out DIR]   list result CSVs, or download all
muiogo serve  --root PATH [--port 5002]            run a headless server in the foreground

All commands take --url (default http://127.0.0.1:5002).
"""
import argparse
import sys

from muiogo_client.client import DEFAULT_URL, MuiogoClient, MuiogoError
from muiogo_client.server import MuiogoServer, ServerError


def _client(args):
    return MuiogoClient(base_url=args.url)


def cmd_cases(args):
    for case in _client(args).list_cases():
        print(case)
    return 0


def cmd_copy(args):
    body = _client(args).copy_case(args.case)
    print(body.get("message", body))
    return 0


def cmd_delete(args):
    if not args.yes:
        print("Refusing to delete without --yes.", file=sys.stderr)
        return 2
    body = _client(args).delete_case(args.case)
    print(body.get("message", body))
    return 0


def cmd_run(args):
    client = _client(args)
    body = client.run(args.case, args.run, solver=args.solver)
    print(f"status: {body.get('status_code')}")
    timer = (body.get("timer") or "").strip()
    if timer:
        print(timer)
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


def cmd_serve(args):
    server = MuiogoServer(args.root, port=args.port)
    server.start()
    print(f"MUIOGO serving headless on {server.url} — Ctrl+C to stop.")
    try:
        server.process.wait()
    except KeyboardInterrupt:
        server.stop()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="muiogo", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=DEFAULT_URL, help=f"server URL (default {DEFAULT_URL})")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("cases", help="list cases").set_defaults(func=cmd_cases)

    p = sub.add_parser("copy", help="copy a case to <name>_copy")
    p.add_argument("--case", required=True)
    p.set_defaults(func=cmd_copy)

    p = sub.add_parser("delete", help="delete a case")
    p.add_argument("--case", required=True)
    p.add_argument("--yes", action="store_true", help="confirm deletion")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("run", help="generate data file and solve one case run")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--solver", default="cbc", choices=["cbc", "glpk"],
                   help="cbc is the working default; glpk is broken upstream (no preprocessing)")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("results", help="list result CSVs, or download all with --out")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--out", help="directory to download all CSVs into")
    p.set_defaults(func=cmd_results)

    p = sub.add_parser("serve", help="run a headless MUIOGO server in the foreground")
    p.add_argument("--root", required=True, help="path to a MUIOGO checkout with a synced .venv")
    p.add_argument("--port", type=int, default=5002)
    p.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (MuiogoError, ServerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
