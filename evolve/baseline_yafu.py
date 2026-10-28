"""External baseline, I-038, the second (information only; YAFU has no op meter and never enters fitness). Predictions:
predictions/baseline-yafu.md (D-21 / D-22, R-21 / R-22; filed before this ran). The same design as baseline_msieve.py.
YAFU c7d9028 (Oct 15 2026), built in ~/opt/yafu-src/yafu: make yafu GMP_INCDIR=/usr/include/x86_64-linux-gnu
USE_AVX2=1 USE_BMI2=1 ECM=1 (gcc -O2, SSE4.1 + AVX2 + BMI2; system GMP and GMP-ECM). The card: the adopted
reference (2'b), lampcore release binary.
  - YAFU runs its full default factor() (its own trial division, Fermat, rho and ECM before SIQS), one thread, batch
    (the numbers piped on stdin: one process per run, start-up paid once), pinned to core 2, in an empty scratch
    directory without yafu.ini (built-in defaults):  taskset -c 2 <yafu> "factor(@)" -threads 1 < in.txt
  - Conditions as baseline_msieve.conditions (else no timing); machine state before each replicate; pause above 90 C.
  - Per size (72, 84, 96; all map numbers), 4 replicates, the order rotating and alternating as in baseline_msieve;
    core 2's clock sampled every 0.05 s.
  - Factors: YAFU's prime factors (P / PRP lines under "***factors found***") must be {p, q}, and the card's factor
    p or q, on every number.
  - THE SEALED COMPARISON: "card" (2'b) against "yafu" on all map numbers. Information, in the same replicates:
    "card_bal" against "yafu_bal" (the balanced band: the last band of 80, the same command) and "pipeline" (the
    full reference pipeline, as baseline_msieve) against "yafu"; once per size, one pass per band.
  python3 baseline_yafu.py -> baseline_yafu.json, stdout"""
import json, math, os, re, shutil, statistics, subprocess, sys, tempfile, time
import partition as P, sizescale2 as S2
from fastlamps import BIN
from baseline_msieve import conditions, cool, pipeline, run_card
from timing import machine_state, timed_with_clock

YAFU = os.path.expanduser("~/opt/yafu-src/yafu/yafu")                  # sha256 f5f9bde1...
REPS, T3 = 4, 3.182
SIZES = (72, 84, 96)

def run_yafu(nums, work):
    for f in os.listdir(work):                                          # an empty directory each run: no yafu.ini, no logs
        os.remove(os.path.join(work, f))
    text = "".join(f"{N}\n" for N, _, _ in nums)
    t0 = time.perf_counter()
    out = subprocess.run(["taskset", "-c", "2", YAFU, "factor(@)", "-threads", "1"], input=text, cwd=work,
                         capture_output=True, text=True, check=True).stdout
    dt = time.perf_counter() - t0
    res, cur, found = {}, None, False
    for l in out.splitlines():
        l = l.strip()
        m = re.fullmatch(r"factor\((\d+)\)", l)
        if m:
            cur = int(m.group(1)); res[cur] = []; found = False
        elif l == "***factors found***":
            found = True
        elif found and cur is not None and re.fullmatch(r"(PRP|P|C)\d+ = \d+", l):
            res[cur].append((l.split()[0].rstrip("0123456789"), int(l.split(" = ")[1])))
    return dt, res

def check(nums, cfac, yres):
    bad = 0
    for (N, p, q), cf in zip(nums, cfac):
        if cf == "miss" or int(cf) not in (p, q):
            bad += 1
        fs = yres.get(N, [])
        if sorted(f for _, f in fs) != sorted((p, q)) or any(k == "C" for k, _ in fs):
            bad += 1
    return bad

if __name__ == "__main__":
    bad = conditions()
    state0 = machine_state()
    if bad:
        print("timing skipped: " + "; ".join(bad), flush=True)
        print(state0)
        sys.exit(2)
    work = tempfile.mkdtemp(prefix="yafu_")
    out = {"yafu": YAFU, "command": f'taskset -c 2 {YAFU} "factor(@)" -threads 1 < in.txt', "card_binary": BIN,
           "replicates": REPS, "sizes": {}, "state_start": state0}
    for BITS in SIZES:
        nums = S2.map_nums(BITS)
        n = len(nums)
        bal = nums[-P.PER_BAND:]
        pipe = pipeline(BITS)
        cells = {"card": lambda: run_card(nums, BITS), "yafu": lambda: run_yafu(nums, work),
                 "pipeline": lambda: run_card(nums, BITS, pipe),
                 "card_bal": lambda: run_card(bal, BITS), "yafu_bal": lambda: run_yafu(bal, work)}
        size_of = {"card": n, "yafu": n, "pipeline": n, "card_bal": len(bal), "yafu_bal": len(bal)}
        names = list(cells)
        rec = {"n": n, "n_bal": len(bal), "bal_smaller_factor_bits": [min(min(p, q) for _, p, q in bal).bit_length(),
               max(min(p, q) for _, p, q in bal).bit_length()], "pipeline": pipe,
               "s": {k: [] for k in names}, "mhz": {k: [] for k in names}, "order": [], "states": [], "factor_failures": {}}
        res = {}
        for r in range(REPS):
            cool()
            rec["states"].append(machine_state())
            order = names[r % len(names):] + names[:r % len(names)]
            if r % 2:
                order = order[::-1]
            rec["order"].append(order)
            for cell in order:
                (dt, x), mhz = timed_with_clock(cells[cell], period=0.05, skip_launch=True)
                rec["s"][cell].append(dt); rec["mhz"][cell] += mhz; res[cell] = x
            ff = {"card": check(nums, res["card"], res["yafu"]), "pipeline": check(nums, res["pipeline"], res["yafu"]),
                  "balanced": check(bal, res["card_bal"], res["yafu_bal"])}
            for k, v in ff.items():
                rec["factor_failures"][k] = rec["factor_failures"].get(k, 0) + v
        def ratio(a, b):
            rs = [x / y for x, y in zip(rec["s"][a], rec["s"][b])]
            m, h = statistics.mean(rs), T3 * statistics.stdev(rs) / math.sqrt(REPS)
            return {"per_replicate": rs, "ratio": m, "ci95": [m - h, m + h]}
        rec["us"] = {k: 1e6 * statistics.mean(v) / size_of[k] for k, v in rec["s"].items()}
        rec["ratios"] = {"card / yafu (sealed)": ratio("card", "yafu"), "pipeline / yafu": ratio("pipeline", "yafu"),
                         "card / yafu, balanced band": ratio("card_bal", "yafu_bal")}
        rec["mhz_median"] = {k: (statistics.median(v) if v else None) for k, v in rec["mhz"].items()}
        print(f"{BITS} bits ({n} numbers; balanced band {len(bal)}, smaller factor {rec['bal_smaller_factor_bits'][0]}-"
              f"{rec['bal_smaller_factor_bits'][1]} bits): us per number " + ", ".join(f"{k} {v:,.1f}" for k, v in rec["us"].items()), flush=True)
        for k, v in rec["ratios"].items():
            print(f"    {k}: {v['ratio']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]", flush=True)
        print(f"    core 2 median MHz: " + ", ".join(f"{k} {v}" for k, v in rec["mhz_median"].items())
              + f"; factor checks failed: {rec['factor_failures']}", flush=True)
        rec["bands"] = {}
        for b in range(n // P.PER_BAND):
            bn = nums[b * P.PER_BAND:(b + 1) * P.PER_BAND]
            cool()
            dc, _ = run_card(bn, BITS); dy, _ = run_yafu(bn, work)
            small = [min(min(p, q) for _, p, q in bn).bit_length(), max(min(p, q) for _, p, q in bn).bit_length()]
            rec["bands"][b] = {"smaller_factor_bits": small, "card_us": 1e6 * dc / len(bn), "yafu_us": 1e6 * dy / len(bn), "ratio": dc / dy}
            print(f"    band {b} (smaller factor {small[0]}-{small[1]} bits): card {1e6 * dc / len(bn):,.1f} us, yafu "
                  f"{1e6 * dy / len(bn):,.1f} us, ratio {dc / dy:.2f} (one pass, information)", flush=True)
        out["sizes"][str(BITS)] = rec
    out["state_end"] = machine_state()
    shutil.rmtree(work, ignore_errors=True)
    json.dump(out, open("baseline_yafu.json", "w"), indent=1)
