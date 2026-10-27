"""Attribution-free check (the user, Oct 27; computation only): total Ir per number for 2'a and 2'b on the same inputs
(op-class v1 step 2 callgrind runs A_ref_* / A_2b_*, derivation B's per-run breakdown, opclass/derivB/weights.json),
split into charged classes, meter, uncharged (card + harness) and unattributed (+ decl), against step 3's op-class ratio.
  python3 irtotal_2b.py (from the repo root) -> stdout, evolve/irtotal_2b.json"""
import json, sys
sys.path.insert(0, "evolve")
from optypes import TYPE_ORDER
B = json.load(open("opclass/derivB/weights.json"))["per_run"]
man = {r["run"]: r["numbers"] for r in json.load(open("opclass/inputs.json"))["runs"]}
s3 = json.load(open("evolve/step3.json"))["sizes"]
rows = []
for bits in (72, 84, 96):
    out = {}
    for cell in ("ref", "2b"):
        r = B[f"A_{cell}_{bits}"]; ir = r["ir"]; n = man[f"A_{cell}_{bits}"]
        att = sum(ir.get(t, 0) for t in TYPE_ORDER)
        unc = ir.get("uncharged:card", 0) + ir.get("uncharged:harness", 0)
        una = ir.get("unattributed", 0) + ir.get("decl", 0)
        met = ir.get("meter", 0); tot = r["total_ir"]
        assert abs(att + unc + una + met - tot) < 1
        out[cell] = dict(n=n, tot=tot / n, att=att / n, unc=unc / n, una=una / n, met=met / n)
    a, b = out["ref"], out["2b"]
    oc = s3[str(bits)]["2'b"]["ratios"]["opclass"]["ratio"]
    rows.append({"bits": bits, "2a": a, "2b": b, "opclass_ratio": oc})
    print(f"{bits}: total 2'a {a['tot']:,.0f} / 2'b {b['tot']:,.0f} Ir per number, ratio {b['tot'] / a['tot']:.4f} (op-class {oc:.4f}); "
          f"charged {b['att'] / a['att']:.4f}; meter {b['met'] / a['met']:.4f}; uncharged {a['unc']:,.0f} -> {b['unc']:,.0f} ({b['unc'] / a['unc']:.4f}; "
          f"share {100 * a['unc'] / a['tot']:.2f}% -> {100 * b['unc'] / b['tot']:.2f}%); unattributed {a['una']:,.0f} -> {b['una']:,.0f}")
json.dump(rows, open("evolve/irtotal_2b.json", "w"), indent=1)
