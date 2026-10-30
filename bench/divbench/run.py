"""The timed D for family (2) (the user's ruling, Oct 30): 64-bit DIV vs the timed word add, same dependent chain,
SQUFOF-sized operands at N = 48, 64, 80 bits. Pinned to core 2 (taskset), under the machine's 2.4 GHz cap; the machine
state is recorded before and after (tools/machine_state.sh). 5 rounds, the three modes interleaved in each round
(div, add, loop), 3 reps each of M = 2e7 iterations; per mode the median ns per iteration.
  D_timed = median(div) / median(add)                       (the ruling's definition: DIV vs the timed word add)
  D_net   = (median(div) - median(loop)) / (median(add) - median(loop))   (beside it, loop overhead removed; noisier)
  cd bench/divbench && cargo build --release && python3 run.py -> divbench.json, stdout"""
import json, statistics, subprocess
B, M, REPS, ROUNDS = "./target/release/divbench", 20_000_000, 3, 5

def state():
    return subprocess.run(["../../tools/machine_state.sh"], capture_output=True, text=True).stdout

before = state()
res = {}
for bits in (48, 64, 80):
    t = {m: [] for m in ("div", "add", "loop")}
    for r in range(ROUNDS):
        for mode in ("div", "add", "loop"):
            out = subprocess.run(["taskset", "-c", "2", B, str(bits), mode, str(M), str(1000 + r), str(REPS)],
                                 capture_output=True, text=True, check=True).stdout.split()
            t[mode] += [float(x) for x in out]
    md = {m: statistics.median(v) for m, v in t.items()}
    res[bits] = {"ns": md, "spread": {m: [min(v), max(v)] for m, v in t.items()},
                 "D_timed": md["div"] / md["add"], "D_net": (md["div"] - md["loop"]) / (md["add"] - md["loop"])}
    print(f"{bits} bits: ns per iteration div {md['div']:.3f} [{min(t['div']):.3f}, {max(t['div']):.3f}], add {md['add']:.3f} "
          f"[{min(t['add']):.3f}, {max(t['add']):.3f}], loop {md['loop']:.3f}; D_timed {res[bits]['D_timed']:.2f}, D_net {res[bits]['D_net']:.2f}")
after = state()
json.dump({"results": res, "machine_before": before, "machine_after": after}, open("divbench.json", "w"), indent=1)
for l in after.splitlines():
    if l.startswith(("cur MHz", "load average", "temperature TCPU", "pinned")):
        print("after:", l)
