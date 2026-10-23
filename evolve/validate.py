"""Re-test baselines and each run's champion on fresh, larger semiprimes,
then project where the block flash would overtake Lehman."""
import json, math, sys
from lamps import measure, measure_cumulative, semiprimes, describe
from evolve import BASELINES

# python3 validate.py            Run 2 (worst-case), files in this folder
# python3 validate.py run3       Run 3 (cumulative), files in run3/
RUN = sys.argv[1] if len(sys.argv) > 1 else ""
DIR = RUN + "/" if RUN else ""
METER = measure_cumulative if RUN == "run3" else measure

VSIZES = [36, 42, 48, 54]
TESTS = {b: semiprimes(b, 12, 777000 + b) for b in VSIZES}

def fit_offset(ys, exponent, log_power):
    """Fit log2(ops) = exponent*bits + log_power*log2(bits) + c; return c."""
    return sum(y - exponent * b - log_power * math.log2(b) for b, y in ys.items()) / len(ys)

def crossover(ps_ys, other_ys, other_exp):
    c_ps = fit_offset(ps_ys, 0.25, 2)
    c_o = fit_offset(other_ys, other_exp, 0)
    for bits in range(54, 2000):
        if 0.25 * bits + 2 * math.log2(bits) + c_ps < other_exp * bits + c_o:
            return bits
    return None

if __name__ == "__main__":
    res = json.load(open(DIR + "results.json"))
    cands = dict(BASELINES)
    for key, hist in res["runs"].items():
        cands[f"champion {key}"] = hist[-1]["champ"]
    out = {}
    for name, g in cands.items():
        r = METER(g, TESTS)
        r["genome"] = g
        out[name] = r
        if RUN == "run3":
            r["ys"] = r["worst"]
            print(f"{name:22s} N^{r['score']:.3f}  lumens/watt N^{0.5-r['score']:.3f}  "
                  f"misses {r['fails']}  "
                  f"mean log2 ops {[round(r['cum'][b], 1) for b in VSIZES if b in r['cum']]}  "
                  f"worst {[round(r['worst'][b], 1) for b in VSIZES if b in r['worst']]}", flush=True)
            r.pop("per_n", None)
        else:
            ys = r["ys"]
            trend = f"N^{r['trend']:.3f}" if r["trend"] is not None else "—"
            print(f"{name:22s} N^{r['score']:.3f}  lumens/watt N^{0.5-r['score']:.3f}  "
                  f"trend {trend}  misses {r['fails']}  "
                  f"worst log2 ops {[round(ys[b], 1) for b in VSIZES if b in ys]}", flush=True)
        if name.startswith("champion"):
            print(f"{'':22s} {describe(g)}", flush=True)
    ps = out["pollard-strassen"]["ys"]
    out["projection"] = {
        "ps_overtakes_lehman_bits": crossover(ps, out["lehman"]["ys"], 1 / 3),
        "ps_overtakes_trial_bits": crossover(ps, out["trial division"]["ys"], 1 / 2),
    }
    print("projection (model: block flash ~ N^(1/4) log^2 N):", out["projection"])
    json.dump(out, open(DIR + "validation.json", "w"), indent=1, default=str)
