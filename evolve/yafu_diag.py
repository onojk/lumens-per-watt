"""YAFU diagnosis (the user, Oct 27; information only, post hoc: Run B's sealed scores stand as "YAFU as configured").
Where YAFU's time goes on (a) 16-bit-factor numbers (96-bit band 0) and (b) balanced numbers (96- and 84-bit last
band); 20 numbers each, one batch process per variant (numbers piped on stdin, as Run B), pinned core 2, under the
same conditions as Run B (baseline_msieve.conditions; else nothing is timed). Each variant in a fresh empty scratch
directory. Reported per variant: external wall per number, and YAFU's own "Total factoring time" per number (from
factor.log, where the variant writes it). Variants:
  V0 factor(@)                       Run B's command (default plan, logs on)
  V1 factor(@) -silent               screen output off
  V2 factor(@) -silent, logs off     -logfile/-session/-jsonlog to /dev/null
  V3 siqs(@)                         SIQS directly (no td / Fermat / rho / ECM pretests)
  V4 siqs(@) -silent, logs off
  V5 factor(@) with the source tree's yafu.ini copied in (another machine's tune_info and paths)
  V6 one process per number (factor(@), 5 numbers): the per-process start-up
  V7 the same balanced number 20 times in one batch (factor(@)): per-line re-initialisation / first-call effects
  V8 smallmpqs(@)                    YAFU's other small-input QS (calc function), for comparison
  python3 yafu_diag.py -> yafu_diag.json, stdout (part 1);  python3 yafu_diag.py part2 -> yafu_diag2.json, stdout"""
import json, os, re, statistics, subprocess, sys, tempfile, time
ARGV = sys.argv[1:]                                                   # before partition's import clears sys.argv
import partition as P, sizescale2 as S2
from baseline_msieve import conditions, cool
from timing import machine_state

YAFU = os.path.expanduser("~/opt/yafu-src/yafu/yafu")
INI = os.path.expanduser("~/opt/yafu-src/yafu/yafu.ini")
LOGS_OFF = ["-logfile", "/dev/null", "-session", "/dev/null", "-jsonlog", "/dev/null"]
K = 20

def run(nums, func="factor(@)", extra=(), ini=False):
    work = tempfile.mkdtemp(prefix="yd_")
    if ini:
        open(os.path.join(work, "yafu.ini"), "w").write(open(INI).read())
    text = "".join(f"{N}\n" for N in nums)
    t0 = time.perf_counter()
    out = subprocess.run(["taskset", "-c", "2", YAFU, func, "-threads", "1", *extra], input=text, cwd=work,
                         capture_output=True, text=True, check=True).stdout
    dt = time.perf_counter() - t0
    lp = os.path.join(work, "factor.log")
    log = open(lp).read() if os.path.exists(lp) else ""
    internal = [float(x) for x in re.findall(r"Total factoring time = ([\d.]+) seconds", log)]
    found = len(re.findall(r"^P\w*\d+ = ", out, re.M)) + len(re.findall(r"prp\d+ = ", log))
    return {"wall_ms": 1e3 * dt / len(nums), "internal_ms": 1e3 * statistics.mean(internal) if internal else None,
            "internal_n": len(internal), "factor_lines": found, "log_tail": log.splitlines()[-14:]}

def part1():
    bad = conditions()
    if bad:
        print("timing skipped: " + "; ".join(bad)); sys.exit(2)
    out = {"state_start": machine_state(), "sets": {}}
    sets = {"96 band 0 (16-bit factor)": [N for N, _, _ in S2.map_nums(96)[:K]],
            "96 balanced (48-bit factor)": [N for N, _, _ in S2.map_nums(96)[-K:]],
            "84 balanced (42-bit factor)": [N for N, _, _ in S2.map_nums(84)[-K:]]}
    variants = {"V0 factor() (Run B)": dict(), "V1 factor() -silent": dict(extra=["-silent"]),
                "V2 factor() -silent, logs off": dict(extra=["-silent"] + LOGS_OFF),
                "V3 siqs()": dict(func="siqs(@)"), "V4 siqs() -silent, logs off": dict(func="siqs(@)", extra=["-silent"] + LOGS_OFF),
                "V5 factor() with the tree's yafu.ini": dict(ini=True),
                "V8 smallmpqs()": dict(func="smallmpqs(@)")}
    for name, nums in sets.items():
        rec = {}
        for v, kw in variants.items():
            cool()
            rec[v] = run(nums, **kw)
            r = rec[v]
            print(f"{name}: {v}: wall {r['wall_ms']:.2f} ms / number; YAFU's own total "
                  + (f"{r['internal_ms']:.2f} ms ({r['internal_n']} logged)" if r["internal_ms"] is not None else "not logged")
                  + f"; factor lines {r['factor_lines']}", flush=True)
        cool()
        sep = [run([N]) for N in nums[:5]]
        rec["V6 one process per number"] = {"wall_ms": statistics.mean(s["wall_ms"] for s in sep),
                                            "internal_ms": statistics.mean(s["internal_ms"] for s in sep if s["internal_ms"] is not None)}
        print(f"{name}: V6 one process per number (5): wall {rec['V6 one process per number']['wall_ms']:.2f} ms; "
              f"YAFU's own total {rec['V6 one process per number']['internal_ms']:.2f} ms", flush=True)
        if "balanced" in name:
            cool()
            r = run([nums[0]] * K)
            rec["V7 one number x20"] = r
            log = r.pop("log_tail")
            print(f"{name}: V7 the same number x{K} in one batch: wall {r['wall_ms']:.2f} ms / number; YAFU's own total "
                  f"{r['internal_ms']:.2f} ms", flush=True)
        out["sets"][name] = rec
    out["state_end"] = machine_state()
    json.dump(out, open("yafu_diag.json", "w"), indent=1)

def part2():
    """Part 2 (after part 1's profile): the per-line floor and the QS alone, on the balanced band (80 numbers) at 72 / 84 /
    96. "abs(@)": a trivial expression per batch line (the floor: YAFU's per-line reset, which re-sieves the primes to 1e7);
    "smallmpqs(@)": tinysiqs directly (init, run, free per number; prints the factors, checked); "siqs(@)" as part 1.
    The QS alone is estimated as smallmpqs - abs per number (information only)."""
    bad = conditions()
    if bad:
        print("timing skipped: " + "; ".join(bad)); sys.exit(2)
    res = {"state_start": machine_state()}
    for bits in (72, 84, 96):
        bal = S2.map_nums(bits)[-P.PER_BAND:]
        nums = [N for N, _, _ in bal]
        rec = {}
        for f in ("abs(@)", "smallmpqs(@)", "siqs(@)"):
            walls = []
            for r in range(3):
                cool()
                work = tempfile.mkdtemp(prefix="yd2_")
                t0 = time.perf_counter()
                out = subprocess.run(["taskset", "-c", "2", YAFU, f, "-threads", "1", "-silent"] if f == "abs(@)" else
                                     ["taskset", "-c", "2", YAFU, f, "-threads", "1"], input="".join(f"{N}\n" for N in nums),
                                     cwd=work, capture_output=True, text=True, check=True).stdout
                walls.append(1e3 * (time.perf_counter() - t0) / len(nums))
            ok = None
            if f == "smallmpqs(@)":
                got = set(int(x) for x in re.findall(r"^(\d+)$", out, re.M))
                ok = sum(p in got or q in got for _, p, q in bal)   # tinysiqs may return one factor; the cofactor follows
            rec[f] = {"wall_ms": walls, "median_ms": statistics.median(walls), "factors_found": ok}
            print(f"{bits} balanced ({len(nums)}): {f}: wall {statistics.median(walls):.2f} ms / number (median of 3)"
                  + (f"; a factor (p or q) printed for {ok}/{len(nums)}" if ok is not None else ""), flush=True)
        rec["QS alone (smallmpqs - abs)"] = rec["smallmpqs(@)"]["median_ms"] - rec["abs(@)"]["median_ms"]
        print(f"{bits} balanced: the QS alone, smallmpqs - abs: {rec['QS alone (smallmpqs - abs)']:.2f} ms / number", flush=True)
        res[str(bits)] = rec
    res["state_end"] = machine_state()
    json.dump(res, open("yafu_diag2.json", "w"), indent=1)

if __name__ == "__main__":
    part2() if ARGV == ["part2"] else part1()
