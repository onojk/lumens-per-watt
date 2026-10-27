"""Builds the op-class v1 input set (reviews/opclass_procedure.md, section 4; step 2.1): opclass/inputs/<run>.in (the
lampcore protocol: genome JSON, cap, then "N p q" per number) and opclass/inputs.json (the manifest). Deterministic:
map numbers from sizescale2.map_nums, genes from the committed reference files. Run from evolve/:
  python3 ../opclass/make_inputs.py"""
import hashlib, json, os, sys
sys.path.insert(0, os.getcwd())
import partition as P, sizescale as SS, sizescale2 as S2, sizescale3 as K
from lctest import ref

OUT = "../opclass/inputs"
sealed = json.load(open("sizescale_k_sealed.json"))

def qs_ref(bits):
    return dict(ref(bits), goff=1)                       # the reference card (2'a, goff = 1; card_params)

def ref_pipeline(bits):
    bud = sealed["sizes"][str(bits)]["tracks"]["R"]["budgets"]["(d) new winner, new budgets"]   # rho, pm1 B, ecm
    return K.pipeline(qs_ref(bits), *bud)

runs = []
def add(name, genome, cap, nums, lump=None, why=""):
    text = json.dumps(genome) + "\n" + str(cap) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    open(f"{OUT}/{name}.in", "w").write(text)
    runs.append({"run": name, "genome": genome, "cap": cap, "numbers": len(nums), "lump": lump, "why": why,
                 "sha256": hashlib.sha256(text.encode()).hexdigest()})

for bits in (72, 84, 96):
    nums = S2.map_nums(bits)
    add(f"A_ref_{bits}", [qs_ref(bits)], P.QS_CAP, nums, why="qs reference (2'a), all map numbers")
    add(f"A_2b_{bits}", [dict(qs_ref(bits), confirm="root")], P.QS_CAP, nums, why="2'b, all map numbers")
for bits in (54, 72, 84, 96):
    add(f"B_pipe_{bits}", ref_pipeline(bits), P.QS_CAP, S2.map_nums(bits),
        why="reference pipeline (td, rho, p-1, ecm, qs; budgets (d)), all map numbers")
n54, n72 = S2.map_nums(54), S2.map_nums(72)
sub = lambda ns, k: ns[::max(1, len(ns) // k)][:k]       # every j-th number, spread over the bands
add("C_ecm", [dict(P.PRE["ecm"])], P.PRE_CAP, sub(n54, 48) + sub(n72, 48),
    why="ecm alone: the reference pipelines give ecm a budget of 0 (setup_mul, setup_euclid_N, and ecm's mul / gcd / word)")
add("C_pm1s2", [{"t": "pm1", "b": 0.2, "B": 2048, "c": 20}], P.PRE_CAP, sub(n54, 48) + sub(n72, 48),
    why="p-1 with stage 2 (gene c): the reference pipelines run stage 1 only")
add("C_sq", [{"t": "sq", "mode": "seqm", "mult": 60, "k": 0.3, "w": 0.25, "c": 1.2, "ksq": False, "r": 64}], P.PRE_CAP,
    sub(n54, 48), lump="sq_ops", why="sq (parity's genome): no reference pipeline runs it")
add("C_ps", [{"t": "ps", "a": 0.5, "s": 0.25, "c": 1.0}], P.PRE_CAP, sub(n54, 48), lump="ps_ops",
    why="ps (parity's genome): no reference pipeline runs it")
add("C_cfrac", [{"t": "cfrac", "kc": 32, "bc": 1.1}], P.QS_CAP, sub(n54, 24), lump="cfrac_ops",
    why="cfrac (parity's genome): no reference pipeline runs it")
add("C_td", [dict(P.PRE["td"])], P.PRE_CAP, sub(n54, 16),
    why="td alone: the reference pipelines give td a budget of 0 (td_mod)")
add("C_check", [dict(qs_ref(72), check=1)], P.QS_CAP, sub(n72, 48),
    why="the ledger check (gene check, off by default): no reference run charges it")
json.dump({"runs": runs, "note": "op-class v1 input set; committed before any count (step 2.1)"},
          open("../opclass/inputs.json", "w"), indent=1)
for r in runs:
    print(r["run"], r["numbers"], r["lump"] or "", r["sha256"][:12])
