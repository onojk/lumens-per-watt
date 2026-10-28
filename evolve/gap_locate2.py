"""Gap location, second run (the user, Oct 27 night; information only): Experiment 1's method (gap_locate.py) on the
current card (2'b + the A-prime fix + alloc-once, lampcore f6aa08d) against YAFU's tinysiqs, balanced band (80 numbers)
at 72 / 84 / 96, plus a split of confirm and lp_ledger into sub-steps.
  - The card: lampcore f6aa08d built with line tables (CARGO_PROFILE_RELEASE_DEBUG=1, Claude's scratch lc-debug2),
    stdout checked identical to the release binary's. YAFU: as Experiment 1 (c7d9028, -g, smallmpqs(@)).
  - Regions: the --phasetime spans DERIVED from qs.rs (each pt_end(m, id, var) with id < 10 paired with the nearest
    preceding `let var = crate::pt_snap(m)`); the derivation is checked to reproduce Experiment 1's hand-written spans on
    210a7d0's qs.rs. Attribution as gap_locate.card_ir (outermost qs.rs frame in a span; calls to the call site).
  - Sub-steps (anchored on code text in the current qs.rs):
      confirm: "evaluate (v, sign, lists)" | "root test" (from `// branch-free root test`) | "A-prime and even checks"
        (from `// the prime 2's low-bit test`) | "merge hit lists" (from the first-division charge) | "divide hits" (from
        `let n_pl =`) to the region's end
      lp_ledger: "cofactor check" (before lp:copy) | lp:copy | lp:add | lp:hash | lp:comb (the LPBREAK sub-region spans) |
        "lp other" (the rest of the region)
  - YAFU check_sieve_val_tiny: Ir by the innermost function of its own instructions, and its calls into libraries by
    callee (inclusive).
  - Time shares: the card's --phasetime only if Run B's conditions hold (AC among them); otherwise not measured.
  - "Change since the last gap run": against gap_locate.json (Experiment 1, the card before alloc-once).
  python3 gap_locate2.py -> gap_locate2.json, stdout;  python3 gap_locate2.py resplit: YAFU's check split again from the
  saved callgrind files (PLT stubs followed one hop to the real callee)"""
import json, os, re, statistics, subprocess, sys, tempfile
ARGV = sys.argv[1:]                                                   # before partition's import clears sys.argv
from collections import defaultdict
import partition as P, sizescale2 as S2
import gap_locate as G
from fastlamps import BIN
from baseline_msieve import conditions, cool, reference

HERE = os.path.dirname(os.path.abspath(__file__))
DBG2 = os.path.join(G.SCRATCH, "lc-debug2", "release", "lampcore")
SUFFIX = "/lc-debug2/release/lampcore"
NAMES = ["mult", "fb", "setup", "gray", "sieve", "scan", "resieve", "confirm", "lp_ledger", "solve"]

def spans_from_source(text):
    last, groups = {}, {}
    for i, l in enumerate(text.splitlines(), 1):
        m = re.search(r"let (\w+) = crate::pt_snap\(m\)", l)
        if m:
            last[m.group(1)] = i
        m = re.search(r"crate::pt_end\(m, (\d+), (\w+)\)", l)
        if m and int(m.group(1)) < 10:
            k = (int(m.group(1)), last[m.group(2)])
            groups[k] = max(groups.get(k, 0), i)
    return sorted((NAMES[id_], a, b) for (id_, a), b in groups.items())

def substeps(text, spans):
    L = text.splitlines()
    def find(s, start=0):
        hits = [i for i, l in enumerate(L, 1) if s in l and i >= start]
        assert hits, s
        return hits[0]
    (_, c0, c1), = [x for x in spans if x[0] == "confirm"]
    (_, l0, l1), = [x for x in spans if x[0] == "lp_ledger"]
    rt = find("// branch-free root test", c0) - 1
    ae = find("// the prime 2's low-bit test", c0)
    mg = find("m.charge(CONFIRM, (cnt + even as usize)", c0)
    dv = find("let n_pl =", c0)
    subs = [("confirm: evaluate (v, sign, lists)", c0, rt - 1), ("confirm: root test", rt, ae - 1),
            ("confirm: A-prime and even checks", ae, mg - 1), ("confirm: merge hit lists", mg, dv - 1),
            ("confirm: divide hits", dv, c1)]
    lp, starts = [], [(i, re.search(r'"(lp:\w+)"', l).group(1)) for i, l in enumerate(L[l0 - 1:l1], l0)
                      if re.search(r'let ptl = crate::pt_snap_lp\(m\); // "lp:\w+"', l)]
    for k, (i, name) in enumerate(starts):
        stop = starts[k + 1][0] if k + 1 < len(starts) else l1 + 1
        ends = [j for j, x in enumerate(L[i:stop - 1], i + 1) if "crate::pt_end(m, " in x and ", ptl)" in x]
        lp.append((name, i, ends[-1]))                      # to its last pt_end before the next sub-region
    first_lp = min(a for _, a, _ in lp)
    subs.append(("lp: cofactor check", l0, first_lp - 1))
    subs += [(f"lp: {n[3:]}", a, b) for n, a, b in lp]
    return subs

def sub_of(f, n, subs, spans):
    if not f.endswith("/lampcore/src/qs.rs") or not n.isdigit():
        return None, None
    n = int(n)
    reg = next((r for r, a, b in spans if a <= n <= b), None)
    if reg is None:
        return None, None
    sub = next((s for s, a, b in subs if a <= n <= b), None)
    if reg == "lp_ledger" and sub is None:
        sub = "lp: other"
    return reg, sub

def card_ir2(nums, bits, work, spans, subs):
    text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    assert subprocess.run([DBG2], input=text, capture_output=True, text=True).stdout == \
        subprocess.run([BIN], input=text, capture_output=True, text=True).stdout, "debug build output differs"
    cg = os.path.join(work, f"card{bits}.cg")
    subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=yes", "--compress-strings=no", "--compress-pos=no",
                    f"--callgrind-out-file={cg}", DBG2], input=text, capture_output=True, text=True, check=True)
    selfc, edges = G.parse_cg(cg)
    main_ob = [o for o, f in selfc if o and o.endswith(SUFFIX)][0]
    own = {a: ir for (o, f), d in selfc.items() if o == main_ob and f in G.CARD_FNS for a, ir in d.items()}
    calls = [(a, cf, ir) for o, f, a, co, cf, ir in edges if o == main_ob and f in G.CARD_FNS and cf not in G.CARD_FNS]
    ch = G.chains(DBG2, set(own) | {a for a, _, _ in calls})
    def where(a):
        c = ch[a]
        if all(not n.isdigit() or int(n) == 0 for f, n in c if f.endswith("qs.rs")):
            return "line 0", None
        for f, n in reversed(c):
            r, s = sub_of(f, n, subs, spans)
            if r:
                return r, s
        return "other (in lamp_qs / sieve_source)", None
    reg, sub, sub_calls = defaultdict(int), defaultdict(int), defaultdict(lambda: defaultdict(int))
    for a, ir in own.items():
        r, s = where(a); reg[r] += ir
        if s:
            sub[s] += ir
    for a, cf, ir in calls:
        r, s = where(a); reg[r] += ir
        if s:
            sub[s] += ir; sub_calls[s][cf] += ir
    incl = sum(ir for o, f, a, co, cf, ir in edges if cf == "lampcore::qs::lamp_qs")
    return {"Ir": dict(reg), "sub_Ir": dict(sub), "sub_calls": {k: dict(v) for k, v in sub_calls.items()},
            "lamp_qs_inclusive": incl, "attributed": sum(reg.values())}

def yafu_check_split(work):
    cg = os.path.join(work, "yafu.cg")
    selfc, edges = G.parse_cg(cg)
    main_ob = [o for o, f in selfc if o and o.endswith("/yafu")][0]
    own = {a: ir for (o, f), d in selfc.items() if o == main_ob and f == "check_sieve_val_tiny" for a, ir in d.items()}
    calls = [(a, co, cf, ir) for o, f, a, co, cf, ir in edges if o == main_ob and f == "check_sieve_val_tiny"]
    ch = G.chains(G.YAFU, set(own) | {a for a, _, _, _ in calls}, funcs=True)
    by_fn, by_callee = defaultdict(int), defaultdict(int)
    for a, ir in own.items():
        by_fn[ch[a][0][0] if ch[a] else "?"] += ir
    out_e = defaultdict(list)
    for o, f, a, co, cf, ir in edges:
        out_e[(o, f)].append((co, cf, ir))
    for a, co, cf, ir in calls:
        if cf.startswith("0x") and out_e[(co, cf)]:               # a PLT stub: follow it one hop to the real callee
            tot = sum(x[2] for x in out_e[(co, cf)]) or 1
            for co2, cf2, ir2 in out_e[(co, cf)]:
                by_callee[(os.path.basename(co2), cf2)] += ir * ir2 / tot
        else:
            by_callee[(os.path.basename(co), cf)] += ir
    return {"own_by_innermost_fn": dict(by_fn), "calls_by_callee": {f"{o}:{f}": v for (o, f), v in by_callee.items()}}

if __name__ == "__main__" and ARGV == ["resplit"]:
    # re-derive YAFU's check split from the saved callgrind files of the last run (no new runs)
    import glob
    out = json.load(open("gap_locate2.json"))
    for bits in out["sizes"]:
        work = sorted(glob.glob(os.path.join(G.SCRATCH, "gap2_*")), key=os.path.getmtime)
        work = [w for w in work if os.path.exists(os.path.join(w, f"card{bits}.cg"))][-1]
        out["sizes"][bits]["yafu_check"] = yafu_check_split(work)
    json.dump(out, open("gap_locate2.json", "w"), indent=1)
    sys.exit(0)

if __name__ == "__main__":
    cur = open(os.path.join(HERE, "..", "lampcore", "src", "qs.rs")).read()
    old = subprocess.run(["git", "show", "210a7d0:lampcore/src/qs.rs"], capture_output=True, text=True, check=True, cwd=HERE).stdout
    assert spans_from_source(old) == sorted(G.SPANS), (spans_from_source(old), sorted(G.SPANS))
    spans = spans_from_source(cur)
    subs = substeps(cur, spans)
    print("spans (derived; reproduce Experiment 1's on 210a7d0):", spans, flush=True)
    print("sub-steps:", subs, flush=True)
    timed = not conditions()
    if not timed:
        print("time shares not measured: " + "; ".join(conditions()), flush=True)
    prev = json.load(open("gap_locate.json"))
    out = {"spans": spans, "substeps": subs, "time_shares_measured": timed, "sizes": {}}
    for bits in (72, 84, 96):
        bal = S2.map_nums(bits)[-P.PER_BAND:]
        ns = None
        if timed:
            passes = []
            for r in range(3):
                cool()
                passes.append(G.card_phasetime(bal, bits))
            ns = {k: statistics.median(t.get(k, 0) for _, t in passes) for k in passes[0][1]}
        work = tempfile.mkdtemp(prefix="gap2_", dir=G.SCRATCH)
        c = card_ir2(bal, bits, work, spans, subs)
        y = G.yafu_ir(bal, work)
        ys = yafu_check_split(work)
        out["sizes"][str(bits)] = {"card": c, "yafu": y, "yafu_check": ys, "card_phasetime_ns": ns}
        print(f"{bits}: card {c['attributed'] / 80 / 1e6:.3f} M Ir per number (lamp_qs inclusive {c['lamp_qs_inclusive'] / 80 / 1e6:.3f}; "
              f"Experiment 1 {prev[str(bits)]['card']['attributed'] / 80 / 1e6:.3f}); YAFU {y['attributed'] / 80 / 1e6:.3f} M "
              f"(Experiment 1 {prev[str(bits)]['yafu']['attributed'] / 80 / 1e6:.3f})", flush=True)
    json.dump(out, open("gap_locate2.json", "w"), indent=1)
