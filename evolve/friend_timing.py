"""Timing cells on any machine, for replications (FRIEND.md; tools/friend_run.sh; tools/contribute_timing.sh).
Reads a committed run file runs/<name>.json:
  {"name": ..., "bits": 96, "numbers": 640 (the first n map numbers at that size), "replicates": 8, "seed": 2026,
   "cells": {"reference": {}, "root": {"confirm": "root"}, ...}}   (each cell: gene changes on the reference genes)
Times every cell once per replicate in its own seeded random order (as timing.shuffled), with lampcore --phasetime,
pinned to one core where taskset exists. Records the machine (CPU model, cores, OS, governor, MHz, temperatures and
RAPL energy where readable without root) before each replicate and at the end, and the pinned core's MHz while each
cell runs. Writes one JSON file and prints a one-screen summary: per cell, wall-clock per number (mean over
replicates) and the ratio to the first cell within each replicate (mean, 95% t interval).
  python3 friend_timing.py RUNFILE OUTFILE
"""
import glob, json, math, os, platform, random, shutil, socket, statistics, subprocess, sys, threading, time
ARGV = sys.argv[1:]                    # captured first: partition / sizescale clear sys.argv on import
import numpy as np
import partition as P, sizescale2 as S2, fastlamps
from lctest import ref

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 19: 2.093, 29: 2.045}
TASKSET = shutil.which("taskset")
CORE = min(2, (os.cpu_count() or 1) - 1)

def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None

def cpu_model():
    for line in (read("/proc/cpuinfo") or "").splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    if platform.system() == "Darwin":
        try:
            return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
        except OSError:
            pass
    return platform.processor() or "unknown"

def machine():
    c = f"/sys/devices/system/cpu/cpu{CORE}/cpufreq"
    temps = {}
    for z in glob.glob("/sys/class/thermal/thermal_zone*"):
        t, v = read(z + "/type"), read(z + "/temp")
        if t and v and v.lstrip("-").isdigit():
            temps[t] = int(v) / 1000
    rapl = {}
    for d in glob.glob("/sys/class/powercap/intel-rapl:*"):
        v = read(d + "/energy_uj")          # readable only if the system allows it; never changed here
        if v is not None:
            rapl[f"{os.path.basename(d)} {read(d + '/name')}"] = int(v)
    cur = read(c + "/scaling_cur_freq")
    return {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "cpu": cpu_model(), "cores": os.cpu_count(),
            "os": f"{platform.system()} {platform.release()}", "governor": read(c + "/scaling_governor"),
            "mhz": int(cur) / 1000 if cur else None, "max_mhz_limit": (int(read(c + "/scaling_max_freq")) / 1000) if read(c + "/scaling_max_freq") else None,
            "load": read("/proc/loadavg"), "temperatures_c": temps, "rapl_energy_uj": rapl or "not readable",
            "pinned_core": CORE if TASKSET else None}

def phasetime(g, nums):
    text = json.dumps([g]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    cmd = ([TASKSET, "-c", str(CORE)] if TASKSET else []) + [fastlamps.BIN, "--phasetime"]
    env = {k: v for k, v in os.environ.items() if k != "LAMPCORE_LPBREAK"}
    res = subprocess.run(cmd, input=text, capture_output=True, text=True, check=True, env=env)
    lines = [json.loads(l) for l in res.stderr.splitlines() if l.startswith("{")]
    over, recs = lines[0]["overhead_ns_per_region"], lines[1:]
    names = recs[0]["regions"]
    ns = np.sum([r["ns"] for r in recs], axis=0).astype(float)
    calls = np.sum([r["calls"] for r in recs], axis=0).astype(float)
    ns -= calls * over
    reg = {nm: ns[i] / len(nums) / 1e3 for i, nm in enumerate(names)}
    return {"wall_us": sum(v for k, v in reg.items() if not k.startswith("lp:")), "regions_us": reg}

def with_clock(fn):
    path, samples, stop = f"/sys/devices/system/cpu/cpu{CORE}/cpufreq/scaling_cur_freq", [], threading.Event()
    def loop():
        while True:
            v = read(path)
            if v:
                samples.append(int(v) / 1000)
            if stop.wait(1.0):
                return
    t = threading.Thread(target=loop, daemon=True); t.start()
    try:
        return fn(), samples
    finally:
        stop.set(); t.join()

def main(runfile, outfile):
    run = json.load(open(runfile))
    bits, n, reps, seed = run["bits"], run["numbers"], run["replicates"], run.get("seed", 2026)
    g0 = ref(bits)
    cells = {name: dict(g0, **chg) for name, chg in run["cells"].items()}
    names = list(cells)
    nums = S2.map_nums(bits)[:n]
    rng = random.Random(seed)
    res = {nm: [None] * reps for nm in names}
    mhz = {nm: [] for nm in names}
    order, states = [], []
    t0 = time.time()
    for r in range(reps):
        states.append(machine())
        perm = names[:]
        rng.shuffle(perm)
        for nm in perm:
            res[nm][r], smp = with_clock(lambda: phasetime(cells[nm], nums))
            mhz[nm] += smp
            order.append([r + 1, nm])
        print(f"replicate {r + 1} of {reps} done ({time.time() - t0:.0f} s)", flush=True)
    states.append(machine())
    out = {"run": run, "runfile": runfile, "host": socket.gethostname(), "git_head": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
           "taskset": bool(TASKSET), "order": order, "machine_before_each_replicate_and_at_end": states, "cells": {}}
    base = names[0]
    lines = []
    for nm in names:
        w = [x["wall_us"] for x in res[nm]]
        rec = {"genes": cells[nm], "wall_us": w, "regions_us": [x["regions_us"] for x in res[nm]],
               "mhz": {"min": min(mhz[nm]), "median": statistics.median(mhz[nm]), "max": max(mhz[nm]), "n": len(mhz[nm])} if mhz[nm] else None}
        line = f"  {nm}: {statistics.mean(w):,.1f} us per number"
        if nm != base:
            q = [a["wall_us"] / b["wall_us"] for a, b in zip(res[nm], res[base])]
            m = statistics.mean(q)
            h = T975.get(len(q) - 1, 2.0) * statistics.stdev(q) / math.sqrt(len(q)) if len(q) > 1 else None
            rec["ratio_to_first"] = {"per_replicate": q, "mean": m, "ci95_half_width": h}
            line += f", {100 * (m - 1):+.1f}% against {base}" + (f" (95% interval +-{100 * h:.1f} points)" if h is not None else "")
        out["cells"][nm] = rec
        lines.append(line)
    with open(outfile, "w") as f:
        json.dump(out, f, indent=1)
    st = states[0]
    print(f"\nRun '{run['name']}' finished in {(time.time() - t0) / 60:.1f} minutes on {out['host']} ({st['cpu']}, {st['cores']} cores, {st['os']}).")
    print(f"{n} numbers of {bits} bits, {len(names)} cells, {reps} replicates, random order seed {seed}"
          + ("" if TASKSET else "; NOT pinned to one core (taskset unavailable), so timings are noisier") + ".")
    print("Average time per number:")
    print("\n".join(lines))
    print(f"\nThe results are in {outfile}. Please send that one file back; nothing else is needed.")

if __name__ == "__main__":
    main(ARGV[0], ARGV[1])
