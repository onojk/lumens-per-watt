"""Information only (user, Oct 25; no card change): per size, for the new reference genes (final Track R
genes as qs alone, corrected card with kset sf32):
  - the share of qs cost spent on candidate confirmation (confirm_full: the v evaluation, 2 per candidate;
    confirm_td: the F-prime trial-division pass and repeats), per pricing; lampcore --types on all map numbers;
  - per confirmed candidate, the mean number of factor-base primes that divide v (and divisions incl.
    repeats), and the share of candidates that are smooth or partial; Python traces on 4 balanced and
    4 band-24 map numbers per size.
  python3 confirmshare.py -> confirmshare.out (stdout)
"""
import json, math
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
from ledger import Charger, Ledger
from fastlamps import run_many
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
for bits in SS.SIZES:
    g = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    nums = S2.map_nums(bits)
    rows = SS.corrected_map_rows(bits)
    rs = run_many([g], nums, P.QS_CAP, types=True)
    tot = {t: sum(x[4][t] for x in rs) for t in optypes.TYPE_ORDER}
    tot = {t: v for t, v in tot.items() if v}
    conf = ("confirm_full", "confirm_td")
    sh = {"official": sum(tot.get(t, 0) for t in conf) / sum(tot.values())}
    for Pn in ("ruint", "montgomery"):
        sh[Pn] = sum(PR[Pn][t] * tot.get(t, 0) for t in conf) / P.cost_of(tot, PR[Pn])
    td_sh = {"official": tot.get("confirm_td", 0) / sum(tot.values())}
    for Pn in ("ruint", "montgomery"):
        td_sh[Pn] = PR[Pn]["confirm_td"] * tot.get("confirm_td", 0) / P.cost_of(tot, PR[Pn])
    top = max(r["band"] for r in rows)
    sample = [t for t, r in zip(nums, rows) if r["band"] == top][:4] + [t for t, r in zip(nums, rows) if r["band"] == 24][:4]
    ncand = ndiv = nrep = 0; Fs = []
    for N, _, _ in sample:
        qs.TRACE = {}
        m = lamps.Meter(P.QS_CAP)
        try:
            qs.lamp_qs(N, g, m)
        except lamps.Budget:
            pass
        tr = qs.TRACE; qs.TRACE = None
        lnN = math.log(N); B = max(30, int(g["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
        for at in tr["attempts"]:
            led = Ledger(N, at["k"], B, Charger(lamps.Meter(1 << 60), None), None)
            led.build_base()
            base = led.base
            Fs.append(len(base))
            for v in at["cands"]:
                v = abs(v)
                if v == 0:
                    continue
                ncand += 1
                for p in base[1:]:
                    if v % p == 0:
                        ndiv += 1
                        v //= p
                        while v % p == 0:
                            v //= p; nrep += 1
    print(f"{bits} bits: confirmation share of qs cost (official / ruint / Montgomery) "
          + " / ".join(f"{sh[Pn]:.3f}" for Pn in sh) + "; of which the trial-division pass (confirm_td) "
          + " / ".join(f"{td_sh[Pn]:.3f}" for Pn in td_sh)
          + f"; per candidate: F {sum(Fs) / len(Fs):.0f}, primes dividing v {ndiv / ncand:.2f}, repeat divisions {nrep / ncand:.2f} ({ncand} candidates, {len(sample)} numbers)", flush=True)
