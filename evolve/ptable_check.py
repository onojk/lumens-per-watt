"""The cost note's check for the fixed-size partials table (after code, before timing; information): instructions per
number in lamp_qs (inclusive), before (div64_check.py's after files: the div64 commit with line tables, lc-debug3) and
after (this commit's source with line tables, Claude's scratch lc-debug4), the same balanced bands (80 numbers), the
reference genes; the after build's stdout checked identical to the release binary's. Also, from the Python card's
trace on 10 balanced 96-bit numbers: partial-relation inserts per attempt (does the 4,096-slot table ever double?).
  python3 ptable_check.py -> ptable_check.json, stdout"""
import glob, json, os, subprocess, tempfile
import partition as P, sizescale2 as S2
import gap_locate as G, qs, lamps
from fastlamps import BIN
from baseline_msieve import reference

DBG4 = os.path.join(G.SCRATCH, "lc-debug4", "release", "lampcore")

def incl(cg):
    selfc, edges = G.parse_cg(cg)
    return sum(ir for o, f, a, co, cf, ir in edges if cf == "lampcore::qs::lamp_qs") / 80

if __name__ == "__main__":
    out = {}
    est = {72: 0.180, 84: 0.273, 96: 0.631}                    # the cost note, c = 22.5 (M per number)
    for bits in (72, 84, 96):
        bal = S2.map_nums(bits)[-P.PER_BAND:]
        text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in bal)
        assert subprocess.run([DBG4], input=text, capture_output=True, text=True).stdout == \
            subprocess.run([BIN], input=text, capture_output=True, text=True).stdout
        cg1 = [w for w in sorted(glob.glob(os.path.join(G.SCRATCH, "d64_*")), key=os.path.getmtime)
               if os.path.exists(os.path.join(w, f"card{bits}.cg"))][-1] + f"/card{bits}.cg"
        cg2 = os.path.join(tempfile.mkdtemp(prefix="ptc_", dir=G.SCRATCH), f"card{bits}.cg")
        subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=yes", "--compress-strings=no", "--compress-pos=no",
                        f"--callgrind-out-file={cg2}", DBG4], input=text, capture_output=True, text=True, check=True)
        b, a = incl(cg1), incl(cg2)
        out[bits] = {"before_Ir": b, "after_Ir": a, "removed": b - a, "cost_note_estimate": est[bits] * 1e6}
        print(f"{bits} bits: instructions per number {b / 1e6:.3f} M -> {a / 1e6:.3f} M ({100 * (a / b - 1):+.2f}%; removed "
              f"{(b - a) / 1e6:.3f} M, the cost note's estimate {est[bits]:.3f} M, a difference of {100 * ((b - a) / 1e6 / est[bits] - 1):+.0f}%)", flush=True)
    ins = []
    for N, _, _ in S2.map_nums(96)[-10:]:
        qs.TRACE = {}
        try:
            qs.lamp_qs(N, reference(96), lamps.Meter(P.QS_CAP))
        except lamps.Budget:
            pass
        ins += [a["lp"]["inserts"] for a in qs.TRACE["attempts"] if "lp" in a]
        qs.TRACE = None
    out["inserts_per_attempt_96"] = ins
    print(f"96 bits, 10 balanced numbers (Python trace): partial inserts per attempt max {max(ins)}, median {sorted(ins)[len(ins) // 2]} "
          f"({len(ins)} attempts); the table doubles past 2,048 entries: {'never' if max(ins) <= 2048 else 'yes'}", flush=True)
    json.dump(out, open("ptable_check.json", "w"), indent=1)
