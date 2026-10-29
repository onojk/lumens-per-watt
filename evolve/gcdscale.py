"""The size-scaled gcd price (the user's ruling, Oct 29, option (a); NOTES "Ruling: gcd pricing for the arrangement
family"): op-class v1 with the gcd weight replaced by (measured instructions per gcd at N's size) / 0.909 (QS's
instructions per op-class unit, the twilight meter-health check). Instructions: bench/gcdbench/gcd_ir.json (dd2db46),
mean of 3 seeds, linear in bits between the measured sizes, constant outside. Curves: "small" (the other argument fits
one 64-bit word) and "uniform" (a difference mod N: rho, p-1, ECM). Reported beside op-class v1; never changes it."""
import json, os

IR_PER_UNIT = 0.909
_D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bench", "gcdbench", "gcd_ir.json")))
CURVE = {m: sorted((int(k.split()[0]), sum(v) / len(v)) for k, v in _D.items() if k.split()[1] == m) for m in ("small", "uniform")}
V1 = {k: v["weight"] for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "opclass",
                                                             "opclass_v1.json")))["classes"].items() if v["weight"]}

def gcd_instructions(bits, curve="uniform"):
    pts = CURVE[curve]
    if bits <= pts[0][0]:
        return pts[0][1]
    for (b0, y0), (b1, y1) in zip(pts, pts[1:]):
        if bits <= b1:
            return y0 + (y1 - y0) * (bits - b0) / (b1 - b0)
    return pts[-1][1]

def gcd_units(bits, curve="uniform"):
    return gcd_instructions(bits, curve) / IR_PER_UNIT

def cost(ty, bits, curve="uniform"):
    """op-class v1 cost of a per-type count dict with the gcd weight size-scaled (None if a type has no v1 weight)."""
    if any(n and t not in V1 and t != "gcd" for t, n in ty.items()):
        return None
    return sum((gcd_units(bits, curve) if t == "gcd" else V1[t]) * n for t, n in ty.items() if n)
