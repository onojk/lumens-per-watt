# op-class v1, derivation A: method

Inputs read: reviews/opclass_procedure.md (s.4), opclass/README.md, opclass/linemap.tsv, opclass/inputs.json, opclass/inputs/*.in,
opclass/bin/*, lampcore/src/*.rs (line text only), evolve/optypes.py (TYPE_ORDER only). Nothing priced.

## Runs (derivA_callgrind.py)
- sha256 checked before counting: both binaries match opclass/README.md; all 17 inputs match inputs.json.
- Each input: `valgrind --tool=callgrind --dump-instr=yes --compress-strings=no --compress-pos=no lampcore-debug1 --types < X.in`
  (valgrind 3.25.1, Ir only, no cache sim). Outputs: raw/<run>.cg, raw/<run>.stdout, raw/<run>.vglog.
- Every callgrind stdout is byte-identical to a native run of lampcore-debug1 --types on the same input.
- Op counts: per run, the sum over the stdout lines of the 30 integers after " T " (TYPE_ORDER); line count == inputs.json "numbers".

## Parsing and address offset
- Cost lines "0xADDR LINE Ir" are self Ir of the current (ob, fn); the line after "calls=" is an edge (caller fn, call-site ADDR,
  callee (cob or ob, cfn), inclusive Ir). Per run, the sum of self Ir equals callgrind's summary exactly (asserted).
- Load offset: callgrind writes main-object addresses already relative to the object (offset 0 against the ELF vaddrs):
  fn=main starts at 0x49210 and cfn=__modti3 at 0xcd790, both equal to `nm` of lampcore-debug1. No correction applied.
  Only addresses of ob=lampcore-debug1 are looked up; all other objects (libc, libm, ld.so, libgcc_s, vgpreload, ???) are unresolved.

## R1
Line text stripped; meter if it starts with m.charge( / m.tick( / m.test( / m.ev( / crate::pt_ / crate::sv_units( or matches
`let (pt|ps|ptl|pt_a|pt_pre) = crate::pt_snap` (prefix; so `let ps = crate::pt_snap_sv(m)` counts). 144 lines overridden (lines already mapped meter not counted)
(list in weights.json "r1_overrides"; includes qs.rs 75/79/82 inside the @caller cpow_n, which become meter).

## R2
`addr2line -a -i -e lampcore-debug1` on every executed main-object address and every main-object call-site address. The chain
is innermost first (line-table row, then each DW_TAG_inlined_subroutine call site outward). Walk outward; take the first frame
whose path contains /lampcore/src/ AND has a known nonzero line; its class (R1, else map) is used unless it is @caller, in which
case keep walking. No frame -> unresolved (R3). decl is a class (not skipped).

**Ambiguity 1 (line 0).** The rules do not say what to do with a lampcore/src frame whose line is 0/unknown ("qs.rs:?"),
or with an instruction whose only frame is a line-0 row of a library file inside a lampcore function. Primary (strict):
a line-0 frame is not a "resolvable line", so it is skipped like @caller; if nothing remains, R3 applies (the cost goes to the
function's call sites). This is large: 2.54e9 Ir of unresolved line-0 code in lampcore::qs::sieve_source alone (plus
Ledger::solve, euclid_inv64, isqrt, Meter::charge, ...), sent by R3 to sieve_source's caller line (uncharged:card).
Sensitivity (DERIVA_LINE0=prevrow, weights_line0_prevrow.json, NOT the primary): such an instruction instead takes the class of
the nearest preceding resolved instruction in the same function (objdump order); 4,474 addresses changed. Effect on weights:
la +10.7%, lp_small +11.7%, setup_euclid_N +5.7%, setup_euclid +5.1%, confirm_td +4.6%, root_test +4.0%, setup_small +2.9%,
sieve_update +2.2%, word +2.0%, f64_log +1.8%, fb -1.1%, others < 0.5%; uncharged:card 11.01e9 -> 7.99e9, meter 4.38e9 -> 4.60e9.
The two derivations must use the same reading; this needs a ruling.

## R3
Per run, per function H: U(H) = H's self Ir at unresolved addresses (all of it for non-main objects). Each incoming edge e of H
has share s_e = incl(e) / sum of incl over all edges into H (callgrind inclusive Ir, per run). Pending P(H) = U(H) + sum over
H's edges at UNRESOLVED call sites into callee C of s_e * P(C). Solved exactly as a linear system (numpy solve of (I - A) P = U),
which handles self-recursion and longer cycles (equivalent to the geometric series of pushing a cycle's share around). Then each
edge at a RESOLVED call site adds s_e * P(callee) to the call site's class (R2 applied to the call instruction's address).
Edge sites on decl lines: none.

## R4
P of functions with no incoming edge (roots: (below main)/_start, ld.so start-up) = unattributed. The C main shim, std's
lang_start and exit handlers have no lampcore line and reach the root through their callers.

## R5
Runs with inputs.json lump (C_sq sq_ops, C_ps ps_ops, C_cfrac cfrac_ops): after R2/R3, every class except meter,
uncharged:harness, decl is renamed to the lump. Unattributed stays unattributed (it is not a class).

## R6 and the sum check
weight = sum of Ir over all 17 runs / sum of ops over all 17 runs; fraction = weight / root_test weight. Every run's classes +
meter + uncharged + decl + unattributed equals callgrind's total to float rounding (|diff| < 4e-6 Ir per run; 3e-5 over all).

**Ambiguity 2 (Ir without ops).** Some runs put Ir on a class with zero ops in that run (by the map): check (the Ledger::add test
path, 0.18-1.5M per qs run), root_test in 2'a/pipeline runs (0.04-1.3M), cfrac_ops (2.6-6.4k). R6 sums them anyway, so
check's pooled weight (337.1) is above its only charging run's (C_check, 272.9). Per-run figures are in weights.json.

## decl Ir
913,262 Ir: main.rs:385 (ks_eval's closing brace, epilogue) 865,332 and qs.rs:394 (Ledger::solve's doc line, prologue) 47,930.

## Per-class weight spread across the runs that charge it (primary)
| class | runs | min | max | max/min |
|---|---|---|---|---|
| mult | 11 | 36.598 (B_pipe_54) | 65.659 (C_check) | 1.794 |
| fb | 11 | 26.129 (A_2b_96) | 30.558 (B_pipe_54) | 1.169 |
| setup_euclid | 11 | 38.358 (B_pipe_96) | 51.299 (B_pipe_54) | 1.337 |
| setup_small | 11 | 172.942 (A_2b_96) | 234.953 (B_pipe_54) | 1.359 |
| sieve_update | 11 | 10.988 (A_ref_96) | 11.891 (A_ref_72) | 1.082 |
| sieve_scan | 11 | 11.547 (C_check) | 15.139 (A_2b_84) | 1.311 |
| confirm_td | 11 | 105.733 (A_ref_96) | 139.668 (A_2b_96) | 1.321 |
| la | 11 | 26.609 (B_pipe_96) | 61.102 (B_pipe_54) | 2.296 |
| sqrt_mul | 11 | 258.286 (B_pipe_54) | 303.411 (A_ref_96) | 1.175 |
| sqrt_gcd | 11 | 121.676 (B_pipe_54) | 178.435 (B_pipe_96) | 1.466 |
| lp_full | 11 | 506.378 (B_pipe_54) | 658.034 (B_pipe_96) | 1.299 |
| lp_small | 11 | 64.000 (C_check) | 69.000 (A_ref_96) | 1.078 |
| check | 1 | 272.911 (C_check) | 272.911 (C_check) | 1.000 |
| setup_mul | 1 | 306.355 (C_ecm) | 306.355 (C_ecm) | 1.000 |
| setup_euclid_N | 1 | 112.613 (C_ecm) | 112.613 (C_ecm) | 1.000 |
| mul | 6 | 486.953 (C_ecm) | 588.273 (B_pipe_72) | 1.208 |
| gcd | 6 | 730.366 (B_pipe_54) | 1551.908 (B_pipe_96) | 2.125 |
| td_mod | 1 | 29.000 (C_td) | 29.000 (C_td) | 1.000 |
| sq_ops | 1 | 1266.280 (C_sq) | 1266.280 (C_sq) | 1.000 |
| ps_ops | 1 | 0.283 (C_ps) | 0.283 (C_ps) | 1.000 |
| cfrac_ops | 1 | 110.064 (C_cfrac) | 110.064 (C_cfrac) | 1.000 |
| word | 13 | 1.335 (C_pm1s2) | 71.273 (C_check) | 53.390 |
| setup_gray | 11 | 4.771 (B_pipe_96) | 6.011 (B_pipe_54) | 1.260 |
| hash | 11 | 451.157 (A_ref_84) | 473.280 (C_check) | 1.049 |
| sort_cmp | 11 | 51.448 (B_pipe_54) | 81.384 (C_check) | 1.582 |
| f64_log | 11 | 130.608 (B_pipe_54) | 137.030 (A_ref_72) | 1.049 |
| f64_div | 11 | 6.000 (A_ref_72) | 6.000 (A_ref_72) | 1.000 |
| root_test | 3 | 52.207 (A_2b_96) | 52.533 (A_2b_72) | 1.006 |

Classes within 2% across runs: root_test (0.6%), f64_div (exactly 6.000). Single-run classes (check, setup_mul,
setup_euclid_N, td_mod, sq_ops, ps_ops, cfrac_ops) have no cross-run spread; a per-number split would need per-number callgrind
dumps, not done here. word's spread (C_pm1s2 1.3 to C_check 71) reflects which lamps' word ops a run contains.

## Files
derivA_callgrind.py (runs), derivA_attrib.py (attribution; env DERIVA_LINE0=prevrow for the sensitivity), weights.json,
weights_line0_prevrow.json, raw/ (callgrind outputs, stdouts, valgrind logs), out/callgrind_driver.log.
