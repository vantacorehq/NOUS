import argparse
import json
import os
import sys
from . import __version__, gitio
from .claims import judge
from .gate import evaluate
from .heatmap import render
from .ledger import Ledger
from .report import analyze, LIT, DRIFT, DARK


def _bar(p, n=30):
    k = round(p * n)
    return "█" * k + "░" * (n - k)


def cmd_status(a, root, led):
    rep = analyze(root, led)
    if a.json:
        print(json.dumps({"coverage": rep.coverage, "lit": len(rep.by_state(LIT)),
                          "drift": len(rep.by_state(DRIFT)), "dark": len(rep.by_state(DARK)),
                          "single_point_of_understanding": len(rep.single_point)}))
        return 0
    print(f"\n  NOUS  comprehension  {_bar(rep.coverage)}  {rep.coverage*100:5.1f}%\n")
    print(f"  lit   {len(rep.by_state(LIT)):>5}   (a human vouched, code unchanged since)")
    print(f"  drift {len(rep.by_state(DRIFT)):>5}   (was understood — then the code changed)")
    print(f"  dark  {len(rep.by_state(DARK)):>5}   (nobody has ever vouched)")
    print(f"  bus=1 {len(rep.single_point):>5}   (understood by exactly one person)\n")
    return 0


def cmd_dark(a, root, led):
    rep = analyze(root, led)
    rows = rep.by_state(DARK) + rep.by_state(DRIFT)
    rows.sort(key=lambda r: -r.unit.loc)
    for r in rows[: a.top]:
        print(f"  {'~' if r.state == DRIFT else '·'} {r.unit.loc:>4} loc  {r.unit.key}")
    return 0


def cmd_vouch(a, root, led):
    hits = [r for r in analyze(root, led).rows if r.unit.key == a.target]
    if len(hits) != 1:
        print("target must be exactly path::name — see `nous dark`", file=sys.stderr)
        return 2
    u = hits[0].unit
    claim = a.message
    if not claim:
        print(f"\n--- {u.key} (L{u.start}-{u.end}) ---\n{u.text}\n---")
        print("Explain what it does, why it is shaped this way, and what would break it:")
        claim = sys.stdin.readline().strip()
    ok, why = judge(u.text, claim, led.used_claims())
    if not ok:
        print(f"✗ not accepted: {why}", file=sys.stderr)
        return 1
    e = led.append(u, gitio.identity(root), claim)
    print(f"✓ lit {u.key}  [{e['hash'][:12]}]")
    return 0


def cmd_gate(a, root, led):
    crit = []
    for c in a.critical or []:
        g, _, p = c.rpartition("=")
        crit.append((g, float(p)))
    fails = evaluate(root, analyze(root, led), a.min, crit, a.since)
    ok, msg = led.verify()
    if not ok:
        fails.insert(0, "ledger integrity: " + msg)
    if fails:
        print("\n  ✗ NOUS GATE: FAILED\n")
        for f in fails:
            print("  " + f)
        print()
        return 1
    print("  ✓ NOUS GATE: passed — everything that ships is understood.")
    return 0


def cmd_verify(a, root, led):
    ok, msg = led.verify()
    print(("✓ " if ok else "✗ ") + msg)
    return 0 if ok else 1


def cmd_map(a, root, led):
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(render(analyze(root, led)))
    print(f"wrote {a.out}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="nous", description="The ledger of human understanding.")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("-C", dest="root", default=".")
    s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("status"); x.add_argument("--json", action="store_true"); x.set_defaults(f=cmd_status)
    x = s.add_parser("dark"); x.add_argument("--top", type=int, default=25); x.set_defaults(f=cmd_dark)
    x = s.add_parser("vouch"); x.add_argument("target"); x.add_argument("-m", "--message"); x.set_defaults(f=cmd_vouch)
    x = s.add_parser("gate"); x.add_argument("--min", type=float, default=0)
    x.add_argument("--critical", action="append", metavar="GLOB=PCT")
    x.add_argument("--since", metavar="BASE_REF"); x.set_defaults(f=cmd_gate)
    x = s.add_parser("verify"); x.set_defaults(f=cmd_verify)
    x = s.add_parser("map"); x.add_argument("-o", "--out", default="nous-map.svg"); x.set_defaults(f=cmd_map)
    a = p.parse_args(argv)
    root = os.path.abspath(a.root)
    return a.f(a, root, Ledger(root))


if __name__ == "__main__":
    sys.exit(main())
