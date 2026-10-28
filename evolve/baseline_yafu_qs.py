"""The fair YAFU re-run, baseline-yafu-qs (information only; predictions/baseline-yafu-qs.md, filed first; run only
through tools/sealed_run.sh). The card's QS against YAFU's QS called directly. Design: NOTES.md, "Proposed: a fair
YAFU re-run"; the user's decisions, Oct 27 evening (siqs() direct; the per-line floor as its own cell; YAFU's internal
time by (a), an instrumented copy; the callgrind cross-check).
  - YAFU: an instrumented copy of the user's build (c7d9028, the same make line), in Claude's scratch, YAFU_TIMED below:
    one change, factor/qs/siqs_test.c check_specialcase: CLOCK_MONOTONIC read before and after the tinysiqs call,
    printed to stderr as "lpw_tinysiqs_ns <ns>" per number. Below 115 bits siqs() runs exactly that call. Every YAFU
    cell uses this binary, in a fresh empty directory, batch on stdin, one thread, pinned to core 2.
  - The card: the current reference (2'b genes, release lampcore with the A-prime fix), batch, core 2.
  - Per size (72, 84, 96), cells in every replicate (4 replicates, the user's instruction; the order rotating and alternating):
      card      the card on the balanced band (the last band of 80)
      siqs      yafu "siqs(@)" on the balanced band: wall, and the internal tinysiqs time per number
      qs        yafu "smallmpqs(@)" on the balanced band (tinysiqs directly)
      floor     yafu "abs(@)" on the balanced band (the per-line cost)
      card_all  the card on all map numbers                         (information)
      siqs_all  yafu "siqs(@)" on all map numbers, wall and internal (information)
  - Per replicate: card / internal (THE SEALED RATIO: card wall per number / YAFU's internal tinysiqs time per number);
    siqs wall - internal (ms per number; R-25 / D-25); card / (qs - floor) (option (b)); card / siqs wall;
    card / qs wall; and the all-numbers card / internal. Means and 95% t intervals over the 4 (3 df, 3.182).
  - Factors on every number: the card's is p or q; siqs's P lines are {p, q}; smallmpqs prints p or q.
  - Conditions as Run B (else nothing is timed); pause above 90 C.
  - Once per size, after timing: the uninstrumented build's siqs(@) wall on the balanced band (the instrumentation's
    cost), and the callgrind cross-check on 10 balanced numbers: the card's Ir per number (10 numbers minus 0) against
    tinysiqs's inclusive Ir per number (clock-free, information).
  python3 baseline_yafu_qs.py -> baseline_yafu_qs.json, stdout"""
import json, math, os, re, statistics, subprocess, sys, tempfile, time
import partition as P, sizescale2 as S2
from fastlamps import BIN
from baseline_msieve import conditions, cool, reference
from timing import machine_state, timed_with_clock

SCRATCH = "/tmp/claude-1000/-home-onojk123-lumens-per-watt/ddfe4e3f-7fea-48e0-ba4d-4e65f4fd682d/scratchpad"
YAFU_TIMED = os.path.join(SCRATCH, "yafu-timed", "yafu")
YAFU = os.path.expanduser("~/opt/yafu-src/yafu/yafu")                    # uninstrumented (f5f9bde1...)
REPS, T3 = 4, 3.182                                                      # 4 replicates (the user, Oct 27 evening)
SIZES = (72, 84, 96)

def card(nums, bits):
    text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    t0 = time.perf_counter()
    out = subprocess.run(["taskset", "-c", "2", BIN], input=text, capture_output=True, text=True, check=True).stdout
    dt = time.perf_counter() - t0
    facs = [l.split()[1] for l in out.splitlines()]
    return dt, sum(f == "miss" or int(f) not in (p, q) for (N, p, q), f in zip(nums, facs))

def yafu(nums, func, binary=YAFU_TIMED):
    work = tempfile.mkdtemp(prefix="yq_")
    t0 = time.perf_counter()
    r = subprocess.run(["taskset", "-c", "2", binary, func, "-threads", "1"], input="".join(f"{N}\n" for N, _, _ in nums),
                       cwd=work, capture_output=True, text=True, check=True)
    dt = time.perf_counter() - t0
    ns = [int(x) for x in re.findall(r"^lpw_tinysiqs_ns (\d+)$", r.stderr, re.M)]
    if func == "siqs(@)":
        res, cur = {}, None
        for l in r.stdout.splitlines():
            l = l.strip()
            m = re.fullmatch(r"siqs\((\d+)\)", l)
            if m:
                cur = int(m.group(1)); res[cur] = set()
            elif cur is not None and re.fullmatch(r"(PRP|P)\d+ = \d+", l):
                res[cur].add(int(l.split(" = ")[1]))
        bad = sum(res.get(N) != {p, q} for N, p, q in nums) + (len(ns) != len(nums))
    elif func == "smallmpqs(@)":
        got = set(int(x) for x in re.findall(r"^(\d+)$", r.stdout, re.M))
        bad = sum(not (p in got or q in got) for _, p, q in nums)
    else:
        bad = 0
    return dt, ns, bad

def tstat(xs):
    m, h = statistics.mean(xs), T3 * statistics.stdev(xs) / math.sqrt(len(xs))
    return {"per_replicate": xs, "mean": m, "ci95": [m - h, m + h]}

def callgrind_ir(cmd, stdin, work, fn=None):
    out = os.path.join(work, f"cg{time.time_ns()}.out")
    subprocess.run(["valgrind", "--tool=callgrind", f"--callgrind-out-file={out}", *cmd], input=stdin, cwd=work,
                   capture_output=True, text=True, check=True)
    ann = subprocess.run(["callgrind_annotate", "--inclusive=yes", out], capture_output=True, text=True).stdout
    if fn is None:
        return int(re.search(r"([\d,]+) \S* *PROGRAM TOTALS", ann).group(1).replace(",", ""))
    m = re.search(r"^\s*([\d,]+) \([^)]*\)\s+\S*" + re.escape(fn) + r" \[", ann, re.M)
    return int(m.group(1).replace(",", "")) if m else None

if __name__ == "__main__":
    bad = conditions()
    state0 = machine_state()
    if bad:
        print("timing skipped: " + "; ".join(bad)); print(state0); sys.exit(2)
    out = {"card_binary": BIN, "yafu_timed": YAFU_TIMED, "yafu": YAFU, "replicates": REPS, "sizes": {}, "state_start": state0}
    for bits in SIZES:
        allnums = S2.map_nums(bits)
        bal = allnums[-P.PER_BAND:]
        cells = {"card": lambda: card(bal, bits), "siqs": lambda: yafu(bal, "siqs(@)"), "qs": lambda: yafu(bal, "smallmpqs(@)"),
                 "floor": lambda: yafu(bal, "abs(@)"), "card_all": lambda: card(allnums, bits),
                 "siqs_all": lambda: yafu(allnums, "siqs(@)")}
        n_of = {"card": len(bal), "siqs": len(bal), "qs": len(bal), "floor": len(bal), "card_all": len(allnums), "siqs_all": len(allnums)}
        names = list(cells)
        rec = {"n_bal": len(bal), "n_all": len(allnums), "ms": {k: [] for k in names}, "internal_ms": {"siqs": [], "siqs_all": []},
               "mhz": {k: [] for k in names}, "order": [], "states": [], "factor_failures": {k: 0 for k in names}}
        for r in range(REPS):
            cool()
            rec["states"].append(machine_state())
            order = names[r % len(names):] + names[:r % len(names)]
            if r % 2:
                order = order[::-1]
            rec["order"].append(order)
            for c in order:
                res, mhz = timed_with_clock(cells[c], period=0.05, skip_launch=True)
                dt = res[0]
                rec["ms"][c].append(1e3 * dt / n_of[c]); rec["mhz"][c] += mhz
                rec["factor_failures"][c] += res[-1]
                if c in rec["internal_ms"]:
                    rec["internal_ms"][c].append(1e-6 * statistics.mean(res[1]))
        ms, im = rec["ms"], rec["internal_ms"]
        rec["ratios"] = {
            "card / YAFU internal (sealed)": tstat([a / b for a, b in zip(ms["card"], im["siqs"])]),
            "siqs wall - internal, ms": tstat([a - b for a, b in zip(ms["siqs"], im["siqs"])]),
            "card / (qs - floor)": tstat([a / (b - c) for a, b, c in zip(ms["card"], ms["qs"], ms["floor"])]),
            "card / siqs wall": tstat([a / b for a, b in zip(ms["card"], ms["siqs"])]),
            "card / qs wall": tstat([a / b for a, b in zip(ms["card"], ms["qs"])]),
            "all numbers: card / YAFU internal": tstat([a / b for a, b in zip(ms["card_all"], im["siqs_all"])]),
            "all numbers: card / siqs wall": tstat([a / b for a, b in zip(ms["card_all"], ms["siqs_all"])])}
        rec["mean_ms"] = {k: statistics.mean(v) for k, v in ms.items()}
        rec["mean_internal_ms"] = {k: statistics.mean(v) for k, v in im.items()}
        rec["mhz_median"] = {k: (statistics.median(v) if v else None) for k, v in rec["mhz"].items()}
        print(f"{bits} bits (balanced {len(bal)}, all {len(allnums)}): ms per number " + ", ".join(f"{k} {v:.3f}" for k, v in rec["mean_ms"].items())
              + "; YAFU internal tinysiqs " + ", ".join(f"{k} {v:.3f}" for k, v in rec["mean_internal_ms"].items()), flush=True)
        for k, v in rec["ratios"].items():
            print(f"    {k}: {v['mean']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]", flush=True)
        print(f"    core 2 median MHz: " + ", ".join(f"{k} {v}" for k, v in rec["mhz_median"].items())
              + f"; factor checks failed: {rec['factor_failures']}", flush=True)
        # information, after timing
        cool()
        du, _, _ = yafu(bal, "siqs(@)", YAFU)
        rec["uninstrumented_siqs_ms"] = 1e3 * du / len(bal)
        print(f"    uninstrumented siqs(@) wall (one pass): {rec['uninstrumented_siqs_ms']:.3f} ms per number "
              f"(instrumented mean {rec['mean_ms']['siqs']:.3f})", flush=True)
        ten = bal[:10]
        work = tempfile.mkdtemp(prefix="yqcg_")
        gtxt = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n"
        c10 = callgrind_ir([BIN], gtxt + "".join(f"{N} {p} {q}\n" for N, p, q in ten), work)
        c0 = callgrind_ir([BIN], gtxt, work)
        t10 = callgrind_ir([YAFU_TIMED, "smallmpqs(@)", "-threads", "1"], "".join(f"{N}\n" for N, _, _ in ten), work, "tinysiqs")
        rec["callgrind"] = {"card_Ir_per_number": (c10 - c0) / 10, "tinysiqs_Ir_per_number": t10 / 10 if t10 else None}
        print(f"    callgrind, 10 balanced numbers: card {(c10 - c0) / 10 / 1e6:.2f} M Ir per number; tinysiqs "
              + (f"{t10 / 10 / 1e6:.2f} M Ir per number; ratio {(c10 - c0) / t10:.2f}" if t10 else "not found"), flush=True)
        out["sizes"][str(bits)] = rec
    out["state_end"] = machine_state()
    json.dump(out, open("baseline_yafu_qs.json", "w"), indent=1)
