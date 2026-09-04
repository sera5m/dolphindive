from __future__ import annotations

import argparse
import sys

from dolphindive import __version__
from dolphindive.engine.rank import RankMode
from dolphindive.pipeline import search


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dive", description="DolphinDive search")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd")

    s = sub.add_parser("search", help="print ranked hits")
    s.add_argument("query", nargs="+")
    s.add_argument("--mode", choices=[m.value for m in RankMode], default="smart")
    s.add_argument("-n", type=int, default=20)

    sub.add_parser("overlay", help="open the Alt+F style search box")
    sub.add_parser("selftest", help="run engine sanity checks")

    args = parser.parse_args(argv)
    if args.cmd == "search":
        raw = " ".join(args.query)
        hits = search(raw, mode=RankMode(args.mode), limit=args.n)
        if not hits:
            print("no hits")
            return 1
        for hit in hits:
            kind = "dir " if hit.is_dir else "file"
            print(f"{hit.final:7.1f}  {kind}  {hit.path}")
        return 0
    if args.cmd == "overlay":
        from dolphindive.app.overlay import run_overlay

        return run_overlay()
    if args.cmd == "selftest":
        return _selftest()
    parser.print_help()
    return 0


def _selftest() -> int:
    from dolphindive.engine.fuzzy import fuzzy_score
    from dolphindive.engine.query import parse_query

    assert fuzzy_score("vs", "VisualStudio") is not None
    assert fuzzy_score("zzz", "abc") is None
    q = parse_query("budget doc: ext:pdf")
    assert q.kind == "doc"
    assert ".pdf" in q.extensions
    assert q.text == "budget"
    print("selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
