"""Cost note input for the allocation change (the user's go-ahead, Oct 27 late): allocation Ir (malloc, free, realloc,
calloc, inclusive through the Rust allocator wrappers, callee-wide fractions) per call site in lamp_qs / sieve_source,
from Experiment 1's callgrind files (gap_locate.py, balanced band, 80 numbers; lampcore at 210a7d0, qs.rs line numbers
of that commit). The change targets these sites (qs.rs):
  653 OnDemand::new (every (s-1)-combination of the pool its own Vec)      1314 its drop at the attempt's end
  763 OnDemand::next (per prefix: the prefix clone, the rest list, per try the key)
  776 aj, 804 bl64, 798 sbi, 817 bainv per prime, 823 vec![r1, r2] per prime, 825-827 / 829 sp, sj, sr, sbi pushes,
  831-832 their drops, 833-835 the power-entry arrays (per A)
  python3 alloc_estimate.py -> alloc_estimate.json, stdout"""
import glob, json, os
from collections import defaultdict
import gap_locate as G

TARGET = {653, 1314, 763, 776, 798, 804, 817, 823, 825, 826, 827, 829, 831, 832, 833, 834, 835}
ALLOCF = ("malloc", "free", "realloc", "calloc", "cfree")

def sites(cg):
    selfc, edges = G.parse_cg(cg)
    main = [o for o, f in selfc if o and o.endswith("/lc-debug1/release/lampcore")][0]
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
            if co != main and cf.split("@")[0] in ALLOCF:
                s += ir
            elif (co, cf) != key and depth < 40:
                s += ir * alloc((co, cf), depth + 1) / (incl[(co, cf)] or 1)
        memo[key] = s
        return s
    per = defaultdict(float)
    calls = [(a, co, cf, ir) for o, f, a, co, cf, ir in edges if o == main and f in G.CARD_FNS and cf not in G.CARD_FNS]
    ch = G.chains(G.DBG, {a for a, _, _, _ in calls})
    for a, co, cf, ir in calls:
        v = ir if (co != main and cf.split("@")[0] in ALLOCF) else ir * alloc((co, cf)) / (incl[(co, cf)] or 1)
        if v:
            qs = [int(n) for fl, n in ch[a] if fl.endswith("qs.rs") and n.isdigit() and int(n) > 0]
            per[qs[-1] if qs else 0] += v
    return per

if __name__ == "__main__":
    out = {}
    for bits in (72, 84, 96):
        cg = sorted(glob.glob(os.path.join(G.SCRATCH, "gap_*", f"card{bits}.cg")), key=os.path.getmtime)[-1]
        per = sites(cg)
        tot = sum(per.values()) / 80; tgt = sum(v for l, v in per.items() if l in TARGET) / 80
        out[bits] = {"alloc_total_per_number": tot, "alloc_targeted_per_number": tgt,
                     "by_line_per_number": {str(l): v / 80 for l, v in sorted(per.items(), key=lambda kv: -kv[1])}}
        print(f"{bits} bits: allocation Ir per number {tot / 1e3:,.0f} k; at the targeted sites {tgt / 1e3:,.0f} k "
              f"({100 * tgt / tot:.0f}%); left (per attempt: Ledger, partials, the attempt's arrays) {(tot - tgt) / 1e3:,.0f} k")
    json.dump(out, open("alloc_estimate.json", "w"), indent=1)
