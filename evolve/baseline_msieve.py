"""External baseline, I-038 (information only; msieve has no op meter and never enters fitness). Predictions:
predictions/baseline-msieve.md (the reviewer, D-18 / D-19, G-11 / G-12; filed before this ran).
msieve 1.53, built from source in ~/opt/msieve-src/msieve-1.53 (tarball sha256 c5fcbaaf...4d93bb4; its Makefile's
-O3 -march=native; NO_ZLIB=1). The card: the adopted reference (2'b: lctest.ref + goff = 1 + confirm = root), lampcore
release binary (baseline x86-64 target).
  - Conditions required before timing (else timing is skipped and the reason printed): AC online, scaling_max_freq
    2,400 MHz on every core, TCPU < 70 C, no Wolfram kernel. Machine state (tools/machine_state.sh) recorded before
    each replicate; timing pauses if TCPU passes 90 C and resumes below 70 C.
  - Per size (72, 84, 96; all map numbers): both tools in batch, one process over a file of the size's numbers, so
    start-up is paid once; pinned to core 2 (taskset); msieve -q -t 1 -i <file> in a scratch directory; 4 replicates,
    the order alternating (card first, then msieve first); core 2's clock sampled every 0.05 s.
  - Factors: msieve's prime factors must be {p, q} and the card's factor must be p or q, on every number.
  - Reported: wall per number (mean over replicates), the ratio card / msieve per replicate, its mean and 95% t
    interval (t3 = 3.182). THE SEALED COMPARISON is "card" (the qs card, 2'b) against "msieve" on all map numbers.
  - Information only (the user's additions, Oct 27, before timing), in the same replicates and rotation:
    "card_bal" against "msieve_bal": the balanced band only (the size's last band of 80, smaller factor near N/2):
    sieve against sieve; "pipeline": the full reference pipeline (td, rho, p-1, ecm, then the 2'b qs; budgets "(d)",
    as opclass/make_inputs.py) on all map numbers, against msieve. And once per size: msieve built with
    -march=x86-64 (MSIEVE_X86) on all map numbers (one replicate; the build difference), and one pass per band.
  python3 baseline_msieve.py -> baseline_msieve.json, stdout"""
import json, math, os, re, shutil, statistics, subprocess, sys, tempfile, time
import partition as P, sizescale2 as S2
from fastlamps import BIN
from lctest import ref
from timing import machine_state, timed_with_clock

MSIEVE = os.path.expanduser("~/opt/msieve-src/msieve-1.53/msieve")                 # -O3 -march=native (sha256 437f5da3...)
MSIEVE_X86 = os.path.expanduser("~/opt/msieve-src/msieve-1.53-x86-64/msieve")     # -O3 -march=x86-64 (sha256 2a9fc91d...)
REPS, T3 = 4, 3.182
SIZES = (72, 84, 96)

def conditions():
    bad = []
    online = [open(f"/sys/class/power_supply/{p}/online").read().strip() for p in os.listdir("/sys/class/power_supply")
              if os.path.exists(f"/sys/class/power_supply/{p}/online")]
    if "1" not in online:
        bad.append("AC not online")
    caps = {open(f"/sys/devices/system/cpu/{c}/cpufreq/scaling_max_freq").read().strip()
            for c in os.listdir("/sys/devices/system/cpu") if re.fullmatch(r"cpu\d+", c)
            and os.path.exists(f"/sys/devices/system/cpu/{c}/cpufreq/scaling_max_freq")}
    if caps != {"2400000"}:
        bad.append(f"cap not 2,400 MHz on every core ({sorted(caps)})")
    t = tcpu()
    if t is None or t >= 70:
        bad.append(f"TCPU {t} C (need < 70)")
    ps = subprocess.run(["ps", "-eo", "comm"], capture_output=True, text=True).stdout.split()
    if any("WolframKernel" in c or "MathKernel" in c for c in ps):
        bad.append("a Wolfram kernel is running")
    return bad

def tcpu():
    for z in os.listdir("/sys/class/thermal"):
        try:
            if open(f"/sys/class/thermal/{z}/type").read().strip() in ("TCPU", "x86_pkg_temp"):
                return int(open(f"/sys/class/thermal/{z}/temp").read()) // 1000
        except OSError:
            pass
    return None

def cool():
    if (tcpu() or 0) > 90:
        print(f"TCPU {tcpu()} C > 90: pausing until below 70", flush=True)
        while (tcpu() or 0) >= 70:
            time.sleep(5)

def reference(bits):
    return dict(ref(bits), goff=1, confirm="root")             # the adopted reference (Oct 27)

def pipeline(bits):
    import sizescale3 as K
    sealed = json.load(open("sizescale_k_sealed.json"))
    bud = sealed["sizes"][str(bits)]["tracks"]["R"]["budgets"]["(d) new winner, new budgets"]   # rho, pm1 B, ecm
    return K.pipeline(reference(bits), *bud)

def run_card(nums, bits, genome=None):
    gen = genome or [reference(bits)]
    text = json.dumps(gen) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    t0 = time.perf_counter()
    out = subprocess.run(["taskset", "-c", "2", BIN], input=text, capture_output=True, text=True, check=True).stdout
    dt = time.perf_counter() - t0
    facs = [l.split()[1] for l in out.splitlines()]
    return dt, facs

def run_msieve(nums, work, binary=MSIEVE):
    path = os.path.join(work, "in.txt")
    open(path, "w").write("".join(f"{N}\n" for N, _, _ in nums))
    for f in ("msieve.dat", "msieve.log"):
        if os.path.exists(os.path.join(work, f)):
            os.remove(os.path.join(work, f))
    t0 = time.perf_counter()
    out = subprocess.run(["taskset", "-c", "2", binary, "-q", "-t", "1", "-i", path], cwd=work,
                         capture_output=True, text=True, check=True).stdout
    dt = time.perf_counter() - t0
    res, cur = {}, None
    for l in out.splitlines():
        l = l.strip()
        if re.fullmatch(r"\d+", l):
            cur = int(l); res[cur] = []
        elif cur is not None and re.match(r"[pc]\d+: \d+", l):
            res[cur].append((l[0], int(l.split(": ")[1])))
    return dt, res

def check(nums, cfac, mres):
    bad = 0
    for (N, p, q), cf in zip(nums, cfac):
        if cf == "miss" or int(cf) not in (p, q):
            bad += 1
        fs = mres.get(N, [])
        if sorted(f for _, f in fs) != sorted((p, q)) or any(k != "p" for k, _ in fs):
            bad += 1
    return bad

if __name__ == "__main__":
    bad = conditions()
    state0 = machine_state()
    if bad:
        print("timing skipped: " + "; ".join(bad), flush=True)
        print(state0)
        sys.exit(2)
    work = tempfile.mkdtemp(prefix="msieve_")
    out = {"msieve": MSIEVE, "card_binary": BIN, "replicates": REPS, "sizes": {}, "state_start": state0}
    for BITS in SIZES:
        nums = S2.map_nums(BITS)
        n = len(nums)
        bal = nums[-P.PER_BAND:]                                  # the last band: smaller factor near N/2
        pipe = pipeline(BITS)
        cells = {"card": lambda: run_card(nums, BITS), "msieve": lambda: run_msieve(nums, work),
                 "pipeline": lambda: run_card(nums, BITS, pipe),
                 "card_bal": lambda: run_card(bal, BITS), "msieve_bal": lambda: run_msieve(bal, work)}
        size_of = {"card": n, "msieve": n, "pipeline": n, "card_bal": len(bal), "msieve_bal": len(bal)}
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
            ff = {"card": check(nums, res["card"], res["msieve"]), "pipeline": check(nums, res["pipeline"], res["msieve"]),
                  "balanced": check(bal, res["card_bal"], res["msieve_bal"])}
            for k, v in ff.items():
                rec["factor_failures"][k] = rec["factor_failures"].get(k, 0) + v
        def ratio(a, b):
            rs = [x / y for x, y in zip(rec["s"][a], rec["s"][b])]
            m, h = statistics.mean(rs), T3 * statistics.stdev(rs) / math.sqrt(REPS)
            return {"per_replicate": rs, "ratio": m, "ci95": [m - h, m + h]}
        rec["us"] = {k: 1e6 * statistics.mean(v) / size_of[k] for k, v in rec["s"].items()}
        rec["ratios"] = {"card / msieve (sealed)": ratio("card", "msieve"), "pipeline / msieve": ratio("pipeline", "msieve"),
                         "card / msieve, balanced band": ratio("card_bal", "msieve_bal")}
        rec["mhz_median"] = {k: (statistics.median(v) if v else None) for k, v in rec["mhz"].items()}
        print(f"{BITS} bits ({n} numbers; balanced band {len(bal)}, smaller factor {rec['bal_smaller_factor_bits'][0]}-"
              f"{rec['bal_smaller_factor_bits'][1]} bits): us per number " + ", ".join(f"{k} {v:,.1f}" for k, v in rec["us"].items()), flush=True)
        for k, v in rec["ratios"].items():
            print(f"    {k}: {v['ratio']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]", flush=True)
        print(f"    core 2 median MHz: " + ", ".join(f"{k} {v}" for k, v in rec["mhz_median"].items())
              + f"; factor checks failed: {rec['factor_failures']}", flush=True)
        # information: msieve built for baseline x86-64, one replicate
        cool()
        dx, mx = run_msieve(nums, work, MSIEVE_X86)
        rec["msieve_x86_64_us"] = 1e6 * dx / n
        rec["msieve_x86_64_factor_failures"] = check(nums, res["card"], mx)
        print(f"    msieve -march=x86-64 (one replicate): {1e6 * dx / n:,.1f} us per number against native "
              f"{rec['us']['msieve']:,.1f} (x{dx / n * 1e6 / rec['us']['msieve']:.2f})", flush=True)
        # information: one pass per band, batch per band
        rec["bands"] = {}
        for b in range(n // P.PER_BAND):
            bn = nums[b * P.PER_BAND:(b + 1) * P.PER_BAND]
            cool()
            dc, _ = run_card(bn, BITS); dm, _ = run_msieve(bn, work)
            small = [min(min(p, q) for _, p, q in bn).bit_length(), max(min(p, q) for _, p, q in bn).bit_length()]
            rec["bands"][b] = {"smaller_factor_bits": small, "card_us": 1e6 * dc / len(bn), "msieve_us": 1e6 * dm / len(bn), "ratio": dc / dm}
            print(f"    band {b} (smaller factor {small[0]}-{small[1]} bits): card {1e6 * dc / len(bn):,.1f} us, msieve "
                  f"{1e6 * dm / len(bn):,.1f} us, ratio {dc / dm:.2f} (one pass, information)", flush=True)
        out["sizes"][str(BITS)] = rec
    out["state_end"] = machine_state()
    shutil.rmtree(work, ignore_errors=True)
    json.dump(out, open("baseline_msieve.json", "w"), indent=1)
