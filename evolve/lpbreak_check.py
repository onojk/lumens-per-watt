"""Read-only check of the lp_ledger sub-timers (NOTES.md, "lp_ledger breakdown"): on all map numbers, new
reference with and without re-sieve, lampcore's stdout (ops, factor, tests, hits, per-type counts) is identical
(i) with --phasetime and LAMPCORE_LPBREAK=1 against --phasetime without it, and (ii) against the pre-change
binary (LAMPCORE_OLD) without --phasetime.
  LAMPCORE_OLD=<pre-change binary> python3 lpbreak_check.py -> stdout
"""
import os, json, subprocess
import partition as P, sizescale as SS, sizescale2 as S2
import fastlamps
sealed = json.load(open("sizescale_k_sealed.json"))
n = bad = 0
for bits in SS.SIZES:
    nums = S2.map_nums(bits)
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    for g in (nr, dict(nr, confirm="resieve")):
        text = json.dumps([g]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
        run = lambda b, args, env: subprocess.run([b] + args, input=text, capture_output=True, text=True, check=True, env=env).stdout
        on = run(fastlamps.BIN, ["--types", "--phasetime"], dict(os.environ, LAMPCORE_LPBREAK="1"))
        off = run(fastlamps.BIN, ["--types", "--phasetime"], {k: v for k, v in os.environ.items() if k != "LAMPCORE_LPBREAK"})
        plain = run(fastlamps.BIN, ["--types"], os.environ)
        old = run(os.environ["LAMPCORE_OLD"], ["--types"], os.environ)
        for a, b, c, d in zip(on.splitlines(), off.splitlines(), plain.splitlines(), old.splitlines()):
            n += 1
            bad += not (a == b == c == d)
print(f"stdout identical (timers on / off with --phasetime, without --phasetime, pre-change binary): {n - bad}/{n}")
assert not bad
