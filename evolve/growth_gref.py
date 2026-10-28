"""Growth fitness G: the reference's doubling periods for freezing (the user's ruling, Oct 28; reviews/growth_fitness.md).
  80-96 chord (primary): from the committed growth_counts.json (sealed run 68250b3); QS at 80 on interpolated genes.
  84-96 chord (gene check: both ends on sealed reference genes): QS alone at 84 bits on 48 fresh balanced semiprimes,
          semiprimes_pq(84, 48, 9600084) (the harness's seed rule), lampcore --types, untimed; 96 from growth_counts.json.
Doubling period = (b - a) / log2(C(b) / C(a)), C = total priced cost / successes (growth_harness.per_fact), per pricing.
Bootstrap: 10,000 resamples of the numbers within each size, random.Random(2026), 2.5-97.5%.
  python3 growth_gref.py -> growth_gref.json, stdout"""
import sys
sys.argv = sys.argv[:1]
import json, math, random
import partition as P
import growth_harness as H
from fastlamps import semiprimes_pq

PRICINGS = ("opclass_v1", "ruint", "montgomery", "official")

data = json.load(open("growth_counts.json"))
rows = {80: data["80"]["qs"], 96: data["96"]["qs"]}
res, dt = H.run([H.qs_genes(84)], P.QS_CAP, semiprimes_pq(84, H.PER, 9600000 + 84))
for r in res:
    r["cost"] = H.costs(r["types"])
rows[84] = res
print(f"84 bits qs: {sum(r['ok'] for r in res)}/{H.PER} succeeded; genes {H.qs_genes(84)}; ({dt:.1f} s, untimed)")

def period(rs, pr, a, b):
    ca, cb = H.per_fact(rs[a], pr), H.per_fact(rs[b], pr)
    return (b - a) / math.log2(cb / ca) if ca and cb else None

out = {"qs_84": res}
for a in (80, 84):
    rng = random.Random(2026)
    for pr in PRICINGS:
        p = period(rows, pr, a, 96)
        bs = sorted(x for x in (period({b: [rows[b][rng.randrange(len(rows[b]))] for _ in rows[b]] for b in (a, 96)}, pr, a, 96)
                                for _ in range(10000)) if x)
        ci = (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1])
        out[f"{a}-96 {pr}"] = {"period": p, "ci": ci}
        print(f"QS doubling period {a}-96 [{pr}]: {p:.2f} bits [{ci[0]:.2f}, {ci[1]:.2f}]")
for pr in PRICINGS:
    x, y = out[f"80-96 {pr}"], out[f"84-96 {pr}"]
    agree = not (x["ci"][1] < y["ci"][0] or y["ci"][1] < x["ci"][0])
    print(f"gene check [{pr}]: intervals {'overlap' if agree else 'DISAGREE (flag)'}")
json.dump(out, open("growth_gref.json", "w"))
