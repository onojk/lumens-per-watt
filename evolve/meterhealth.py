"""Meter-health check (IDEAS.md I-042; report only, never feeds fitness): where does wall-clock time sit without a price?
  (a) absolute: for each timed cell, per region and sub-region, wall against priced cost (ruint) converted to µs at the
      cell's own mean rate (cell wall / cell ruint). Flagged when the excess exceeds K x the sub-region's own noise.
  (b) differential: for a pair of cells (a gene toggle, cell against base), per region and sub-region, the change in
      wall against the change in priced cost converted at the base region's own rate (µs per ruint of that region in
      the base; the base cell's mean rate where the region has no price in the base). Flagged when the excess exceeds
      both an absolute and a relative tolerance (and, with replicates, when its 95% interval excludes zero).
Regions: lampcore --phasetime's regions (wall replicates, flags off). Sub-regions: one breakdown pass per cell
(LAMPCORE_SIEVEBREAK sv:*, LAMPCORE_LPBREAK lp:*), sub-timers on.
  - The sieve sub-regions carry no types of their own (the sieve region charges once, at its end, in sv:tail); their
    price is their op units at ruint's prices: sv:zero and sv:free2 sieve_scan, sv:prime and sv:power sieve_update
    and word (the same price); sv:tail keeps the rest of the region's price.
  - Noise: a region's sd over replicates. A sub-region timed once gets its parent region's sd scaled by its share of
    the parent's time in the same pass (stated in the output; an estimate, not a measurement).
Usage:
  python3 meterhealth.py report <run.json> [<run.json> ...]   (shiftrun_A/B/C.json, i032shift.json; no timing)
  python3 meterhealth.py run                                  (information-only timed pass -> meterhealth_run.json)
"""
import json, math, statistics, sys
ARGV = sys.argv[1:]   # before the imports: partition and sizescale clear sys.argv
from lctest import PR

K, FLOOR = 3.0, 1.0           # (a) flag when excess > K x noise and > 1 us per number (the floor drops trivial flags)
ABS_TOL, REL_TOL = 10.0, 0.05  # (b) flag when excess > 10 µs per number and > 5% of the base region's wall
T7 = 2.3646
RU = PR["ruint"]
UNIT_PRICE = {"sv:zero": RU["sieve_scan"], "sv:free2": RU["sieve_scan"], "sv:prime": RU["sieve_update"], "sv:power": RU["sieve_update"]}
PARENT = {"sv": "sieve", "lp": "lp_ledger"}

def cell_view(timing, brk):
    """{name: {"wall", "sd", "ruint", "reps" (or None), "sub"}} for one cell; the regions from the wall replicates, the
    sub-regions from the breakdown pass(es)."""
    regs = {}
    for k, v in timing.items():
        if k in ("mhz", "wall") or not isinstance(v, dict) or "mean" not in v:
            continue
        regs[k] = {"wall": v["mean"], "sd": v["sd"], "ruint": v.get("ruint", 0.0), "reps": v.get("per_replicate"), "sub": False}
    for src in brk:
        if not src:
            continue
        own = {}
        for k, v in src.items():
            if ":" not in k:
                continue
            if k in UNIT_PRICE:
                own[k] = v.get("units", 0.0) * UNIT_PRICE[k]
            else:
                own[k] = v["priced"]
        if "sv:tail" in own:   # sv:tail carries the whole region's types: keep only what the walk sub-regions do not
            own["sv:tail"] -= sum(own[k] for k in UNIT_PRICE if k in own)
        for k, v in src.items():
            if ":" not in k:
                continue
            par = PARENT[k.split(":")[0]]
            pw = src[par]["ns"] if par in src else None
            share = max(v["ns"], 0.0) / pw if pw else 0.0
            psd = regs[par]["sd"] if par in regs else 0.0
            regs[k] = {"wall": v["ns"] / 1e3, "sd": psd * share, "ruint": own[k], "reps": None, "sub": True}
    return regs

def rate(timing, regs):
    tot = sum(r["ruint"] for k, r in regs.items() if not r["sub"])
    return timing["wall"]["mean"] / tot

# scan has no ops of its own: its sieve_scan ops are charged in the sieve region (the width charge, which also pays
# for the array clear, sv:zero). Its row is reported but not flagged; the combined rows carry the comparison.
COMBINED = (("sieve+scan", ("sieve", "scan")), ("sv:zero+scan", ("sv:zero", "scan")))

def absolute(name, timing, regs):
    rt = rate(timing, regs)
    rows = []
    for k, r in regs.items():
        ex = r["wall"] - r["ruint"] * rt
        noise = r["sd"]
        flag = noise > 0 and ex > K * noise and ex > FLOOR and k != "scan"
        rows.append((k, r["wall"], r["ruint"] * rt, ex, noise, flag))
    for k, parts in COMBINED:
        if all(p in regs for p in parts):
            w = sum(regs[p]["wall"] for p in parts)
            pr = sum(regs[p]["ruint"] for p in parts) * rt
            noise = math.sqrt(sum(regs[p]["sd"] ** 2 for p in parts))
            rows.append((k, w, pr, w - pr, noise, noise > 0 and w - pr > K * noise and w - pr > FLOOR))
    return rt, rows

def differential(ta, ra, tb, rb):
    rtb = rate(tb, rb)
    rows = []
    for k in rb:
        if k not in ra:
            continue
        a, b = ra[k], rb[k]
        own = b["wall"] / b["ruint"] if b["ruint"] > 0 and b["wall"] > 0 else rtb
        dw, dp = a["wall"] - b["wall"], (a["ruint"] - b["ruint"]) * own
        ex = dw - dp
        ci = None
        if a["reps"] and b["reps"] and b["ruint"] > 0:
            pr = a["ruint"] / b["ruint"]
            xs = [(x / y - pr) * b["wall"] for x, y in zip(a["reps"], b["reps"])]
            m, h = statistics.mean(xs), T7 * statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0
            ci = (m - h, m + h)
        rel = ex / b["wall"] if b["wall"] > 0 else math.inf
        flag = ex > ABS_TOL and rel > REL_TOL and (ci is None or ci[0] > 0)
        rows.append((k, dw, dp, ex, ci, rel, flag))
    return rows

def print_abs(tag, name, timing, regs):
    rt, rows = absolute(name, timing, regs)
    print(f"(a) {tag}{name}: cell rate {rt * 1e3:.2f} ns per ruint; flag when excess > {K:g} x noise and > {FLOOR:g} us (a flag means the region runs"
          " slower per ruint than the cell's mean, not necessarily an uncharged op; scan's ops are priced in sieve, see sieve+scan)")
    for k, w, p, ex, n, f in rows:
        print(f"    {k:10s} wall {w:9.1f} us  priced {p:9.1f} us  excess {ex:+9.1f}  noise {n:6.1f}{' (scaled)' if k.find(':') > 0 else ''}{'  FLAG' if f else ''}")
    return [(k, ex, n) for k, w, p, ex, n, f in rows if f]

def print_diff(tag, a, b, ta, ra, tb, rb):
    rows = differential(ta, ra, tb, rb)
    print(f"(b) {tag}{a} against {b}: flag when excess > {ABS_TOL:g} us per number and > {100 * REL_TOL:g}% of the base region's wall"
          " (and the 95% interval excludes zero, where replicates exist)")
    for k, dw, dp, ex, ci, rel, f in rows:
        c = f" [{ci[0]:+.1f}, {ci[1]:+.1f}]" if ci else ""
        r = f"{100 * rel:+.1f}%" if rel != math.inf else "new"
        print(f"    {k:10s} d-wall {dw:+9.1f}  d-priced {dp:+9.1f}  excess {ex:+9.1f}{c}  ({r}){'  FLAG' if f else ''}")
    return [(k, ex) for k, dw, dp, ex, ci, rel, f in rows if f]

def sets(d):
    """The (tag, data) per size in a run JSON (shiftrun_A/B/C.json, i032shift.json, meterhealth_run.json)."""
    if "timing" in d:
        return [("", d)]
    return [(f"{k} bits: ", v) for k, v in d.items() if isinstance(v, dict) and "timing" in v]

def report(path):
    d = json.load(open(path))
    flags = []
    print(f"=== {path}")
    for tag, s in sets(d):
        cells = [n for n in s["timing"] if " vs " not in n]
        view = {n: cell_view(s["timing"][n], [s.get("svbreak", {}).get(n), s.get("lpbreak", {}).get(n), s.get("break", {}).get(n)]) for n in cells}
        for n in cells:
            flags += [(path, tag + n, "a", k, ex) for k, ex, _ in print_abs(tag, n, s["timing"][n], view[n])]
        for pair in s["timing"]:
            if " vs " not in pair:
                continue
            a, b = pair.split(" vs ")
            if a in view and b in view:
                flags += [(path, f"{tag}{a} vs {b}", "b", k, ex) for k, ex in print_diff(tag, a, b, s["timing"][a], view[a], s["timing"][b], view[b])]
    return flags

def run():
    """Information-only timed pass: 2'a and 2'b at 72, 84 and 96; 4 replicates (flags off), then one pass per cell with
    both breakdowns on. Clock options for short cells. No sealed predictions: never a verdict."""
    import partition as P, sizescale2 as S2
    from lctest import ref, phasetime
    from timing import shuffled
    out = {}
    for bits, inner in ((72, 3), (84, 2), (96, 1)):
        g0 = dict(ref(bits), goff=1)
        cells = {"2'a": g0, "2'b": dict(g0, confirm="root")}
        nums = S2.map_nums(bits)
        res, order, states, clock = shuffled(cells, nums, reps=4, seed=3000 + bits, period=0.05, skip_launch=True, inner=inner)
        t = {}
        for n in cells:
            rec = {"mhz": clock[n]}
            walls = [sum(v["ns"] for k, v in w.items() if ":" not in k) / 1e3 for w in res[n]]
            rec["wall"] = {"mean": statistics.mean(walls), "sd": statistics.stdev(walls), "per_replicate": walls}
            for k in res[n][0]:
                if ":" in k:
                    continue
                x = [w[k]["ns"] / 1e3 for w in res[n]]
                rec[k] = {"mean": statistics.mean(x), "sd": statistics.stdev(x), "per_replicate": x,
                          "ruint": float(res[n][0][k]["priced"]), "calls": float(res[n][0][k]["calls"])}
            t[n] = rec
        t["2'b vs 2'a"] = {}
        brk = {n: {k: {kk: float(vv) for kk, vv in v.items()} for k, v in phasetime(g, nums, True, True).items()} for n, g in cells.items()}
        out[str(bits)] = {"timing": t, "break": brk, "order": order, "states": states, "clock": clock}
        print(f"{bits} bits timed: " + ", ".join(f"{n} {t[n]['wall']['mean']:,.1f} us (core 2 median {clock[n].get('median')}, "
                                                   f"{clock[n]['per_pass']:.1f} samples per pass)" for n in cells), flush=True)
    json.dump(out, open("meterhealth_run.json", "w"), indent=1)
    return out

if __name__ == "__main__":
    if ARGV and ARGV[0] == "report":
        allf = []
        for p in ARGV[1:]:
            allf += report(p)
        print("=== flags")
        for f in allf:
            print(f"  {f[0]} | {f[1]} | ({f[2]}) {f[3]}: excess {f[4]:+.1f} us per number")
    elif ARGV and ARGV[0] == "run":
        run()
        allf = report("meterhealth_run.json")
        print("=== flags (information only; no sealed predictions)")
        for f in allf:
            print(f"  {f[1]} | ({f[2]}) {f[3]}: excess {f[4]:+.1f} us per number")
    else:
        sys.exit(__doc__)
