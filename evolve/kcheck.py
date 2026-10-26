"""Selected-multiplier check (information only; NOTES.md, the user's kc check and DeepSeek's D-k).
For each final genome (current final and the kc/lc round's new frozen genomes) on its size's map
numbers: the k qs would select (top Knuth-Schroeppel score among 1..kc; ties to the smaller k), how
often it would differ with kc = 16 / 24 / 32 / 64, and s (number of primes in A) for the new genomes.
Scoring only: no sieving.  python3 kcheck.py -> kcheck.out (stdout)
"""
import json, math, collections
from lamps import Meter, ks_score
from ledger import Charger, Ledger
import sizescale2 as S2

def top(N, kc, sc):
    return max(range(1, kc + 1), key=lambda k: (sc[k], -k))

def s_of(N, k, g):
    lnN = math.log(N); B = max(30, int(g["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
    led = Ledger(N, k, B, Charger(Meter(1 << 60), None), None)
    if led.build_base():
        return None
    M = max(64, int(g["mc"] * B)); target = math.isqrt(2 * k * N) / M
    pool = [p for p in led.base[2:] if k % p and p > 2]
    s = 1
    while target ** (1 / s) > pool[-1] and s < 8: s += 1
    while s > 1 and target ** (1 / s) < pool[min(len(pool) - 1, 2)]: s -= 1
    return s

cur = json.load(open("sizescale_r2_sealed.json"))
new = json.load(open("sizescale_k_budgets.json"))["genes"]
for bits in (54, 72, 84, 96):
    nums = S2.map_nums(bits)
    scores = [{k: ks_score(k, N) for k in range(1, 65)} for N, _, _ in nums]
    for tr in "RM":
        for lab, g in (("current final", cur["sizes"][str(bits)]["tracks"][tr]["final_genes"]), ("new frozen", new[str(bits)][tr])):
            kc = int(g["kc"])
            sel = [top(N, kc, sc) for (N, _, _), sc in zip(nums, scores)]
            ks = sorted(sel)
            n = len(ks)
            dist = collections.Counter(sel).most_common(6)
            diff = {c: sum(top(N, c, sc) != s for (N, _, _), sc, s in zip(nums, scores, sel)) / n for c in (16, 24, 32, 64)}
            sq = sum(1 for k in sel if all(k % (p * p) for p in range(2, 9))) / n
            line = (f"{bits} {tr} {lab:13s} kc {kc:2d}: selected k median {ks[n // 2]}, 90th pct {ks[int(0.9 * n)]}, max {ks[-1]}; "
                    f"top {dist}; squarefree {sq:.2f}; differs at kc 16/24/32/64: " + " / ".join(f"{diff[c]:.3f}" for c in diff))
            if lab == "new frozen":
                ss = collections.Counter(s_of(N, k, g) for (N, _, _), k in zip(nums, sel))
                line += f"; s {dict(sorted(ss.items(), key=lambda x: (x[0] is None, x[0] or 0)))}"
            print(line, flush=True)
    # flatness: the smallest kc above which the selected k never changes, over all map numbers
    flat = next(c for c in range(1, 65) if all(top(N, c, sc) == top(N, 64, sc) for (N, _, _), sc in zip(nums, scores)))
    print(f"{bits}: selected k is the same for every kc >= {flat} (up to 64) on all {len(nums)} map numbers", flush=True)
