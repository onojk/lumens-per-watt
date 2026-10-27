# op-class v1, derivation B: method

Inputs used: reviews/opclass_procedure.md, opclass/README.md, opclass/linemap.tsv, opclass/inputs.json + inputs/*.in,
opclass/bin/lampcore-{debug1,release} (sha256 checked against README; every input's sha256 checked against inputs.json,
all match), lampcore/src/*.rs (line text for R1), TYPE_ORDER (identical to lampcore's TYPE_NAMES).

Scripts: `derivB_runs.py` (hash checks; `valgrind --tool=callgrind --dump-instr=yes --compress-strings=no
--compress-pos=no` on `lampcore-debug1 --types`, all other options default, incl. `--separate-recs=2`);
`derivB_attr.py` (attribution, weights; `LINE0=prev` env selects the sensitivity variant). Raw callgrind files,
stdout and valgrind logs: `raw/`. `objdump.txt` is the disassembly used only by the variant.
Every run's debug1-under-callgrind stdout is byte-identical to the release binary's native `--types` stdout.

## Ops
Sum over every output line of the 30 integers after " T" (line count checked = inputs.json "numbers").

## R1
Line text stripped; meter if it starts with `m.charge(`, `m.tick(`, `m.test(`, `m.ev(`, `crate::pt_`, `crate::sv_units(`,
or matches `^let (pt|ps|ptl|pt_a|pt_pre) = crate::pt_snap` (this includes `pt_snap_sv` / `pt_snap_lp`, which begin
with the text `crate::pt_snap`). Applied to the line's class before any R2 walk (so an R1 line is never @caller).

## R2 (address offset, inline chains)
Callgrind writes main-object instruction addresses relative to the object's load base; they equal the ELF/nm
addresses directly (e.g. `lampcore::main` at 0x3e6a0 in both), so offset = 0. Each executed main-object address and
each call-site address is resolved with `addr2line -i -a -e lampcore-debug1` (frames innermost first; outer frames
carry the call line). Walk frames innermost -> outermost; skip frames not in lampcore/src/{cfrac,ecm,main,qs,race}.rs
(no frame ever landed in lampcore/src/bin); skip a lampcore frame with line 0 (ambiguity 1); skip @caller lines; the
first remaining frame gives (file, line, class). No such frame -> unresolved. Code in other objects (libc, libm,
ld.so, vgpreload, ob=???) is always unresolved.

## R3 (call edges)
Node = (object, callgrind function name; recursion levels `f'2` are their own nodes). Unresolved self Ir is pooled
per node. Each callgrind call edge (caller node, call-site address, callee node, inclusive Ir) carries a share of the
callee's pool: share = edge inclusive Ir / sum of inclusive Ir over all edges into the callee. If the call-site
address resolves by R2, the share is absorbed by that line's class; otherwise it joins the caller node's pool and
continues upward. Self-edges with an unresolved call site (a node calling itself) are dropped from the denominator:
their share would only return to the same pool, so dropping it gives the same absorption and conserves mass. Cycles
across nodes: the push is iterated until every pool holds < 1e-9 Ir (that tail is booked unattributed; < 1e-6 Ir per
run). A pool with no incoming edges (_start, ld.so entry) is unattributed (R4); cost whose path reaches only the C
main shim / libc start-up ends there.

## R5
Runs with inputs.json "lump" set (C_sq, C_ps, C_cfrac): all classes except meter, uncharged:harness, decl (and
unattributed) are relabelled as the lump class, after R2/R3.

## R6
weight = sum Ir / sum ops over all 17 runs; fraction = weight / root_test weight.

## Sum check
Per run and in total, classes + meter + uncharged:card + uncharged:harness + decl + unattributed = callgrind summary
Ir to within 4e-6 Ir (float rounding; total 138,220,025,671 Ir). Callgrind's summary equals the sum of its self-cost
lines in every file.

## Ambiguities and how they were resolved
1. **Line-0 rows.** Many instructions carry DWARF line 0 in a lampcore frame. Where an outer lampcore frame has a
   real line I move outward (a line-0 frame has no class). Where every lampcore frame is line 0 (e.g. 0.73e9 Ir in
   the non-inlined `qs::sieve_source` in A_ref_96 alone; also Ledger::solve, euclid_inv64, Meter::charge,
   combinations, OnDemand::next), the primary result reads R3 literally ("no resolvable lampcore/src line"): the cost
   goes to the caller's line (sieve_source's only call site is qs.rs:237, uncharged:card). Sensitivity variant
   `LINE0=prev` (`weights_line0_prev.json`): such an instruction takes the class of the nearest preceding instruction
   in the same symbol (objdump order) that has a real lampcore line. It moves ~2.6e9 Ir out of uncharged:card;
   root_test's weight goes 52.29 -> 54.32 (+3.9%), and the fractions move by 0-5%. This exceeds the 2% agreement
   tolerance, so the two readings must be ruled on.
2. **Ir in a class in runs with zero ops of that class** (function entries and gene tests): `check` (qs.rs 376-377,
   Ledger::add's entry and `if chk`) 7.6e6 Ir across the non-check qs runs; `root_test` (qs.rs 1145, the confirm
   branch) 3.9e6 Ir in 2'a runs; `cfrac_ops` (cfrac.rs 29) 4.6e4 Ir in qs runs. R6 as written sums them in:
   check's weight is 337.1 by R6 against 272.9 in C_check alone (+23.5%); root_test 52.29 against 52.26.
3. **Decl lines with Ir:** main.rs:385 (ks_eval's closing brace: epilogue) 865,332 Ir; qs.rs:394 (the `fn solve`
   signature, inside a "blank, doc" decl range) 47,930 Ir. Reported as decl, not reassigned.

## Per-class weight spread across the runs that contain its ops (primary rule), and the line-0 variant
| class | min | max | max/min-1 | runs | weight (LINE0=prev) | fraction (LINE0=prev) |
|---|---|---|---|---|---|---|
| mult | 36.598 | 65.659 | 79.4% | 11 | 64.044 | 1.1790 |
| fb | 26.129 | 30.558 | 16.9% | 11 | 27.059 | 0.4981 |
| setup_euclid | 38.358 | 51.299 | 33.7% | 11 | 41.381 | 0.7618 |
| setup_small | 172.942 | 234.953 | 35.9% | 11 | 182.139 | 3.3530 |
| sieve_update | 10.988 | 11.891 | 8.2% | 11 | 11.328 | 0.2085 |
| sieve_scan | 11.547 | 15.139 | 31.1% | 11 | 14.893 | 0.2742 |
| confirm_td | 105.733 | 139.668 | 32.1% | 11 | 113.380 | 2.0872 |
| la | 26.609 | 61.102 | 129.6% | 11 | 29.454 | 0.5422 |
| sqrt_mul | 258.286 | 303.411 | 17.5% | 11 | 299.065 | 5.5055 |
| sqrt_gcd | 121.676 | 178.435 | 46.6% | 11 | 159.699 | 2.9399 |
| lp_full | 506.378 | 658.034 | 29.9% | 11 | 649.422 | 11.9552 |
| lp_small | 64.000 | 69.000 | 7.8% | 11 | 76.227 | 1.4033 |
| check | 272.911 | 272.911 | 0.0% | 1 | 336.435 | 6.1934 |
| setup_mul | 306.355 | 306.355 | 0.0% | 1 | 306.355 | 5.6397 |
| setup_euclid_N | 112.613 | 112.613 | 0.0% | 1 | 118.983 | 2.1904 |
| mul | 486.953 | 588.273 | 20.8% | 6 | 554.862 | 10.2145 |
| gcd | 730.366 | 1551.908 | 112.5% | 6 | 1401.749 | 25.8048 |
| td_mod | 29.000 | 29.000 | 0.0% | 1 | 29.000 | 0.5339 |
| sq_ops | 1266.280 | 1266.280 | 0.0% | 1 | 1266.154 | 23.3087 |
| ps_ops | 0.283 | 0.283 | 0.0% | 1 | 0.283 | 0.0052 |
| cfrac_ops | 110.064 | 110.064 | 0.0% | 1 | 110.088 | 2.0266 |
| word | 1.335 | 71.273 | 5239.0% | 13 | 56.435 | 1.0389 |
| setup_gray | 4.771 | 6.011 | 26.0% | 11 | 4.879 | 0.0898 |
| hash | 451.139 | 473.206 | 4.9% | 11 | 465.421 | 8.5679 |
| sort_cmp | 51.448 | 81.384 | 58.2% | 11 | 67.399 | 1.2407 |
| f64_log | 130.608 | 137.030 | 4.9% | 11 | 137.406 | 2.5295 |
| f64_div | 6.000 | 6.000 | 0.0% | 11 | 6.000 | 0.1105 |
| root_test | 52.207 | 52.533 | 0.6% | 3 | 54.321 | 1.0000 |

Widest spreads: mult 36.6 in B_pipe_54 vs 65.66 in every other run; la falls with size (61.1 at 54 bits -> 26.6 at 96); gcd 730-1552 (grows with N); word 1.33 in C_pm1s2 vs 38-71 elsewhere; confirm_td 105.7-109.6 in 2'a/pipeline runs vs 135.8-139.7 in 2'b runs; sort_cmp 51-81. Within 2%: root_test (0.6%), f64_div, and the single-run classes (check, setup_mul, setup_euclid_N, td_mod, sq_ops, ps_ops, cfrac_ops; spread not measurable from one run).
