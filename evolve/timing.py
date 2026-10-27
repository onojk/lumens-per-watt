"""Counterbalanced wall-clock timing for comparison scripts (PROTOCOL.md, "Timed runs").
Cells are timed with lampcore --phasetime (lctest.phasetime, pinned to core 2) in an interleaved, counterbalanced
order: replicate 1 runs the cells forward (ref, c1, ..., cn), replicate 2 backward (cn, ..., c1, ref), and so on, so
heat build-up affects every cell equally. The machine state (tools/machine_state.sh) is read before each replicate.
The order and the states are returned for the results.
"""
import os, subprocess
from lctest import phasetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def machine_state():
    return subprocess.run([os.path.join(ROOT, "tools", "machine_state.sh")], capture_output=True, text=True).stdout

def counterbalanced(cells, nums, reps=2, lpb=False):
    """cells: {name: genes}. Returns ({name: [phasetime result per replicate, in replicate order]},
    [(replicate, name) in the order timed], [machine state before each replicate])."""
    names = list(cells)
    res = {n: [None] * reps for n in names}
    order, states = [], []
    for r in range(reps):
        states.append(machine_state())
        for n in (names if r % 2 == 0 else names[::-1]):
            res[n][r] = phasetime(cells[n], nums, lpb)
            order.append((r + 1, n))
    return res, order, states
