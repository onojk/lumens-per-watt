#!/usr/bin/env python3
"""derivB: attribute callgrind Ir to op classes by opclass/linemap.tsv rules R1-R6; write weights.json.

Usage: python3 derivB_attr.py            (all runs in inputs.json that have raw/<run>.done)
"""
import json, os, re, subprocess, sys
from collections import defaultdict

REPO = "/home/onojk123/lumens-per-watt"
BIN = f"{REPO}/opclass/bin/lampcore-debug1"
REL = f"{REPO}/opclass/bin/lampcore-release"
SRC = f"{REPO}/lampcore/src/"
D = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(D, "raw")
TYPE_ORDER = ["mult", "fb", "setup_full", "setup_euclid", "setup_small", "sieve_update", "sieve_scan",
              "confirm_full", "confirm_td", "la", "sqrt_mul", "sqrt_gcd", "lp_full", "lp_small", "check",
              "setup_mul", "setup_euclid_N", "mul", "gcd", "td_mod", "sq_ops", "ps_ops", "cfrac_ops", "word",
              "setup_gray", "hash", "sort_cmp", "f64_log", "f64_div", "root_test"]
NONCLASS = ["meter", "uncharged:card", "uncharged:harness", "decl", "unattributed"]
MAPFILES = {"cfrac.rs", "ecm.rs", "main.rs", "qs.rs", "race.rs"}

# ---------------- the line map + R1 ----------------
linecls = {}
for ln in open(f"{REPO}/opclass/linemap.tsv"):
    if ln.startswith("#") or not ln.strip():
        continue
    f, a, b, c = ln.rstrip("\n").split("\t")[:4]
    f = os.path.basename(f)
    for i in range(int(a), int(b) + 1):
        assert (f, i) not in linecls
        linecls[(f, i)] = c
R1_PREFIX = ("m.charge(", "m.tick(", "m.test(", "m.ev(", "crate::pt_", "crate::sv_units(")
R1_LET = re.compile(r"^let (pt|ps|ptl|pt_a|pt_pre) = crate::pt_snap")
r1_lines = set()
for f in MAPFILES:
    for i, t in enumerate(open(SRC + f).read().split("\n"), 1):
        s = t.strip()
        if s.startswith(R1_PREFIX) or R1_LET.match(s):
            r1_lines.add((f, i))
            linecls[(f, i)] = "meter"
        assert (f, i) in linecls or i == len(open(SRC + f).read().split("\n")), (f, i)

# ---------------- R2: inline chains ----------------
a2l_cache = {}
stats = defaultdict(int)


def resolve_addrs(addrs):
    addrs = [a for a in addrs if a not in a2l_cache]
    if not addrs:
        return
    inp = "".join(f"0x{a:x}\n" for a in addrs)
    out = subprocess.run(["addr2line", "-i", "-a", "-e", BIN], input=inp, capture_output=True, text=True).stdout
    cur = None
    for ln in out.split("\n"):
        if ln.startswith("0x") and ":" not in ln:
            cur = int(ln, 16)
            a2l_cache[cur] = []
        elif ln:
            path, _, line = ln.rpartition(":")
            line = line.split(" ")[0]
            a2l_cache[cur].append((path, int(line) if line.isdigit() else 0))
    for a in addrs:
        assert a in a2l_cache


LINE0 = os.environ.get("LINE0", "literal")  # "literal" (primary) or "prev" (sensitivity variant)
_prev = None


def prev_map():
    """For the 'prev' variant: per instruction address, the previous instruction address in the same symbol."""
    global _prev
    if _prev is None:
        _prev = {}
        last = None
        for ln in open(os.path.join(D, "objdump.txt")):
            m = re.match(r"^([0-9a-f]+) <", ln)
            if m:
                last = None
                continue
            m = re.match(r"^\s+([0-9a-f]+):", ln)
            if m:
                a = int(m.group(1), 16)
                _prev[a] = last
                last = a
    return _prev


def classify(addr, _depth=0):
    if LINE0 == "prev" and _depth == 0:
        ch = [(p, l) for p, l in a2l_cache[addr] if p.startswith(SRC)]
        if ch and all(l == 0 for p, l in ch):
            pm = prev_map()
            a = pm.get(addr)
            while a is not None:
                if a not in a2l_cache:
                    resolve_addrs([a])
                ch2 = [(p, l) for p, l in a2l_cache[a] if p.startswith(SRC)]
                if ch2 and not all(l == 0 for p, l in ch2):
                    return classify(a, 1)
                a = pm.get(a)
    return classify0(addr)


def classify0(addr):
    """R2: innermost lampcore/src frame with a mapped class other than @caller -> (file, line, class) or None.
    Returns also a flag if a lampcore frame with line 0 was skipped."""
    zero = False
    for path, line in a2l_cache[addr]:
        if not path.startswith(SRC):
            continue
        f = path[len(SRC):]
        if f not in MAPFILES:
            raise SystemExit(f"frame in unmapped lampcore file {path}")
        if line == 0:
            zero = True
            continue
        c = linecls[(f, line)]
        if c == "@caller":
            continue
        return (f, line, c), zero
    return None, zero


# ---------------- callgrind parsing ----------------
def parse_cg(path):
    selfc = defaultdict(lambda: defaultdict(int))  # node -> addr -> Ir
    edges = []  # (caller node, call addr, callee node, inclusive Ir)
    ob = fn = None
    cob = cfn = None
    pending_call = False
    summary = None
    totals = 0
    with open(path) as fh:
        for ln in fh:
            if pending_call:
                p = ln.split()
                edges.append(((ob, fn), int(p[0], 16), (cob or ob, cfn), int(p[2])))
                pending_call = False
                cob = cfn = None
                continue
            c0 = ln[0]
            if c0 == "0":
                p = ln.split()
                v = int(p[2])
                selfc[(ob, fn)][int(p[0], 16)] += v
                totals += v
            elif ln.startswith("ob="):
                ob = ln[3:].rstrip("\n")
            elif ln.startswith("fn="):
                fn = ln[3:].rstrip("\n"); cob = cfn = None
            elif ln.startswith("cob="):
                cob = ln[4:].rstrip("\n")
            elif ln.startswith("cfn="):
                cfn = ln[4:].rstrip("\n")
            elif ln.startswith("calls="):
                pending_call = True
            elif ln.startswith("summary:"):
                summary = int(ln.split()[1])
            elif ln.startswith(("fl=", "fi=", "fe=", "cfi=", "cfl=", "#", "version", "creator", "pid", "cmd", "part",
                                "desc", "positions", "events", "totals")) or not ln.strip():
                pass
            elif ln[0] in "123456789+-*":
                raise SystemExit(f"unexpected line {ln!r}")
    assert summary == totals, (summary, totals)
    return selfc, edges, summary


def attribute(run, lump):
    selfc, edges, total = parse_cg(os.path.join(RAW, run + ".cg"))
    mainobs = {n[0] for n in selfc if n[0] and n[0].endswith("/lampcore-debug1")}
    assert mainobs == {BIN}, mainobs
    addrs = set()
    for (o, f), d in selfc.items():
        if o == BIN:
            addrs.update(d)
    for (o, f), a, _, _ in edges:
        if o == BIN:
            addrs.add(a)
    resolve_addrs(sorted(addrs))
    cls = defaultdict(float)
    lines = defaultdict(float)
    zero_ir = 0
    line0_unres = defaultdict(int)  # Ir of instructions in lampcore code whose every lampcore frame has line 0
    U = defaultdict(float)  # unresolved pool per node
    for node, d in selfc.items():
        for a, v in d.items():
            r = None
            if node[0] == BIN:
                r, z = classify(a)
                if z and r is not None:
                    zero_ir += v
            if r is None:
                U[node] += v
                if node[0] == BIN and any(p.startswith(SRC) and l == 0 for p, l in a2l_cache[a]):
                    line0_unres[node[1]] += v
            else:
                cls[r[2]] += v
                lines[(r[0], r[1])] += v
    # R3: edges. The target of each edge's share: a resolved line, or the caller node's pool.
    into = defaultdict(list)
    for cnode, a, callee, incl in edges:
        r = classify(a)[0] if cnode[0] == BIN else None
        if r is None and cnode == callee:
            continue  # self-recursive edge inside an unresolved node: its share stays in the same pool
        into[callee].append((incl, r, cnode))
    shares = {}
    for h, lst in into.items():
        den = sum(x[0] for x in lst)
        shares[h] = [(x[0] / den, x[1], x[2]) for x in lst] if den > 0 else []
    resid = dict(U)
    unattr = 0.0
    r3_to_class = defaultdict(float)
    it = 0
    while resid:
        it += 1
        nxt = defaultdict(float)
        for h, mass in resid.items():
            sh = shares.get(h)
            if not sh:
                unattr += mass  # R4: reaches no lampcore line
                continue
            for s, r, cnode in sh:
                if r is not None:
                    cls[r[2]] += s * mass
                    lines[(r[0], r[1])] += s * mass
                    r3_to_class[r[2]] += s * mass
                else:
                    nxt[cnode] += s * mass
        resid = {k: v for k, v in nxt.items() if v > 1e-9}
        lost = sum(v for v in nxt.values() if v <= 1e-9)
        unattr += lost  # negligible tail of cycles (< 1e-9 Ir per node), kept for conservation
        if it > 100000:
            raise SystemExit("no convergence")
    cls["unattributed"] += unattr
    # R5
    if lump:
        for c in list(cls):
            if c not in ("meter", "uncharged:harness", "decl", "unattributed", lump):
                cls[lump] += cls.pop(c)
    decl_lines = {f"{f}:{l}": v for (f, l), v in lines.items() if linecls[(f, l)] == "decl" and v > 0}
    return dict(cls), total, zero_ir, decl_lines, it, dict(r3_to_class), dict(line0_unres)


def read_types(path):
    tot = [0] * 30
    nl = 0
    for ln in open(path):
        p = ln.split()
        i = p.index("T")
        v = [int(x) for x in p[i + 1:]]
        assert len(v) == 30
        tot = [a + b for a, b in zip(tot, v)]
        nl += 1
    return dict(zip(TYPE_ORDER, tot)), nl


def main():
    runs = json.load(open(f"{REPO}/opclass/inputs.json"))["runs"]
    out = {"per_run": {}}
    IR = defaultdict(float)
    OPS = defaultdict(int)
    grand = 0
    for r in runs:
        name = r["run"]
        if not os.path.exists(os.path.join(RAW, name + ".done")):
            print("missing", name); continue
        ops, nl = read_types(os.path.join(RAW, name + ".stdout"))
        assert nl == r["numbers"], (name, nl)
        rel = subprocess.run([REL, "--types"], stdin=open(f"{REPO}/opclass/inputs/{name}.in"), capture_output=True,
                             text=True).stdout
        same = rel == open(os.path.join(RAW, name + ".stdout")).read()
        cls, total, zero_ir, decl_lines, it, r3, l0u = attribute(name, r["lump"])
        s = sum(cls.values())
        rec = {"total_ir": total, "sum_attributed": s, "sum_minus_total": s - total,
               "stdout_equals_release": same, "ir": {k: cls.get(k, 0.0) for k in TYPE_ORDER + NONCLASS},
               "ops": ops, "r3_ir_by_class": r3, "decl_lines_ir": decl_lines, "line0_skipped_ir": zero_ir,
               "r3_iterations": it, "line0_unresolved_ir_by_fn": l0u, "lump": r["lump"]}
        rec["weight"] = {k: (rec["ir"][k] / ops[k] if ops[k] else None) for k in TYPE_ORDER}
        rec["ir_without_ops"] = {k: rec["ir"][k] for k in TYPE_ORDER if ops[k] == 0 and rec["ir"][k] > 0}
        out["per_run"][name] = rec
        for k, v in cls.items():
            IR[k] += v
        for k, v in ops.items():
            OPS[k] += v
        grand += total
        print(f"{name}: total {total} sum-total {s - total:.6f} stdout==release {same} decl {sum(decl_lines.values()):.1f}"
              f" unattr {cls.get('unattributed', 0):.0f} line0 {zero_ir}", flush=True)
    rw = IR["root_test"] / OPS["root_test"] if OPS["root_test"] else None
    out["classes"] = {}
    for k in TYPE_ORDER:
        w = IR[k] / OPS[k] if OPS[k] else None
        ws = [v["weight"][k] for v in out["per_run"].values() if v["weight"][k] is not None]
        out["classes"][k] = {"ir": IR[k], "ops": OPS[k], "weight": w, "fraction": (w / rw if w is not None and rw else None),
                             "runs_with_ops": len(ws), "weight_min_run": min(ws) if ws else None,
                             "weight_max_run": max(ws) if ws else None}
    out["totals"] = {k: IR[k] for k in NONCLASS}
    out["total_ir"] = grand
    out["sum_attributed"] = sum(IR.values())
    out["sum_minus_total"] = out["sum_attributed"] - grand
    out["line0_rule"] = LINE0
    json.dump(out, open(os.path.join(D, "weights.json" if LINE0 == "literal" else f"weights_line0_{LINE0}.json"), "w"), indent=1)
    print(f"total {grand} sum-total {out['sum_minus_total']:.6f}")
    for k in TYPE_ORDER:
        c = out["classes"][k]
        if c["ops"]:
            print(f"{k:15s} {c['ir']:16.0f} {c['ops']:14d} {c['weight']:10.3f} {c['fraction']:8.4f}  "
                  f"[{c['weight_min_run']:.3f}, {c['weight_max_run']:.3f}] n={c['runs_with_ops']}")
        else:
            print(f"{k:15s} {c['ir']:16.0f} {c['ops']:14d}")
    for k in NONCLASS:
        print(f"{k:18s} {IR[k]:16.0f} {100 * IR[k] / grand:.3f}%")


if __name__ == "__main__":
    main()
