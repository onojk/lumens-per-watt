# op-class v1: static cross-check (procedure, section 4, secondary)

The static count is the instructions in a class's steady-state body, from the line-annotated disassembly of
`opclass/bin/lampcore-debug1`, whose code is identical to the release binary's. It is taken per op, along the
common path. It is set against the dynamic weight (`opclass_v1.json`). Any class off by more than 10% is
explained here, before step 3.

| class | static, per op | dynamic weight | difference | explanation |
|---|---|---|---|---|
| root_test | 54 (2′b in-place loop, qs.rs 1153–1161) | 52.29 | −3% | within 10% |
| sieve_update | 10 (base-prime walk, qs.rs 959–962; bounds checks and stack reloads not hoisted) | 11.09 | +11% | the per-root work around the walk (offset load, start test, loop entry and exit, the k loop) is mapped to sieve_update. It amortises over the few updates per root at large p. The static body excludes it by rule. |
| sieve_scan | 11 (scan compare per cell, qs.rs 1039) + the clear | 14.89 | +35% without the clear; −1% with it | the clear (qs.rs 930) calls glibc's `memset`, which runs `rep stosb` (ERMS). Callgrind counts each repetition as an instruction: about 4 per 4-byte cell, i.e. 846M Ir over 99,867 polynomials in A_ref_96, about 4.0 per cell. 11 + 4 = 15. The static rule counts `rep stosb` once, so the static figure is low for this reason only. |
| setup_gray | 2.6 (d > 0: SSE body, 21 per 8 roots) / about 7.5 (d < 0: scalar, unrolled ×2, branchy) | 4.87 | between the two | the compiler vectorised only the d > 0 branch (qs.rs 905–907). The d < 0 branch (918–920) is scalar. The Gray code flips each sign half the time, so the mean of about 5.0 matches. No single body represents the class. |
| la | 17 per XOR actually executed (qs.rs 437) | 28.38 per charged op | +67% | the charge is a formula, ⌈rows·F·rows / 64⌉, not the number of XORs done. The dynamic weight also includes the pivot search (qs.rs 429) and the row clones. Static and dynamic measure different units. |
| setup_euclid | about 28 per Euclid step (euclid_inv64 loop, 32-bit divide path) | 39.38 | +41% | each inverse also pays a fixed entry and exit (two `rem_euclid`, the call, the result) mapped to setup_euclid. The steps per inverse are few (moduli below 2^30), so that fixed part is a large share per step. The 64-bit `idiv` path is longer than the 32-bit one. |

**No single steady-state body; dynamic only.** For these classes the path length depends on the operands or runs
through library code, so a static body count does not represent the op:
- confirm_td, td_mod, lp_small: 128-bit remainders through `__modti3` / `__umodti3`, whose path depends on the operand sizes;
- mul, sqrt_mul, lp_full, check, setup_mul: ruint `mul_mod` on U256, out of line;
- gcd, sqrt_gcd: ruint gcd;
- f64_log: libm `log`;
- hash: std HashMap / HashSet probes;
- mult, fb, setup_small, setup_euclid_N, sort_cmp, f64_div: a mix of arithmetic and short sequences;
- word: scattered sites in four lamps;
- sq_ops, ps_ops, cfrac_ops: lumps.

For these the dynamic weight stands alone.

Nothing here is priced.
