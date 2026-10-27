"""Counterbalanced wall-clock timing for comparison scripts (PROTOCOL.md, "Timed runs").
Cells are timed with lampcore --phasetime (lctest.phasetime, pinned to core 2) in an interleaved, counterbalanced
order: replicate 1 runs the cells forward (ref, c1, ..., cn), replicate 2 backward (cn, ..., c1, ref), and so on, so
heat build-up affects every cell equally. The machine state (tools/machine_state.sh) is read before each replicate.
While each cell is timed, the pinned core's clock (cpufreq scaling_cur_freq) is sampled every second; per cell, the
samples' range and median are returned, and a cell whose median differs from the reference's (the first cell) by
more than 10% is flagged. The order, the states and the clock summary are returned for the results.
"""
import os, random, statistics, subprocess, threading
from lctest import phasetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def machine_state():
    return subprocess.run([os.path.join(ROOT, "tools", "machine_state.sh")], capture_output=True, text=True).stdout

FREQ = "/sys/devices/system/cpu/cpu2/cpufreq/scaling_cur_freq"   # core 2, as lctest.phasetime pins it

def timed_with_clock(fn, period=1.0, skip_launch=False):
    """Run fn() while sampling the pinned core's MHz every `period` seconds; returns (fn's result, [MHz samples]).
    By default the first sample is read at launch, before the core has ramped; with skip_launch it is read after
    the first period (for short cells: NOTES.md, "Clock samples in short cells")."""
    samples, stop = [], threading.Event()
    def sample():
        if skip_launch and stop.wait(period):
            return
        while True:
            try:
                samples.append(int(open(FREQ).read()) / 1000)
            except OSError:
                pass
            if stop.wait(period):
                return
    t = threading.Thread(target=sample, daemon=True)
    t.start()
    try:
        out = fn()
    finally:
        stop.set(); t.join()
    return out, samples

def counterbalanced(cells, nums, reps=2, lpb=False):
    """cells: {name: genes}, the reference first. Returns ({name: [phasetime result per replicate, in replicate order]},
    [(replicate, name) in the order timed], [machine state before each replicate],
    {name: {"min", "median", "max", "n", "flag"}} for the pinned core's MHz while the cell was timed)."""
    names = list(cells)
    res = {n: [None] * reps for n in names}
    mhz = {n: [] for n in names}
    order, states = [], []
    for r in range(reps):
        states.append(machine_state())
        for n in (names if r % 2 == 0 else names[::-1]):
            res[n][r], smp = timed_with_clock(lambda: phasetime(cells[n], nums, lpb))
            mhz[n] += smp
            order.append((r + 1, n))
    clock = {n: {"min": min(v), "median": statistics.median(v), "max": max(v), "n": len(v)} if v else {"n": 0} for n, v in mhz.items()}
    ref = clock[names[0]].get("median")
    for n in names:
        med = clock[n].get("median")
        clock[n]["flag"] = bool(ref and med and abs(med / ref - 1) > 0.10)
    return res, order, states, clock

def mean_passes(ps):
    """Several phasetime passes of one cell as one: ns averaged per region; priced, calls and units are deterministic."""
    out = {k: dict(v) for k, v in ps[0].items()}
    for k in out:
        out[k]["ns"] = sum(p[k]["ns"] for p in ps) / len(ps)
    return out

def shuffled(cells, nums, reps=8, seed=2026, period=1.0, skip_launch=False, inner=1, svb=False, min_per_pass=3):
    """As counterbalanced, but each replicate times the cells in its own random order (random.Random(seed), one
    shuffle per replicate), so heat build-up is spread over the cells. The cells are the reference first; the
    orders, the per-replicate machine states and the clock summary are returned as by counterbalanced.
    Short cells (NOTES.md, "Clock samples in short cells"): period (s) between core-2 MHz samples; skip_launch drops
    the launch sample; inner > 1 times each cell inner times back to back per replicate (ns averaged); svb times the
    sieve sub-regions. Each cell's clock summary also gives "per_pass" (samples per timed pass) and "valid" (per_pass
    >= min_per_pass): a flag on a cell that is not valid rests on too few samples to mean anything."""
    names = list(cells)
    rng = random.Random(seed)
    res = {n: [None] * reps for n in names}
    mhz = {n: [] for n in names}
    order, states = [], []
    for r in range(reps):
        states.append(machine_state())
        perm = names[:]
        rng.shuffle(perm)
        for n in perm:
            ps = []
            for _ in range(inner):
                p, smp = timed_with_clock(lambda: phasetime(cells[n], nums, False, svb), period, skip_launch)
                ps.append(p)
                mhz[n] += smp
            res[n][r] = ps[0] if inner == 1 else mean_passes(ps)
            order.append((r + 1, n))
    clock = {n: {"min": min(v), "median": statistics.median(v), "max": max(v), "n": len(v)} if v else {"n": 0} for n, v in mhz.items()}
    ref = clock[names[0]].get("median")
    for n in names:
        med = clock[n].get("median")
        clock[n]["flag"] = bool(ref and med and abs(med / ref - 1) > 0.10)
        clock[n]["per_pass"] = clock[n]["n"] / (reps * inner)
        clock[n]["valid"] = clock[n]["per_pass"] >= min_per_pass
    return res, order, states, clock
