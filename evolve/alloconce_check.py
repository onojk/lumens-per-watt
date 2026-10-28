"""The cost note's check (after code, before timing; information): allocator instructions and all instructions per
number, before (Experiment 1's callgrind files, lampcore with the A-prime fix) and after (this commit's source built
with line tables, CARGO_PROFILE_RELEASE_DEBUG=1, in Claude's scratch lc-debug2), on the same balanced bands (80 numbers)
at 72 / 84 / 96, the reference genes; stdout of the after build checked identical to the release binary's.
  python3 alloconce_check.py -> alloconce_check.json, stdout"""
import glob, json, os, subprocess, tempfile
import partition as P, sizescale2 as S2
import gap_locate as G, alloc_estimate as A
from fastlamps import BIN
from baseline_msieve import reference

DBG2 = os.path.join(G.SCRATCH, "lc-debug2", "release", "lampcore")

def measure(cg, dbg, suffix):
    selfc, edges = G.parse_cg(cg)
    incl = sum(ir for o, f, a, co, cf, ir in edges if cf == "lampcore::qs::lamp_qs")
    per = sites_for(cg, dbg, suffix)
    return incl / 80, sum(per.values()) / 80

def sites_for(cg, dbg, suffix):
    from collections import defaultdict
    selfc, edges = G.parse_cg(cg)
    main = [o for o, f in selfc if o and o.endswith(suffix)][0]
    out_e = defaultdict(list); incl = defaultdict(int)
    for o, f, a, co, cf, ir in edges:
        out_e[(o, f)].append((co, cf, ir)); incl[(co, cf)] += ir
    memo = {}
    def alloc(key, depth=0):
        if key in memo:
            return memo[key]
        memo[key] = 0.0
        s = 0.0
        for co, cf, ir in out_e[key]:
            if co != main and cf.split("@")[0] in A.ALLOCF:
                s += ir
            elif (co, cf) != key and depth < 40:
                s += ir * alloc((co, cf), depth + 1) / (incl[(co, cf)] or 1)
        memo[key] = s
        return s
    per = defaultdict(float)
    for o, f, a, co, cf, ir in edges:
        if o == main and f in G.CARD_FNS and cf not in G.CARD_FNS:
            v = ir if (co != main and cf.split("@")[0] in A.ALLOCF) else ir * alloc((co, cf)) / (incl[(co, cf)] or 1)
            if v:
                per[a] += v
    return per

if __name__ == "__main__":
    out = {}
    for bits in (72, 84, 96):
        bal = S2.map_nums(bits)[-P.PER_BAND:]
        text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in bal)
        assert subprocess.run([DBG2], input=text, capture_output=True, text=True).stdout == \
            subprocess.run([BIN], input=text, capture_output=True, text=True).stdout
        work = tempfile.mkdtemp(prefix="aoc_", dir=G.SCRATCH)
        cg2 = os.path.join(work, f"card{bits}.cg")
        subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=yes", "--compress-strings=no", "--compress-pos=no",
                        f"--callgrind-out-file={cg2}", DBG2], input=text, capture_output=True, text=True, check=True)
        cg1 = sorted(glob.glob(os.path.join(G.SCRATCH, "gap_*", f"card{bits}.cg")), key=os.path.getmtime)[-1]
        b_incl, b_alloc = measure(cg1, G.DBG, "/lc-debug1/release/lampcore")
        a_incl, a_alloc = measure(cg2, DBG2, "/lc-debug2/release/lampcore")
        out[bits] = {"before": {"Ir": b_incl, "alloc_Ir": b_alloc}, "after": {"Ir": a_incl, "alloc_Ir": a_alloc}}
        print(f"{bits} bits: instructions per number {b_incl / 1e6:.3f} M -> {a_incl / 1e6:.3f} M ({100 * (a_incl / b_incl - 1):+.1f}%); "
              f"allocator {b_alloc / 1e6:.3f} M -> {a_alloc / 1e6:.3f} M (removed {(b_alloc - a_alloc) / 1e6:.3f} M; "
              f"the cost note's estimate at the targeted sites {json.load(open('alloc_estimate.json'))[str(bits)]['alloc_targeted_per_number'] / 1e6:.3f} M); "
              f"all instructions removed {(b_incl - a_incl) / 1e6:.3f} M", flush=True)
    json.dump(out, open("alloconce_check.json", "w"), indent=1)
