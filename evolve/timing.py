"""Counterbalanced wall-clock timing for comparison scripts (PROTOCOL.md, "Timed runs").
Cells are timed with lampcore --phasetime (lctest.phasetime, pinned to core 2) in an interleaved, counterbalanced
order: replicate 1 runs the cells forward (ref, c1, ..., cn), replicate 2 backward (cn, ..., c1, ref), and so on, so
heat build-up affects every cell equally. The machine state (tools/machine_state.sh) is read before each replicate.
While each cell is timed, the pinned core's clock (cpufreq scaling_cur_freq) is sampled every second; per cell, the
samples' range and median are returned, and a cell whose median differs from the reference's (the first cell) by
more than 10% is flagged. The order, the states and the clock summary are returned for the results.
"""
import os, statistics, subprocess, threading
from lctest import phasetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def machine_state():
    return subprocess.run([os.path.join(ROOT, "tools", "machine_state.sh")], capture_output=True, text=True).stdout

FREQ = "/sys/devices/system/cpu/cpu2/cpufreq/scaling_cur_freq"   # core 2, as lctest.phasetime pins it

def timed_with_clock(fn, period=1.0):
    """Run fn() while sampling the pinned core's MHz every `period` seconds; returns (fn's result, [MHz samples])."""
    samples, stop = [], threading.Event()
    def sample():
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
