"""Light spectrum v1 (the user's next round, item 1, Oct 28; Phase 3; information only, counts, no timing).
For 72, 84 and 96 bits, numbers in theta bands of width 0.02 from 0.10 to 0.50 (theta = log2 p / log2 N, p the smaller
prime; 20 bands), 40 fresh numbers per band per size (seeds 9700000 + 1000 * bits + band), each lamp ALONE in lampcore
--types:
  rho, p-1: the reference pipeline's budgets ("(d)", sizescale_k_sealed.json: rho ob, p-1 B with ob = 2B)
  td, ECM: budget 0 in the reference pipeline (off), so the earlier maps' setting: cap 2^21 ops (partition.PRE genes)
  CFRAC: not in the reference; its accepted genes (cfrac_accept.py: kc 32, bc 1.1), the QS cap 2^28
  QS: the reference genes (2'b), the QS cap 2^28 (lampcore at this commit: alloc-once, div64, and the partials table if built)
Per number: success (a factor p or q) and priced cost: op-class v1 (opclass/opclass_v1.json weights; types with no weight
counted as 0 and listed) and ruint (optypes.prices, median P-core). light = successes / total cost (per million units).
Twilight band (defined before running): the bands where the best non-QS lamp's light is within 2.5x of QS's (ratio in
[0.4, 2.5]) under ruint.
Instruction check (added Oct 28, before the sealed run; from Grok's information-only point, the user's addition): for each
lamp in each band, the total instructions retired (callgrind 3.25.1 whole-program summary, attribution-free) on the band's
first 8 numbers, less the lamp's start-up (the same genome on no numbers), beside the op-class v1 cost of those 8
numbers. Flag a band where op-class / instructions differs from that lamp's pooled ratio at the same size by > 25%.
Run in parallel (6 workers), untimed.
  python3 light_spectrum.py -> light_spectrum.json, light_spectrum.csv, stdout"""
import json, math, os, random, re, subprocess, tempfile
from multiprocessing import Pool
import partition as P, optypes
from lamps import rand_prime
from fastlamps import BIN
from baseline_msieve import reference

SIZES = (72, 84, 96)
BANDS = [round(0.10 + 0.02 * i, 2) for i in range(20)]
PER = 40
V1 = {k: v["weight"] for k, v in json.load(open("../opclass/opclass_v1.json"))["classes"].items() if v["weight"]}
PR = optypes.prices()["ruint"]

def band_numbers(bits, lo, seed):
    rng, out = random.Random(seed), []
    while len(out) < PER:
        pb = max(4, round(rng.uniform(lo, lo + 0.02) * bits))
        p = rand_prime(pb, rng)
        q = rand_prime(bits - pb + 1, rng)
        N = p * q
        if N.bit_length() != bits or p == q:
            continue
        p, q = min(p, q), max(p, q)
        th = math.log2(p) / math.log2(N)
        if lo <= th < lo + 0.02:
            out.append((N, p, q))
    return out

def lamps(bits):
    bud = json.load(open("sizescale_k_sealed.json"))["sizes"][str(bits)]["tracks"]["R"]["budgets"]["(d) new winner, new budgets"]
    return {"td": ([dict(P.PRE["td"])], P.PRE_CAP), "rho": ([dict(P.PRE["rho"], ob=bud[0])], P.QS_CAP),
            "pm1": ([dict(P.PRE["pm1"], B=int(bud[1]), ob=2 * int(bud[1]))], P.QS_CAP),
            "ecm": ([dict(P.PRE["ecm"])], P.PRE_CAP), "cfrac": ([{"t": "cfrac", "kc": 32, "bc": 1.1}], P.QS_CAP),
            "qs": ([reference(bits)], P.QS_CAP)}

SUB = 8
SCR = "/tmp/claude-1000/-home-onojk123-lumens-per-watt/ddfe4e3f-7fea-48e0-ba4d-4e65f4fd682d/scratchpad"

def instructions(args):
    genome, cap, nums = args
    text = json.dumps(genome) + "\n" + str(int(cap)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    out = os.path.join(tempfile.mkdtemp(dir=SCR, prefix="ls_"), "cg.out")
    subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=no", "--dump-line=no", f"--callgrind-out-file={out}", BIN],
                   input=text, capture_output=True, text=True, check=True)
    return int(re.search(r"^summary: (\d+)", open(out).read(), re.M).group(1))

def run(genome, cap, nums):
    text = json.dumps(genome) + "\n" + str(int(cap)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    out = subprocess.run([BIN, "--types"], input=text, capture_output=True, text=True, check=True).stdout
    res = []
    for (N, p, q), l in zip(nums, out.splitlines()):
        f = l.split(); i = f.index("T")
        ty = dict(zip(optypes.TYPE_ORDER, map(int, f[i + 1:])))
        ok = f[1] != "miss" and int(f[1]) in (p, q)
        res.append((ok, ty))
    return res

if __name__ == "__main__":
    out, unweighted, rows = {}, set(), []
    for bits in SIZES:
        L = lamps(bits)
        out[bits] = {}
        for bi, lo in enumerate(BANDS):
            nums = band_numbers(bits, lo, 9700000 + 1000 * bits + bi)
            cell = {}
            for name, (g, cap) in L.items():
                r = run(g, cap, nums)
                succ = sum(ok for ok, _ in r)
                v1 = sum(V1.get(t, 0.0) * n for _, ty in r for t, n in ty.items())
                ru = sum(PR.get(t, 0.0) * n for _, ty in r for t, n in ty.items())
                unweighted |= {t for _, ty in r for t, n in ty.items() if n and t not in V1}
                cell[name] = {"success": succ, "n": len(nums), "opclass_v1": v1, "ruint": ru,
                              "light_v1": 1e6 * succ / v1 if v1 else 0.0, "light_ruint": 1e6 * succ / ru if ru else 0.0}
                rows.append((bits, lo, name, succ, len(nums), cell[name]["light_v1"], cell[name]["light_ruint"]))
            best_non = max((n for n in L if n != "qs"), key=lambda n: cell[n]["light_ruint"])
            ratio = cell[best_non]["light_ruint"] / cell["qs"]["light_ruint"] if cell["qs"]["light_ruint"] else None
            cell["_best"] = max(L, key=lambda n: cell[n]["light_ruint"]); cell["_best_non_qs"] = best_non
            cell["_twilight"] = ratio is not None and 0.4 <= ratio <= 2.5; cell["_ratio_best_non_qs_to_qs"] = ratio
            out[bits][lo] = cell
            print(f"{bits} theta {lo:.2f}-{lo + 0.02:.2f}: " + ", ".join(f"{n} {cell[n]['success']}/{PER} {cell[n]['light_ruint']:.2f}" for n in L)
                  + f"; best {cell['_best']}" + ("; TWILIGHT" if cell["_twilight"] else ""), flush=True)
    if unweighted:
        print("types without an op-class v1 weight (counted 0):", sorted(unweighted))
    # the instruction check: the first SUB numbers of each band, each lamp, callgrind, in parallel
    jobs, keys = [], []
    for bits in SIZES:
        L = lamps(bits)
        for name, (g, cap) in L.items():
            jobs.append((g, cap, [])); keys.append((bits, None, name))           # start-up
            for bi, lo in enumerate(BANDS):
                nums = band_numbers(bits, lo, 9700000 + 1000 * bits + bi)[:SUB]
                jobs.append((g, cap, nums)); keys.append((bits, lo, name))
    with Pool(6) as pool:
        irs = pool.map(instructions, jobs, chunksize=1)
    base = {(b, n): ir for (b, lo, n), ir in zip(keys, irs) if lo is None}
    for (bits, lo, name), ir in zip(keys, irs):
        if lo is None:
            continue
        g, cap = lamps(bits)[name]
        nums = band_numbers(bits, lo, 9700000 + 1000 * bits + BANDS.index(lo))[:SUB]
        v1 = sum(V1.get(t, 0.0) * n for _, ty in run(g, cap, nums) for t, n in ty.items())
        out[bits][lo][name]["check_instructions"] = ir - base[(bits, name)]
        out[bits][lo][name]["check_opclass_v1"] = v1
    for bits in SIZES:
        for name in lamps(bits):
            cells = [out[bits][lo][name] for lo in BANDS]
            pooled = sum(c["check_opclass_v1"] for c in cells) / sum(c["check_instructions"] for c in cells)
            flagged = []
            for lo, c in zip(BANDS, cells):
                r = c["check_opclass_v1"] / c["check_instructions"] if c["check_instructions"] else None
                c["check_ratio_to_pooled"] = r / pooled if r is not None else None
                if r is not None and abs(r / pooled - 1) > 0.25:
                    flagged.append(f"{lo:.2f} ({r / pooled:.2f})")
            print(f"instruction check {bits} bits {name}: op-class / instructions pooled {pooled:.3f}; bands off by > 25%: "
                  + (", ".join(flagged) if flagged else "none"), flush=True)
    json.dump({str(b): {f"{lo:.2f}": c for lo, c in d.items()} for b, d in out.items()}, open("light_spectrum.json", "w"), indent=1)
    with open("light_spectrum.csv", "w") as fh:
        fh.write("bits,theta_lo,lamp,success,n,light_v1,light_ruint\n")
        for r in rows:
            fh.write(",".join(str(x) for x in r) + "\n")
