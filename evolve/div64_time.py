"""Sealed timing, divide hits in 64-bit hardware steps (predictions/div64.md, filed first; run only through tools/sealed_run.sh).
Cells: "alloc" = the reference genes (lctest.ref + goff = 1 + confirm = root) on lampcore f6aa08d (alloc-once)
(sha256 13554a61..., kept in Claude's scratch); "alloc+div64" = the same genes on this change's
release build. All map numbers at 72 / 84 / 96, batch (one process per cell per replicate), pinned to core 2;
8 replicates, the order alternating (alloc first in odd replicates). Conditions as baseline_msieve.conditions (else no
timing); pause above 90 C. Reported: wall per number, the ratio div64 / alloc per replicate, its mean and 95% t interval
(7 df, 2.3646), as a percent change. Checked once per size: both cells' stdout with --types identical.
  python3 div64_time.py -> div64_time.json, stdout"""
import hashlib, json, math, os, statistics, subprocess, sys, time
import partition as P, sizescale2 as S2
from fastlamps import BIN
from baseline_msieve import conditions, cool, reference
from timing import machine_state, timed_with_clock

HERE = os.path.dirname(os.path.abspath(__file__))
BEFORE = "/tmp/claude-1000/-home-onojk123-lumens-per-watt/ddfe4e3f-7fea-48e0-ba4d-4e65f4fd682d/scratchpad/lampcore_alloc_13554a"
REPS, T7 = 8, 2.3646
SIZES = (72, 84, 96)

def run(binary, nums, bits, types=False):
    text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    t0 = time.perf_counter()
    out = subprocess.run(["taskset", "-c", "2", binary] + (["--types"] if types else []), input=text,
                         capture_output=True, text=True, check=True).stdout
    return time.perf_counter() - t0, out

if __name__ == "__main__":
    sha = {k: hashlib.sha256(open(b, "rb").read()).hexdigest() for k, b in (("alloc", BEFORE), ("alloc+div64", BIN))}
    print("binaries:", {k: v[:16] for k, v in sha.items()}, flush=True)
    if not sha["alloc"].startswith("13554a617c8446b5"):
        print("the before binary is not 13554a61...: stopping"); sys.exit(2)
    bad = conditions()
    state0 = machine_state()
    if bad:
        print("timing skipped: " + "; ".join(bad)); print(state0); sys.exit(2)
    out = {"binaries": sha, "replicates": REPS, "sizes": {}, "state_start": state0}
    cells = {"alloc": BEFORE, "alloc+div64": BIN}
    for bits in SIZES:
        nums = S2.map_nums(bits)
        same = run(BEFORE, nums, bits, True)[1] == run(BIN, nums, bits, True)[1]
        rec = {"n": len(nums), "outputs_identical": same, "s": {k: [] for k in cells}, "mhz": {k: [] for k in cells},
               "order": [], "states": []}
        for r in range(REPS):
            cool()
            rec["states"].append(machine_state())
            order = list(cells) if r % 2 == 0 else list(cells)[::-1]
            rec["order"].append(order)
            for c in order:
                (dt, _), mhz = timed_with_clock(lambda: run(cells[c], nums, bits), period=0.05, skip_launch=True)
                rec["s"][c].append(dt); rec["mhz"][c] += mhz
        rs = [b / a for a, b in zip(rec["s"]["alloc"], rec["s"]["alloc+div64"])]
        m, h = statistics.mean(rs), T7 * statistics.stdev(rs) / math.sqrt(REPS)
        rec["ratio"] = {"per_replicate": rs, "mean": m, "ci95": [m - h, m + h]}
        rec["us"] = {k: 1e6 * statistics.mean(v) / len(nums) for k, v in rec["s"].items()}
        rec["mhz_median"] = {k: (statistics.median(v) if v else None) for k, v in rec["mhz"].items()}
        print(f"{bits} bits ({len(nums)} numbers): outputs with --types identical: {same}; us per number "
              + ", ".join(f"{k} {v:,.1f}" for k, v in rec["us"].items())
              + f"; div64 / alloc {m:.4f} [{m - h:.4f}, {m + h:.4f}] = {100 * (m - 1):+.2f}% [{100 * (m - h - 1):+.2f}, {100 * (m + h - 1):+.2f}]"
              + "; core 2 median MHz " + ", ".join(f"{k} {v}" for k, v in rec["mhz_median"].items()), flush=True)
        out["sizes"][str(bits)] = rec
    out["state_end"] = machine_state()
    json.dump(out, open("div64_time.json", "w"), indent=1)
