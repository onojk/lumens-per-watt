"""Unattributed-instruction guard (IDEAS I-045; report only, never fitness): for an op-class comparison, per cell the
uncharged Ir (uncharged:card + uncharged:harness) and the unattributed Ir (unattributed + decl) per number, from a
callgrind derivation's per-run breakdown (opclass/derivB/weights.json format: per_run.<run>.ir, total_ir; numbers from
opclass/inputs.json, or given as run:numbers). A rise from the base cell to the changed cell is FLAGGED when it exceeds
both tolerances:
  ABS_TOL  1,000 Ir per number   (the floor: smaller rises are below interest at 54-96 bits, 1-45 M Ir per number)
  REL_TOL  2% of the base cell's own value of that quantity
This is the op-class version of an uncharged op: work that runs but that no charged class pays for.
  python3 opclass/guard.py <breakdown.json> <base_run>:<changed_run> [...]       (from the repo root)"""
import json, sys
ABS_TOL, REL_TOL = 1000.0, 0.02

def numbers():
    try:
        return {r["run"]: r["numbers"] for r in json.load(open("opclass/inputs.json"))["runs"]}
    except OSError:
        return {}

def cell(pr, run, n):
    r = pr[run]
    ir = r["ir"]
    unc = ir.get("uncharged:card", 0) + ir.get("uncharged:harness", 0)
    una = ir.get("unattributed", 0) + ir.get("decl", 0)
    return {"total": r["total_ir"] / n, "uncharged": unc / n, "unattributed": una / n}

def compare(pr, base, new, nums):
    a, b = cell(pr, base, nums[base]), cell(pr, new, nums[new])
    flags = []
    print(f"{new} against {base} (per number; flag when the rise > {ABS_TOL:,.0f} Ir and > {100 * REL_TOL:g}% of the base's value):")
    for q in ("uncharged", "unattributed"):
        d = b[q] - a[q]
        rel = d / a[q] if a[q] else float("inf") if d > 0 else 0.0
        f = d > ABS_TOL and rel > REL_TOL
        print(f"    {q:12s} {a[q]:14,.0f} -> {b[q]:14,.0f}  change {d:+12,.0f} ({100 * rel:+.2f}%)  share of total "
              f"{100 * a[q] / a['total']:.3f}% -> {100 * b[q] / b['total']:.3f}%{'  FLAG' if f else ''}")
        if f:
            flags.append((new, base, q, d))
    print(f"    total        {a['total']:14,.0f} -> {b['total']:14,.0f}  ratio {b['total'] / a['total']:.4f}")
    return flags

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    pr = json.load(open(sys.argv[1]))["per_run"]
    nums = numbers()
    allf = []
    for pair in sys.argv[2:]:
        base, new = pair.split(":")
        allf += compare(pr, base, new, nums)
    print("flags:", allf if allf else "none")
