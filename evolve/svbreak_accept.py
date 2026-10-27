"""Acceptance for the sieve sub-regions in lampcore --phasetime (NOTES.md, "Sieve breakdown"; tooling only, no charge
changes). Genomes: the reference, + goff, + goff + root, + goff + root + pp 3, + pp 10, + root + pp 10, + goff + pp 10
(pp 10 has power entries; pp 3 has none at these sizes: q < 8 admits no odd prime power and no 2^j with j >= 4).
  1. --types and every result identical to the pre-change lampcore (LAMPCORE_OLD), per number and per type, all map
     numbers 54-96.
  2. With LAMPCORE_SIEVEBREAK=1, every 8th map number per size: the sub-regions' units sum to the sieve region's
     sieve_update + sieve_scan + word; sv:zero, sv:free2, sv:prime and sv:power carry no types (the charges are in
     sv:tail); the top-level regions' types sum to the --types totals (sub-regions nest inside sieve and lp_ledger).
  3. Without it: the sub-regions have no calls and no ns; the per-region types sum to the --types totals.
  LAMPCORE_OLD=<pre-change binary> python3 svbreak_accept.py -> stdout
"""
import json, os, subprocess
import partition as P, sizescale as SS, sizescale2 as S2, optypes, fastlamps
from fastlamps import run_many
from goff_accept import nr, old_run

TO = list(optypes.TYPE_ORDER)
SV = ("sv:zero", "sv:free2", "sv:prime", "sv:power", "sv:tail")

def raw(g, nums, svb):
    text = json.dumps([g]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    env = {k: v for k, v in os.environ.items() if k not in ("LAMPCORE_LPBREAK", "LAMPCORE_SIEVEBREAK")}
    if svb:
        env["LAMPCORE_SIEVEBREAK"] = "1"
    r = subprocess.run([fastlamps.BIN, "--phasetime"], input=text, capture_output=True, text=True, check=True, env=env)
    return [json.loads(l) for l in r.stderr.splitlines()[1:]]

if __name__ == "__main__":
    c = {k: [0, 0] for k in (1, 2, 3)}
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        g0 = nr(bits)
        gs = [g0, dict(g0, goff=1), dict(g0, goff=1, confirm="root"), dict(g0, goff=1, confirm="root", pp=3),
              dict(g0, pp=10), dict(g0, confirm="root", pp=10), dict(g0, goff=1, pp=10)]
        for g in gs:
            new = run_many([g], nums, P.QS_CAP, types=True)
            for x, y in zip(new, old_run(g, nums)):
                c[1][0] += 1; c[1][1] += not (x[:4] == y[:4] and x[4] == y[4])
            sub = nums[::8]
            tot = {N: r[4] for (N, _, _), r in zip(nums, new)}
            for svb, k in ((True, 2), (False, 3)):
                for (N, _, _), d in zip(sub, raw(g, sub, svb)):
                    rg = d["regions"]
                    ty = d["types"][rg.index("sieve")]
                    summed = [sum(d["types"][i][j] for i in range(len(rg)) if ":" not in rg[i]) for j in range(len(TO))]   # top-level regions (sub-regions nest)
                    ok = all(summed[j] == tot[N].get(t, 0) for j, t in enumerate(TO))
                    if svb:
                        ok &= sum(d["sv_units"]) == sum(ty[TO.index(t)] for t in ("sieve_update", "sieve_scan", "word"))
                        ok &= not any(any(d["types"][rg.index(s)]) for s in SV[:4])
                    else:
                        ok &= all(d["calls"][rg.index(s)] == 0 and d["ns"][rg.index(s)] == 0 for s in SV)
                        ok &= not any(d["sv_units"])
                    c[k][0] += 1; c[k][1] += not ok
        print(f"{bits} bits done " + " ".join(f"{k}:{v[0] - v[1]}/{v[0]}" for k, v in c.items()), flush=True)
    names = {1: "--types and results identical to the pre-change lampcore, per number and per type",
             2: "SIEVEBREAK on: units = sieve region's sieve_update + sieve_scan + word; no types in the four walk sub-regions; regions sum to --types",
             3: "SIEVEBREAK off: sub-regions empty; regions sum to --types"}
    for k, v in c.items():
        print(f"{k}. {names[k]}: {v[0] - v[1]}/{v[0]}")
    assert not any(v[1] for v in c.values())
