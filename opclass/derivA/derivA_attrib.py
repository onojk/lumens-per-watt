#!/usr/bin/env python3
"""derivA: attribute each run's callgrind Ir to op classes by opclass/linemap.tsv and rules R1-R6; write weights.json.
Reads raw/<run>.cg (callgrind, --dump-instr=yes, uncompressed) and raw/<run>.stdout (lampcore-debug1 --types)."""
import json, os, re, subprocess, sys
from collections import defaultdict
import numpy as np

REPO = "/home/onojk123/lumens-per-watt"
D = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(REPO, "opclass/bin/lampcore-debug1")
MAIN_OB = BIN
SRC_TAG = "/lampcore/src/"
TYPE_ORDER = ["mult", "fb", "setup_full", "setup_euclid", "setup_small", "sieve_update", "sieve_scan",
              "confirm_full", "confirm_td", "la", "sqrt_mul", "sqrt_gcd", "lp_full", "lp_small", "check",
              "setup_mul", "setup_euclid_N", "mul", "gcd", "td_mod", "sq_ops", "ps_ops", "cfrac_ops", "word", "setup_gray",
              "hash", "sort_cmp", "f64_log", "f64_div", "root_test"]
NONOP = ["meter", "uncharged:card", "uncharged:harness", "decl"]

# ---- line map and R1 ----
cls = {}
for ln in open(os.path.join(REPO, "opclass/linemap.tsv")):
    if ln.startswith("#") or not ln.strip():
        continue
    f, a, b, c = ln.rstrip("\n").split("\t")[:4]
    f = os.path.basename(f)
    for i in range(int(a), int(b) + 1):
        assert (f, i) not in cls
        cls[(f, i)] = c
R1_PREFIX = ("m.charge(", "m.tick(", "m.test(", "m.ev(", "crate::pt_", "crate::sv_units(")
R1_LET = re.compile(r"let (pt|ps|ptl|pt_a|pt_pre) = crate::pt_snap")
r1_lines = []
for f in sorted({k[0] for k in cls}):
    for i, t in enumerate(open(os.path.join(REPO, "lampcore/src", f)), 1):
        s = t.strip()
        if s.startswith(R1_PREFIX) or R1_LET.match(s):
            if cls[(f, i)] != "meter":
                r1_lines.append((f, i, cls[(f, i)]))
            cls[(f, i)] = "meter"
assert set(cls.values()) <= set(TYPE_ORDER) | set(NONOP) | {"@caller"}, set(cls.values()) - set(TYPE_ORDER) - set(NONOP)

# ---- callgrind parsing ----
def parse_cg(path):
    """Returns: total Ir; selfc {(ob, fn): {addr_or_key: Ir}}; edges [(caller_fnkey, ob, call_addr, callee_fnkey, incl)]."""
    selfc = defaultdict(lambda: defaultdict(int))
    edges = []
    total = None
    ob = fn = cob = cfn = None
    pending_call = False
    with open(path) as fh:
        for line in fh:
            c0 = line[0]
            if c0 == "0":  # cost line "0xADDR LINE IR"
                p = line.split()
                addr = int(p[0], 16)
                ir = int(p[2])
                if pending_call:
                    edges.append(((ob, fn), ob, addr, (cob or ob, cfn), ir))
                    pending_call = False
                    cob = None
                else:
                    selfc[(ob, fn)][addr] += ir
                continue
            if line.startswith("fn="):
                fn = line[3:].rstrip("\n"); cob = None
            elif line.startswith("ob="):
                ob = line[3:].rstrip("\n")
            elif line.startswith("cob="):
                cob = line[4:].rstrip("\n")
            elif line.startswith("cfn="):
                cfn = line[4:].rstrip("\n")
            elif line.startswith("calls="):
                pending_call = True
            elif line.startswith("summary:"):
                total = int(line.split()[1])
            elif line.startswith("totals:"):
                assert int(line.split()[1]) == total
            elif c0 in "+-*" or line[:1].isdigit():
                raise ValueError("unexpected compressed position: " + line)
            elif line.startswith(("jump=", "jcnd=")):
                raise ValueError("jumps not expected")
    return total, selfc, edges

# ---- R2: inline chains ----
def addr2line_chains(addrs):
    addrs = sorted(addrs)
    out = subprocess.run(["addr2line", "-a", "-i", "-e", BIN], input="".join("0x%x\n" % a for a in addrs),
                         capture_output=True, text=True, check=True).stdout.splitlines()
    chains = {}
    cur = None
    for l in out:
        if l.startswith("0x"):
            cur = int(l, 16); chains[cur] = []
        else:
            fl = l.split(" (discriminator")[0]
            f, _, n = fl.rpartition(":")
            chains[cur].append((f, n))
    assert set(chains) == set(addrs)
    return chains

STATS = defaultdict(int)
VARIANT = os.environ.get("DERIVA_LINE0", "strict")   # "strict" (primary) or "prevrow" (sensitivity only)

def function_instrs():
    """Every instruction address of the binary, grouped by function symbol (objdump), in address order."""
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", BIN], capture_output=True, text=True, check=True).stdout
    funcs = []; cur = None
    for l in out.splitlines():
        m = re.match(r"^([0-9a-f]+) <(.*)>:$", l)
        if m:
            cur = []; funcs.append(cur); continue
        m = re.match(r"^ +([0-9a-f]+):", l)
        if m and cur is not None:
            cur.append(int(m.group(1), 16))
    return funcs

def has_unknown_line(chain):
    return any(not n.isdigit() or int(n) == 0 for f, n in chain)
def resolve(chain):
    """R2: innermost lampcore/src frame; move outward past @caller. Frames with an unknown line (?, 0) are skipped
    (they name no line). Returns (class, (file, line)) or None (no resolvable lampcore line: R3)."""
    for f, n in chain:
        if SRC_TAG not in f:
            continue
        b = os.path.basename(f)
        assert "/lampcore/src/bin/" not in f, f
        if not n.isdigit() or int(n) == 0:
            STATS["skipped_line0_frames"] += 1
            continue
        c = cls[(b, int(n))]
        if c == "@caller":
            continue
        return c, (b, int(n))
    return None

def main():
    runs = json.load(open(os.path.join(REPO, "opclass/inputs.json")))["runs"]
    parsed = {}
    for r in runs:
        parsed[r["run"]] = parse_cg(os.path.join(D, "raw", r["run"] + ".cg"))
        print("parsed", r["run"], file=sys.stderr, flush=True)
    addrs = set()
    for total, selfc, edges in parsed.values():
        for (ob, fn), d in selfc.items():
            if ob == MAIN_OB:
                addrs.update(d)
        for (g, ob, a, h, ir) in edges:
            if ob == MAIN_OB:
                addrs.add(a)
    if VARIANT == "prevrow":
        funcs = function_instrs()
        allad = {a for fn in funcs for a in fn}
        assert addrs <= allad, len(addrs - allad)
        chains = addr2line_chains(allad)
        res = {a: resolve(ch) for a, ch in chains.items()}
        nfix = 0
        for fn in funcs:     # an unresolved instruction with an unknown line takes the nearest preceding resolved row
            last = None
            for a in fn:
                if res[a] is None and last is not None and has_unknown_line(chains[a]):
                    res[a] = last; nfix += 1
                elif res[a] is not None:
                    last = res[a]
        STATS["prevrow_fixed_addresses"] = nfix
    else:
        chains = addr2line_chains(addrs)
        res = {a: resolve(ch) for a, ch in chains.items()}
    # diagnostic: addresses in main object whose line-table row has an unknown line but sit in no inline frame
    out = {"classes": {}, "runs": {}, "r1_overrides": [list(x) for x in r1_lines]}
    agg_ir = defaultdict(float); agg_ops = defaultdict(int)
    tot = defaultdict(float)
    diag_unres_lampfn = defaultdict(float)
    decl_lines = defaultdict(int); unk_unres = defaultdict(int)
    for r in runs:
        name = r["run"]; lump = r["lump"]
        total, selfc, edges = parsed[name]
        ir = defaultdict(float)
        # unresolved self cost per function (R3 input)
        fns = sorted(set(selfc) | {e[0] for e in edges} | {e[3] for e in edges})
        idx = {f: i for i, f in enumerate(fns)}
        U = np.zeros(len(fns))
        for f, d in selfc.items():
            for a, c in d.items():
                rr = res.get(a) if f[0] == MAIN_OB else None
                if rr is None:
                    U[idx[f]] += c
                    if f[0] == MAIN_OB:
                        diag_unres_lampfn[f[1]] += c
                        if any(SRC_TAG in x for x, n in chains[a]) and has_unknown_line(chains[a]):
                            unk_unres[f[1]] += c
                else:
                    ir[rr[0]] += c
                    if rr[0] == "decl":
                        decl_lines["%s:%d" % rr[1]] += c
        # R3: shares by inclusive Ir of incoming edges
        inc = defaultdict(float)
        for (g, ob, a, h, I) in edges:
            inc[h] += I
        n = len(fns)
        A = np.zeros((n, n))          # P = U + A P ; A[g, h] = share of h's pending cost passed into g's pending
        resolved_edges = []           # (h, class, share)
        assert sum(sum(d.values()) for d in selfc.values()) == total, name
        for (g, ob, a, h, I) in edges:
            if inc[h] == 0:
                continue
            s = I / inc[h]
            rr = res.get(a) if ob == MAIN_OB else None
            if rr is None:
                A[idx[g], idx[h]] += s
            else:
                resolved_edges.append((idx[h], rr[0], s))
                if rr[0] == "decl":
                    decl_lines["%s:%d (call edge)" % rr[1]] += 0  # marked; Ir added below
        P = np.linalg.solve(np.eye(n) - A, U)
        assert np.all(P >= -1e-6)
        for h, c, s in resolved_edges:
            ir[c] += s * P[h]
        if ir.get("decl"):
            decl_lines["(all decl Ir incl. edges) " + name] += ir["decl"]
        # R4: pending cost of functions with no incoming edge (roots) reaches no lampcore line
        unattr = sum(P[idx[f]] for f in fns if inc[f] == 0)
        # R5: lump runs
        if lump:
            lumped = defaultdict(float)
            for c, v in ir.items():
                lumped[c if c in ("meter", "uncharged:harness", "decl") else lump] += v
            ir = lumped
        # op counts
        ops = [0] * 30; nlines = 0
        for l in open(os.path.join(D, "raw", name + ".stdout")):
            p = l.split()
            if "T" in p:
                t = p[p.index("T") + 1:]
                assert len(t) == 30, l
                ops = [x + int(y) for x, y in zip(ops, t)]; nlines += 1
        assert nlines == r["numbers"], (name, nlines)
        opsd = {t: ops[i] for i, t in enumerate(TYPE_ORDER)}
        s = sum(ir.values()) + unattr
        rec = {"total_ir": total, "unattributed": unattr, "sum_check_diff": s - total,
               "ir": {c: ir[c] for c in sorted(ir)}, "ops": {t: v for t, v in opsd.items() if v},
               "weight": {t: ir.get(t, 0.0) / opsd[t] for t in TYPE_ORDER if opsd[t]},
               "charged_ir_without_ops": {c: v for c, v in ir.items() if c in TYPE_ORDER and opsd[c] == 0}}
        out["runs"][name] = rec
        for c, v in ir.items():
            agg_ir[c] += v
        for t, v in opsd.items():
            agg_ops[t] += v
        tot["total_ir"] += total; tot["unattributed"] += unattr
        print(name, "total", total, "sum diff", s - total, "unattr %.4f%%" % (100 * unattr / total), file=sys.stderr)
    rt = agg_ir["root_test"] / agg_ops["root_test"]
    for t in TYPE_ORDER:
        w = agg_ir[t] / agg_ops[t] if agg_ops[t] else None
        out["classes"][t] = {"ir": agg_ir[t], "ops": agg_ops[t], "weight": w, "fraction": (w / rt) if w is not None else None}
    for c in NONOP:
        tot[c] = agg_ir[c]
    tot["sum_classes_plus_rest_minus_total"] = sum(agg_ir.values()) + tot["unattributed"] - tot["total_ir"]
    out["totals"] = dict(tot)
    spread = {}
    for t in TYPE_ORDER:
        ws = {n: rec["weight"][t] for n, rec in out["runs"].items() if t in rec["weight"]}
        if ws:
            lo, hi = min(ws.values()), max(ws.values())
            spread[t] = {"runs": len(ws), "min": lo, "max": hi, "argmin": min(ws, key=ws.get), "argmax": max(ws, key=ws.get),
                         "max_over_min": hi / lo if lo else None}
    out["per_class_run_spread"] = spread
    out["variant_line0"] = VARIANT
    out["diagnostics"] = {"decl_ir_by_line": dict(decl_lines),
                          "unresolved_self_ir_with_unknown_line_in_lampcore_frames_by_function": dict(sorted(unk_unres.items(), key=lambda x: -x[1])),
                          "prevrow_fixed_addresses": STATS.get("prevrow_fixed_addresses"),"skipped_line0_frames(addresses x frames)": STATS["skipped_line0_frames"],
                          "main_object_unresolved_self_ir_by_function(top30)": dict(sorted(diag_unres_lampfn.items(), key=lambda x: -x[1])[:30])}
    json.dump(out, open(os.path.join(D, "weights.json" if VARIANT == "strict" else "weights_line0_prevrow.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
