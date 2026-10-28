"""Sealed timing, allocate once per attempt (predictions/alloc-once.md, filed first; run only through tools/sealed_run.sh).
Cells: "2'b+fix" = the reference genes (lctest.ref + goff = 1 + confirm = root) on the lampcore with the A-prime fix
(sha256 ef345913..., built from f988aab, kept in Claude's scratch); "2'b+fix+alloc" = the same genes on this commit's
release build. All map numbers at 72 / 84 / 96, batch (one process per cell per replicate), pinned to core 2;
8 replicates, the order alternating (2'b+fix first in odd replicates). Conditions as baseline_msieve.conditions (else no
timing); pause above 90 C. Reported: wall per number, the ratio alloc / fix per replicate, its mean and 95% t interval
(7 df, 2.3646), as a percent change. Checked once per size: both cells' stdout with --types identical.
  Battery override (the user's decision, this run only, Oct 27 late): with LPW_BATTERY_RUN=user-decision-2026-10-27 in
  the environment, only the AC check is skipped (the cap, TCPU and Wolfram checks stay); the battery level is recorded
  at the start and end; before every replicate the run stops (exit 3) if the battery is below 25% or the CPU frequency
  policy (governor, energy_performance_preference, scaling_min/max_freq, no_turbo, min/max_perf_pct, every core)
  differs from the start. Without the variable the conditions are unchanged.
  python3 alloconce_time.py -> alloconce_time.json, stdout"""
import hashlib, json, math, os, statistics, subprocess, sys, time
import partition as P, sizescale2 as S2
from fastlamps import BIN
from baseline_msieve import conditions, cool, reference
from timing import machine_state, timed_with_clock

HERE = os.path.dirname(os.path.abspath(__file__))
BEFORE = "/tmp/claude-1000/-home-onojk123-lumens-per-watt/ddfe4e3f-7fea-48e0-ba4d-4e65f4fd682d/scratchpad/lampcore_fix_ef3459"
REPS, T7 = 8, 2.3646
BATTERY_RUN = os.environ.get("LPW_BATTERY_RUN") == "user-decision-2026-10-27"

def battery():
    for b in sorted(os.listdir("/sys/class/power_supply")):
        if b.startswith("BAT"):
            return int(open(f"/sys/class/power_supply/{b}/capacity").read())
    return None

def freq_policy():
    out = {}
    for c in sorted(os.listdir("/sys/devices/system/cpu")):
        d = f"/sys/devices/system/cpu/{c}/cpufreq"
        if c.startswith("cpu") and c[3:].isdigit() and os.path.isdir(d):
            for f in ("scaling_governor", "energy_performance_preference", "scaling_min_freq", "scaling_max_freq"):
                if os.path.exists(f"{d}/{f}"):
                    out[f"{c}/{f}"] = open(f"{d}/{f}").read().strip()
    for f in ("no_turbo", "min_perf_pct", "max_perf_pct"):
        q = f"/sys/devices/system/cpu/intel_pstate/{f}"
        if os.path.exists(q):
            out[f"intel_pstate/{f}"] = open(q).read().strip()
    return out
SIZES = (72, 84, 96)

def run(binary, nums, bits, types=False):
    text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    t0 = time.perf_counter()
    out = subprocess.run(["taskset", "-c", "2", binary] + (["--types"] if types else []), input=text,
                         capture_output=True, text=True, check=True).stdout
    return time.perf_counter() - t0, out

if __name__ == "__main__":
    sha = {k: hashlib.sha256(open(b, "rb").read()).hexdigest() for k, b in (("2'b+fix", BEFORE), ("2'b+fix+alloc", BIN))}
    print("binaries:", {k: v[:16] for k, v in sha.items()}, flush=True)
    if not sha["2'b+fix"].startswith("ef3459130e46133f"):
        print("the before binary is not ef345913...: stopping"); sys.exit(2)
    bad = conditions()
    if BATTERY_RUN:
        bad = [b for b in bad if b != "AC not online"]                 # the user's override: AC only
        print(f"battery (user's decision): AC check skipped for this run; battery {battery()}% at the start", flush=True)
    state0 = machine_state()
    policy0 = freq_policy()
    if bad:
        print("timing skipped: " + "; ".join(bad)); print(state0); sys.exit(2)
    out = {"binaries": sha, "replicates": REPS, "sizes": {}, "state_start": state0, "freq_policy_start": policy0,
           "power": "battery (user's decision)" if BATTERY_RUN else "conditions as baseline_msieve", "battery_start_pct": battery()}
    def guard():
        if not BATTERY_RUN:
            return
        b, pol = battery(), freq_policy()
        if b is not None and b < 25:
            print(f"STOP: battery {b}% < 25%"); out["stopped"] = f"battery {b}%"; json.dump(out, open("alloconce_time.json", "w"), indent=1); sys.exit(3)
        if pol != policy0:
            diff = {k: (policy0.get(k), pol.get(k)) for k in set(pol) | set(policy0) if pol.get(k) != policy0.get(k)}
            print(f"STOP: the CPU frequency policy changed: {diff}"); out["stopped"] = f"policy changed {diff}"
            json.dump(out, open("alloconce_time.json", "w"), indent=1); sys.exit(3)
    cells = {"2'b+fix": BEFORE, "2'b+fix+alloc": BIN}
    for bits in SIZES:
        nums = S2.map_nums(bits)
        same = run(BEFORE, nums, bits, True)[1] == run(BIN, nums, bits, True)[1]
        rec = {"n": len(nums), "outputs_identical": same, "s": {k: [] for k in cells}, "mhz": {k: [] for k in cells},
               "order": [], "states": []}
        for r in range(REPS):
            cool()
            guard()
            rec["states"].append(machine_state())
            order = list(cells) if r % 2 == 0 else list(cells)[::-1]
            rec["order"].append(order)
            for c in order:
                (dt, _), mhz = timed_with_clock(lambda: run(cells[c], nums, bits), period=0.05, skip_launch=True)
                rec["s"][c].append(dt); rec["mhz"][c] += mhz
        rs = [b / a for a, b in zip(rec["s"]["2'b+fix"], rec["s"]["2'b+fix+alloc"])]
        m, h = statistics.mean(rs), T7 * statistics.stdev(rs) / math.sqrt(REPS)
        rec["ratio"] = {"per_replicate": rs, "mean": m, "ci95": [m - h, m + h]}
        rec["us"] = {k: 1e6 * statistics.mean(v) / len(nums) for k, v in rec["s"].items()}
        rec["mhz_median"] = {k: (statistics.median(v) if v else None) for k, v in rec["mhz"].items()}
        print(f"{bits} bits ({len(nums)} numbers): outputs with --types identical: {same}; us per number "
              + ", ".join(f"{k} {v:,.1f}" for k, v in rec["us"].items())
              + f"; alloc / fix {m:.4f} [{m - h:.4f}, {m + h:.4f}] = {100 * (m - 1):+.2f}% [{100 * (m - h - 1):+.2f}, {100 * (m + h - 1):+.2f}]"
              + "; core 2 median MHz " + ", ".join(f"{k} {v}" for k, v in rec["mhz_median"].items()), flush=True)
        out["sizes"][str(bits)] = rec
    out["state_end"] = machine_state()
    out["battery_end_pct"] = battery()
    if BATTERY_RUN:
        print(f"battery (user's decision): {out['battery_start_pct']}% at the start, {out['battery_end_pct']}% at the end; "
              f"frequency policy unchanged: {freq_policy() == policy0}", flush=True)
    json.dump(out, open("alloconce_time.json", "w"), indent=1)
