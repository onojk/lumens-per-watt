"""I-047 (the user's go-ahead, Oct 27 night): rho for the A-prime lookup fix. Instructions retired (callgrind 3.25.1, Ir,
whole-program summary) on all map numbers at 72 / 84 / 96 (Run A's inputs and genes: the reference, 2'b), before the fix
(opclass/bin/lampcore-debug1, sha256 b5b8dc6a..., the line-table build of Run A's pre-fix release 1505efbf...) and after
(lampcore 210a7d0 built with line tables, Claude's scratch lc-debug1, sha256 1b49eb6b...: the fix, before alloc-once);
stdout of each checked identical to its release twin's (pre-fix: opclass/bin/lampcore-release; post-fix: the copy
ef345913... in Claude's scratch). rho = Run A's wall change / the instruction change. Memory class (PROTOCOL): (c), a
factor-base scan suspected of evicting sieve data. No timing.
  python3 rho_aprime.py -> rho_aprime.json, stdout"""
import json, os, re, subprocess, tempfile
import partition as P, sizescale2 as S2
from baseline_msieve import reference

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = "/tmp/claude-1000/-home-onojk123-lumens-per-watt/ddfe4e3f-7fea-48e0-ba4d-4e65f4fd682d/scratchpad"
BUILDS = {"before": (os.path.join(HERE, "..", "opclass", "bin", "lampcore-debug1"), os.path.join(HERE, "..", "opclass", "bin", "lampcore-release")),
          "after": (os.path.join(SCR, "lc-debug1", "release", "lampcore"), os.path.join(SCR, "lampcore_fix_ef3459"))}
RUN_A = json.load(open("aprimefix_time.json"))

def ir(binary, text):
    out = os.path.join(tempfile.mkdtemp(dir=SCR, prefix="rho_"), "cg.out")
    subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=no", "--dump-line=no", f"--callgrind-out-file={out}", binary],
                   input=text, capture_output=True, text=True, check=True)
    return int(re.search(r"^summary: (\d+)", open(out).read(), re.M).group(1))

if __name__ == "__main__":
    res = {}
    for bits in (72, 84, 96):
        nums = S2.map_nums(bits)
        text = json.dumps([reference(bits)]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
        r = {}
        for k, (dbg, rel) in BUILDS.items():
            assert subprocess.run([dbg], input=text, capture_output=True, text=True).stdout == \
                subprocess.run([rel], input=text, capture_output=True, text=True).stdout, k
            r[k] = ir(dbg, text) / len(nums)
        di = r["after"] / r["before"] - 1
        dw = RUN_A["sizes"][str(bits)]["ratio"]["mean"] - 1
        ci = [x - 1 for x in RUN_A["sizes"][str(bits)]["ratio"]["ci95"]]
        res[bits] = {"Ir_per_number": r, "instruction_change": di, "wall_change_runA": dw, "wall_ci_runA": ci,
                     "rho": dw / di, "rho_from_ci": [ci[1] / di, ci[0] / di]}
        print(f"{bits} bits ({len(nums)} numbers): instructions per number {r['before'] / 1e6:.3f} M -> {r['after'] / 1e6:.3f} M "
              f"({100 * di:+.2f}%); Run A wall {100 * dw:+.2f}% [{100 * ci[0]:+.2f}, {100 * ci[1]:+.2f}]; "
              f"rho {dw / di:.2f} (from the interval {ci[1] / di:.2f}-{ci[0] / di:.2f})", flush=True)
    json.dump(res, open("rho_aprime.json", "w"), indent=1)
