"""`muiogo` CLI entry point. Skeleton: subcommands land with Phase 0."""

import sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    print("muiogo-client 0.0.1 — skeleton. Subcommands land with Phase 0 (see docs/SCOPE.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
