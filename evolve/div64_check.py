"""The cost note's check for the 64-bit division (after code, before timing; information): instructions per number in
lamp_qs (inclusive) and in calls to __modti3 / __divti3 from lamp_qs / sieve_source, before (the second gap run's
callgrind files: lampcore f6aa08d, lc-debug2) and after (this commit's source with line tables, Claude's scratch
lc-debug3), the same balanced bands (80 numbers), the reference genes; the after build's stdout checked identical to
the release binary's.
  python3 div64_check.py -> div64_check.json, stdout"""
import glob, json, os, subprocess, tempfile
import partition as P, sizescale2 as S2
import gap_locate as G
from fastlamps import BIN
from baseline_msieve import reference

DBG3 = os.path.join(G.SCRATCH, "lc-debug3", "release", "lampcore")

def counts(cg):
    selfc, edges = G.parse_cg(cg)
    incl = sum(ir for o, f, a, co, cf, ir in edges if cf == "lampcore::qs::lamp_qs")
    ti = sum(ir for o, f, a, co, cf, ir in edges if f in G.CARD_FNS and cf in ("__modti3", "__divti3"))
    return incl / 80, ti / 80

if __name__ == "__main__":
    out = {}
    est = {72: 0.432, 84: 0.703, 96: 1.071}                    # the cost note, c = 7.5 (M per number)
    for bits in (72, 84, 96):
        bal = S2.map_nums(bits)[-P.PER_BAND:]
        text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in bal)
        assert subprocess.run([DBG3], input=text, capture_output=True, text=True).stdout == \
            subprocess.run([BIN], input=text, capture_output=True, text=True).stdout
        cg1 = [w for w in sorted(glob.glob(os.path.join(G.SCRATCH, "gap2_*")), key=os.path.getmtime)
               if os.path.exists(os.path.join(w, f"card{bits}.cg"))][-1] + f"/card{bits}.cg"
        cg2 = os.path.join(tempfile.mkdtemp(prefix="d64_", dir=G.SCRATCH), f"card{bits}.cg")
        subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=yes", "--compress-strings=no", "--compress-pos=no",
                        f"--callgrind-out-file={cg2}", DBG3], input=text, capture_output=True, text=True, check=True)
        (b, bt), (a, at) = counts(cg1), counts(cg2)
        out[bits] = {"before": {"Ir": b, "ti_Ir": bt}, "after": {"Ir": a, "ti_Ir": at}}
        print(f"{bits} bits: instructions per number {b / 1e6:.3f} M -> {a / 1e6:.3f} M ({100 * (a / b - 1):+.2f}%; removed "
              f"{(b - a) / 1e6:.3f} M, the cost note's estimate {est[bits]:.3f} M); __modti3 / __divti3 from lamp_qs / sieve_source "
              f"{bt / 1e6:.3f} M -> {at / 1e6:.3f} M", flush=True)
    json.dump(out, open("div64_check.json", "w"), indent=1)
