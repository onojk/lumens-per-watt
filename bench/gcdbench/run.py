"""gcd cost against N's size (the user's meter check before Seven of Nine stage 3; I-042 style; untimed; never charged).
Callgrind instructions per call of ruint 1.20.1 U256::gcd (as lampcore calls it), M = 2,000 calls, minus the same loop
without the gcd (the *0 modes), 3 seeds; N random odd of the given bits.
  small   : k = 2, 3, ... (the vl lamp's dots)
  uniform : k uniform below N (rho / p-1 / ECM's gcd against N)
  tdmod   : td's step, N mod d (u128), d = 3, 5, ... (beside, for the vl / td ratio)
  cd bench/gcdbench && cargo build --release --offline && python3 run.py -> gcd_ir.json, stdout"""
import json, os, re, subprocess
B = "./target/release/gcdbench"
M = 2000

def ir(bits, mode, seed):
    out = f"cg_{bits}_{mode}_{seed}.out"
    subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=no", "--dump-line=no", f"--callgrind-out-file={out}", B,
                    str(bits), mode, str(M), str(seed)], capture_output=True, check=True)
    v = int(re.search(r"^summary: (\d+)", open(out).read(), re.M).group(1)); os.remove(out); return v

res = {}
for bits in (24, 32, 48, 64, 96, 128):
    for mode in ("small", "uniform", "tdmod"):
        res[f"{bits} {mode}"] = [(ir(bits, mode, s) - ir(bits, mode + "0", s)) / M for s in (1, 2, 3)]
        print(bits, mode, [round(x, 1) for x in res[f"{bits} {mode}"]], flush=True)
json.dump(res, open("gcd_ir.json", "w"), indent=1)
