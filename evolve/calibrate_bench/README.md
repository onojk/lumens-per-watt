Raw outputs of the op-price calibration (NOTES.md, "Op-price calibration: result").

- `bench_ns.txt`: the three moduli (about 60, 84 and 100 bits) passed to opbench.
- `opbench_p1.jsonl`, `opbench_p2.jsonl`, `opbench_p3.jsonl`: three repeats on a P-core (`taskset -c 2`).
- `opbench_e1.jsonl`: one run on an E-core (`taskset -c 5`).
- `opbench_probe.jsonl`: the sizing probes (`opbench --probe`), used to estimate the wall time before launching.
- `opbench_p1_killed.jsonl`: the first run's 25 lines, before it hung on "sieve update" (count bug, fixed); the reruns reproduce them within 10%.
- `calibrate_price.out`, `calibrate_extra.out`: stdout of `calibrate.py price` and `calibrate.py extra` on the four runs.

Reproduce, from `evolve/`:

    D=calibrate_bench; NS=$(cat $D/bench_ns.txt); B=../lampcore/target/release/opbench
    for r in 1 2 3; do taskset -c 2 $B $NS > $D/opbench_p$r.jsonl; done
    taskset -c 5 $B $NS > $D/opbench_e1.jsonl
    python3 calibrate.py price $D/opbench_p1.jsonl $D/opbench_p2.jsonl $D/opbench_p3.jsonl $D/opbench_e1.jsonl
