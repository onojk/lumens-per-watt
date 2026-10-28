"""Experiment 1, locate the gap (the user, Oct 27 late; information only): the card's --phasetime regions against YAFU's
tinysiqs by function, on the balanced band (the last band of 80) at 72 / 84 / 96. Inputs and binaries:
  - the card: the reference genes (2'b), lampcore built from this commit's source with line tables
    (CARGO_PROFILE_RELEASE_DEBUG=1 cargo build --release --locked --target-dir <scratch>/lc-debug1); its stdout is checked
    identical to the release binary's on the same numbers. Timed shares: the release binary with --phasetime.
  - YAFU: the user's build (c7d9028, -g), "smallmpqs(@)" (tinysiqs directly), batch on stdin, one thread.
  1. Time shares (timed; Run B's conditions, else nothing is timed): the card's --phasetime ns per region summed over the
     80 numbers, median of 3 passes, pinned core 2; and YAFU's internal tinysiqs time from Run C (no per-function clock).
  2. Instructions (callgrind 3.25.1, --dump-instr=yes, Ir only; one run per size and side):
     card: each executed instruction of lamp_qs / sieve_source goes to the region whose source span (pt_snap .. its last
       pt_end, below) contains the OUTERMOST qs.rs frame of its inline chain (addr2line -i) with a known line; a call from
       those functions to any other function gives its inclusive Ir to the call site's region; instructions whose chain has
       no qs.rs line in a span: "other (sieve_source / lamp_qs, outside the spans)", and line 0 is reported separately.
     YAFU: each executed main-object instruction under tinysiqs goes to its INNERMOST source function (addr2line -f -i);
       calls into other objects (GMP, libc) give their inclusive Ir to the calling instruction's innermost function.
  3. SIMD (per side, per phase): every executed main-object instruction classified from objdump -d: "256-bit" (a %ymm
     operand), "128-bit packed" (a %xmm operand, packed: p*/vp* integer ops, *ps/*pd, movdq*/movap*/movup*, shuffles,
     unpacks), "scalar FP in xmm" (*ss/*sd, cvt*, ucomis*/comis*, movd/movq to or from xmm), "general" (no vector register).
     Ir in other objects is not classified (reported as "library").
  python3 gap_locate.py -> gap_locate.json, stdout"""
import json, os, re, statistics, subprocess, sys, tempfile, time
from collections import defaultdict
import partition as P, sizescale2 as S2
from fastlamps import BIN
from baseline_msieve import conditions, cool, reference

SCRATCH = "/tmp/claude-1000/-home-onojk123-lumens-per-watt/ddfe4e3f-7fea-48e0-ba4d-4e65f4fd682d/scratchpad"
DBG = os.path.join(SCRATCH, "lc-debug1", "release", "lampcore")
YAFU = os.path.expanduser("~/opt/yafu-src/yafu/yafu")
SIZES = (72, 84, 96)
# the --phasetime regions as qs.rs source spans (pt_snap line .. last pt_end line; lampcore/src/qs.rs at this commit)
SPANS = [("mult", 214, 225), ("fb", 230, 232), ("solve", 241, 243), ("setup", 601, 759), ("setup", 761, 892),
         ("gray", 895, 926), ("sieve", 928, 1037), ("scan", 1038, 1041), ("resieve", 1042, 1101),
         ("confirm", 1104, 1216), ("lp_ledger", 1217, 1309)]
CARD_FNS = ("lampcore::qs::sieve_source", "lampcore::qs::lamp_qs")

def region_of(f, n):
    if not f.endswith("/lampcore/src/qs.rs") or not n.isdigit():
        return None
    n = int(n)
    for r, a, b in SPANS:
        if a <= n <= b:
            return r
    return None

def parse_cg(path):
    selfc = defaultdict(lambda: defaultdict(int)); edges = []
    ob = fn = cob = cfn = None; pending = False
    for line in open(path):
        if line[0] == "0":
            p = line.split(); addr, ir = int(p[0], 16), int(p[-1])
            if pending:
                edges.append((ob, fn, addr, cob or ob, cfn, ir)); pending = False; cob = None
            else:
                selfc[(ob, fn)][addr] += ir
        elif line.startswith("fn="):
            fn = line[3:].rstrip("\n"); cob = None
        elif line.startswith("ob="):
            ob = line[3:].rstrip("\n")
        elif line.startswith("cob="):
            cob = line[4:].rstrip("\n")
        elif line.startswith("cfn="):
            cfn = line[4:].rstrip("\n")
        elif line.startswith("calls="):
            pending = True
    return selfc, edges

def chains(binary, addrs, funcs=False):
    addrs = sorted(addrs)
    out = subprocess.run(["addr2line", "-a", "-i"] + (["-f"] if funcs else []) + ["-e", binary],
                         input="".join("0x%x\n" % a for a in addrs), capture_output=True, text=True, check=True).stdout.splitlines()
    res, cur, fname = {}, None, None
    for l in out:
        if re.fullmatch(r"0x[0-9a-f]+", l):
            cur = int(l, 16); res[cur] = []
        elif funcs and fname is None:
            fname = l
        else:
            f, _, n = l.split(" (discriminator")[0].rpartition(":")
            res[cur].append((fname, f, n) if funcs else (f, n)); fname = None
    return res

def classify(binary):
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary], capture_output=True, text=True, check=True).stdout
    cl = {}
    for l in out.splitlines():
        m = re.match(r"^ +([0-9a-f]+):\s+(\S+)\s*(.*)$", l)
        if not m:
            continue
        a, mn, ops = int(m.group(1), 16), m.group(2), m.group(3)
        if "%ymm" in ops or "%zmm" in ops:
            c = "256-bit"
        elif "%xmm" in ops:
            if re.search(r"(ss|sd)$", mn) or mn.startswith(("cvt", "vcvt", "ucomis", "comis", "vucomis", "vcomis")) or mn in ("movd", "movq", "vmovd", "vmovq"):
                c = "scalar FP in xmm"
            else:
                c = "128-bit packed"
        else:
            c = "general"
        cl[a] = c
    return cl

def card_phasetime(nums, bits):
    text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    t0 = time.perf_counter()
    r = subprocess.run(["taskset", "-c", "2", BIN, "--phasetime"], input=text, capture_output=True, text=True, check=True)
    wall = time.perf_counter() - t0
    tot = defaultdict(int)
    for l in r.stderr.splitlines():
        if l.startswith("{"):
            d = json.loads(l)
            if "regions" not in d:                          # the first line: the timer's overhead per region
                continue
            for k, v in zip(d["regions"], d["ns"]):
                tot[k] += v
    return wall, dict(tot)

def card_ir(nums, bits, work):
    text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    assert subprocess.run([DBG], input=text, capture_output=True, text=True).stdout == \
        subprocess.run([BIN], input=text, capture_output=True, text=True).stdout, "debug build output differs"
    cg = os.path.join(work, f"card{bits}.cg")
    subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=yes", "--compress-strings=no", "--compress-pos=no",
                    f"--callgrind-out-file={cg}", DBG], input=text, capture_output=True, text=True, check=True)
    selfc, edges = parse_cg(cg)
    main_ob = [o for o, f in selfc if o and o.endswith("/lc-debug1/release/lampcore")][0]
    own = {a: ir for (o, f), d in selfc.items() if o == main_ob and f in CARD_FNS for a, ir in d.items()}
    calls = [(a, ir) for o, f, a, co, cf, ir in edges if o == main_ob and f in CARD_FNS and cf not in CARD_FNS]
    ch = chains(DBG, set(own) | {a for a, _ in calls})
    def reg(a):
        c = ch[a]
        if all(not n.isdigit() or int(n) == 0 for f, n in c if f.endswith("qs.rs")):
            return "line 0"
        for f, n in reversed(c):                            # outermost first
            r = region_of(f, n)
            if r:
                return r
        return "other (in lamp_qs / sieve_source)"
    cl = classify(DBG)
    ir_by = defaultdict(int); simd = defaultdict(lambda: defaultdict(int))
    for a, ir in own.items():
        r = reg(a); ir_by[r] += ir; simd[r][cl.get(a, "general")] += ir
    for a, ir in calls:
        ir_by[reg(a)] += ir
    # classify callee main-object instructions too (inclusive edges): their SIMD mix, by the call site's region
    callee_self = defaultdict(int)
    for (o, f), d in selfc.items():
        if o == main_ob and f not in CARD_FNS:
            for a, ir in d.items():
                callee_self[cl.get(a, "general")] += ir
    incl = sum(ir for o, f, a, co, cf, ir in edges if cf == "lampcore::qs::lamp_qs")
    return {"Ir": dict(ir_by), "simd_own": {k: dict(v) for k, v in simd.items()}, "simd_callees_all": dict(callee_self),
            "lamp_qs_inclusive": incl, "attributed": sum(ir_by.values())}

def yafu_ir(nums, work):
    cg = os.path.join(work, "yafu.cg")
    subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=yes", "--compress-strings=no", "--compress-pos=no",
                    f"--callgrind-out-file={cg}", YAFU, "smallmpqs(@)", "-threads", "1"],
                   input="".join(f"{N}\n" for N, _, _ in nums), cwd=work, capture_output=True, text=True, check=True)
    selfc, edges = parse_cg(cg)
    main_ob = [o for o, f in selfc if o and o.endswith("/yafu")][0]
    # the functions under tinysiqs: the call graph's closure from tinysiqs (main object and libraries)
    kids = defaultdict(set)
    for o, f, a, co, cf, ir in edges:
        kids[(o, f)].add((co, cf))
    seen, todo = set(), [(main_ob, "tinysiqs")]
    while todo:
        k = todo.pop()
        if k in seen:
            continue
        seen.add(k); todo += list(kids[k])
    own = {a: ir for (o, f), d in selfc.items() if o == main_ob and (o, f) in seen for a, ir in d.items()}
    calls = [(a, ir) for o, f, a, co, cf, ir in edges if o == main_ob and (o, f) in seen and co != main_ob]
    ch = chains(YAFU, set(own) | {a for a, _ in calls}, funcs=True)
    def fn_of(a):
        c = ch[a]
        return c[0][0] if c else "?"
    cl = classify(YAFU)
    ir_by = defaultdict(int); simd = defaultdict(lambda: defaultdict(int)); lib = defaultdict(int)
    for a, ir in own.items():
        f = fn_of(a); ir_by[f] += ir; simd[f][cl.get(a, "general")] += ir
    for a, ir in calls:
        f = fn_of(a); ir_by[f] += ir; lib[f] += ir
    incl = sum(ir for o, f, a, co, cf, ir in edges if cf == "tinysiqs")
    return {"Ir": dict(ir_by), "library_Ir": dict(lib), "simd_own": {k: dict(v) for k, v in simd.items()},
            "tinysiqs_inclusive": incl, "attributed": sum(ir_by.values())}

if __name__ == "__main__":
    bad = conditions()
    if bad:
        print("timing skipped: " + "; ".join(bad)); sys.exit(2)
    runc = json.load(open("baseline_yafu_qs.json"))
    out = {}
    for bits in SIZES:
        bal = S2.map_nums(bits)[-P.PER_BAND:]
        passes = []
        for r in range(3):
            cool()
            passes.append(card_phasetime(bal, bits))
        regions = sorted({k for _, t in passes for k in t})
        ns = {k: statistics.median(t.get(k, 0) for _, t in passes) for k in regions}
        wall = statistics.median(w for w, _ in passes)
        work = tempfile.mkdtemp(prefix="gap_", dir=SCRATCH)
        c = card_ir(bal, bits, work)
        y = yafu_ir(bal, work)
        out[str(bits)] = {"card_phasetime_ns": ns, "card_wall_s": wall, "card": c, "yafu": y,
                          "yafu_internal_ms_runC": runc["sizes"][str(bits)]["mean_internal_ms"]["siqs"]}
        n = len(bal)
        print(f"== {bits} bits, balanced band ({n} numbers)")
        print(f"  card: wall {1e3 * wall / n:.3f} ms per number (--phasetime pass); lamp_qs inclusive {c['lamp_qs_inclusive'] / n / 1e6:.2f} M Ir "
              f"per number, attributed {c['attributed'] / n / 1e6:.2f} M")
        tot_ns = sum(ns.values())
        printed = set()
        for r in [s[0] for s in SPANS] + ["other (in lamp_qs / sieve_source)", "line 0"]:
            if r in printed:
                continue
            printed.add(r)
            ir = c["Ir"].get(r, 0)
            if not ir and not ns.get(r):
                continue
            sm = c["simd_own"].get(r, {})
            tot = sum(sm.values()) or 1
            print(f"    {r:34s} {ir / n / 1e6:7.3f} M Ir/number ({100 * ir / c['attributed']:5.1f}%); time share "
                  f"{100 * ns.get(r, 0) / tot_ns:5.1f}%; own Ir 256-bit {100 * sm.get('256-bit', 0) / tot:.1f}%, 128-bit packed "
                  f"{100 * sm.get('128-bit packed', 0) / tot:.1f}%, scalar FP {100 * sm.get('scalar FP in xmm', 0) / tot:.1f}%")
        cs = c["simd_callees_all"]; ct = sum(cs.values()) or 1
        print(f"    (callees' own instructions, all regions: 256-bit {100 * cs.get('256-bit', 0) / ct:.1f}%, 128-bit packed "
              f"{100 * cs.get('128-bit packed', 0) / ct:.1f}%, scalar FP {100 * cs.get('scalar FP in xmm', 0) / ct:.1f}%)")
        print(f"  YAFU tinysiqs: inclusive {y['tinysiqs_inclusive'] / n / 1e6:.2f} M Ir per number, attributed "
              f"{y['attributed'] / n / 1e6:.2f} M; internal time (Run C) {out[str(bits)]['yafu_internal_ms_runC']:.3f} ms")
        for f, ir in sorted(y["Ir"].items(), key=lambda kv: -kv[1]):
            if ir / y["attributed"] < 0.005:
                continue
            sm = y["simd_own"].get(f, {}); tot = sum(sm.values()) or 1
            print(f"    {f:34s} {ir / n / 1e6:7.3f} M Ir/number ({100 * ir / y['attributed']:5.1f}%); library "
                  f"{100 * y['library_Ir'].get(f, 0) / ir:4.1f}%; own Ir 256-bit {100 * sm.get('256-bit', 0) / tot:.1f}%, "
                  f"128-bit packed {100 * sm.get('128-bit packed', 0) / tot:.1f}%, scalar FP {100 * sm.get('scalar FP in xmm', 0) / tot:.1f}%")
        sys.stdout.flush()
    json.dump(out, open("gap_locate.json", "w"), indent=1)

ALLOC = ("malloc", "free", "realloc", "calloc", "cfree")

def card_library_by_region(cg_path):
    """Post-run (Experiment 1): the card's libc / libm Ir by --phasetime region. Each call from lamp_qs / sieve_source
    goes to its call site's region (as card_ir); a callee's inclusive Ir is split into allocation (malloc, free,
    realloc, calloc), memset / memcpy, log and the rest by the callee's own totals over the run (callee-wide fractions,
    an approximation for callees called from several regions)."""
    selfc, edges = parse_cg(cg_path)
    main_ob = [o for o, f in selfc if o and o.endswith("/lc-debug1/release/lampcore")][0]
    def kind(co, cf):
        if co == main_ob:
            return None
        b = cf.split("@")[0]
        if b in ALLOC or b.startswith(("_int_malloc", "_int_free")):
            return "alloc"
        if "memset" in b or "memcpy" in b or "memmove" in b:
            return "memset/memcpy"
        if b in ("log", "log2", "exp", "pow"):
            return "libm"
        return "other library"
    out_e = defaultdict(list)
    for o, f, a, co, cf, ir in edges:
        out_e[(o, f)].append((co, cf, ir))
    memo = {}
    def split(key):                                         # {kind: Ir} of a function's library calls, inclusive
        if key in memo:
            return memo[key]
        memo[key] = {}
        acc = defaultdict(float)
        for co, cf, ir in out_e[key]:
            k = kind(co, cf)
            if k:
                acc[k] += ir
            elif (co, cf) != key:
                sub = split((co, cf))
                tot = sum(ir2 for o2, f2, a2, co2, cf2, ir2 in edges if (co2, cf2) == (co, cf)) or 1
                for kk, v in sub.items():
                    acc[kk] += ir * v / tot
        memo[key] = dict(acc)
        return memo[key]
    calls = [(a, co, cf, ir) for o, f, a, co, cf, ir in edges if o == main_ob and f in CARD_FNS and cf not in CARD_FNS]
    ch = chains(DBG, {a for a, _, _, _ in calls})
    res = defaultdict(lambda: defaultdict(float))
    for a, co, cf, ir in calls:
        c = ch[a]
        r = next((region_of(f, n) for f, n in reversed(c) if region_of(f, n)), "other / line 0")
        k = kind(co, cf)
        if k:
            res[r][k] += ir
        else:
            sub = split((co, cf))
            tot = sum(ir2 for o2, f2, a2, co2, cf2, ir2 in edges if (co2, cf2) == (co, cf)) or 1
            for kk, v in sub.items():
                res[r][kk] += ir * v / tot
    return {r: dict(v) for r, v in res.items()}
