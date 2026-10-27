(* I-032 cost model (NOTES, "Design note: root confirm without the per-polynomial offset pass"; this run's entry).
   Root confirm alone at 96 bits against the reference, means per number over the 640 map numbers, card e13603a.
   Inputs copied from card runs (run_many --types and phasetime call counts, Oct 27; calibrate.json prices).
   Model only: op counts x prices; no wall-clock; not a verdict. *)

(* measured: polynomials, A's (setup-region entries 20.955 minus the pre-loop entry), candidates, B, M *)
P = 156.0421875; A = 20.955 - 1; nc = 1012.748; B = 1754.33; M = 1056.15;
(* per-type counts per number: reference and root alone *)
ref = <|"mult" -> 117.0, "fb" -> 7877.86, "setup_euclid" -> 15595.84, "setup_small" -> 16125.92,
  "sieve_update" -> 751178.61, "sieve_scan" -> 329844.28, "confirm_td" -> 142064.29, "la" -> 49193.15,
  "sqrt_mul" -> 1070.54, "sqrt_gcd" -> 94.46, "lp_full" -> 71.92, "lp_small" -> 916.32, "word" -> 103028.95,
  "setup_gray" -> 35897.39, "hash" -> 1910.27, "sort_cmp" -> 2350.28, "f64_log" -> 3651.9, "f64_div" -> 25.47,
  "root_test" -> 0.|>;
root = Join[ref, <|"setup_small" -> 16263.74, "confirm_td" -> 12363.0, "word" -> 152250.29, "root_test" -> 135730.56|>];
(* prices *)
ruint = <|"mult" -> 0.306483228338059, "fb" -> 0.306483228338059, "setup_euclid" -> 0.31640537369859184,
  "setup_small" -> 0.306483228338059, "sieve_update" -> 0.0258, "sieve_scan" -> 0.012353034197935398,
  "confirm_td" -> 0.11413041479569133, "la" -> 0.016729369623819032, "sqrt_mul" -> 1.0, "sqrt_gcd" -> 0.6173133713596427,
  "lp_full" -> 1.0, "lp_small" -> 0.11413041479569133, "word" -> 0.0258, "setup_gray" -> 0.0258, "hash" -> 0.3638,
  "sort_cmp" -> 0.1169, "f64_log" -> 0.1063, "f64_div" -> 0.19, "root_test" -> 0.0581|>;
mont = <|"mult" -> 1.1372719610668551, "fb" -> 1.1372719610668551, "setup_euclid" -> 1.1904923737799407,
  "setup_small" -> 1.1372719610668551, "sieve_update" -> 0.0951, "sieve_scan" -> 0.04662733476523205,
  "confirm_td" -> 0.4260079932573883, "la" -> 0.0628857290448873, "sqrt_mul" -> 1.0, "sqrt_gcd" -> 2.2911557597672707,
  "lp_full" -> 1.0, "lp_small" -> 0.4260079932573883, "word" -> 0.0951, "setup_gray" -> 0.0951, "hash" -> 1.3427,
  "sort_cmp" -> 0.4315, "f64_log" -> 0.3923, "f64_div" -> 0.7011, "root_test" -> 0.2142|>;
official = AssociationMap[1. &, Keys[ref]];
fmt[x_] := Round[x, 0.0001];
cost[t_, pr_] := Total[KeyValueMap[#2 pr[#1] &, t]];

(* derived per-structure counts *)
Tp = root["root_test"]/nc;                          (* sieved odd primes per candidate *)
Rg = ref["setup_gray"]/(P - A);                    (* roots per polynomial, from Gray updates (one per root per switch) *)
hits = root["confirm_td"] - ref["confirm_td"] + nc (Tp + 1);  (* nc (cnt + even): first divisions by hits and an even v *)
Rw = (root["word"] - ref["word"] - nc - hits)/P;    (* roots per polynomial, from root mode's extra word (A-prime hits ~0 assumed) *)
F = Tp + 2 + 4;                                    (* base size, candidate-weighted (s = 4) *)
Print["inputs: P ", P, " A ", A, " P/A ", P/A, " nc ", nc, " nc/P ", nc/P, " B ", B, " M ", M, " F ~ ", F];
Print["derived: primes tested per candidate Tp ", Tp, "; roots per polynomial ", Rg, " (Gray) / ", Rw, " (word); hits+even per candidate ", hits/nc];
R = Rg; negfrac = 0.5;   (* share of candidates with x < 0: assumed symmetric interval *)

check = Table[{pn, cost[root, pr]/cost[ref, pr]}, {pn, {"official", "ruint", "montgomery"}}, {pr, {Switch[pn, "official", official, "ruint", ruint, _, mont]}}];
Print["check, today's root / reference (measured 1.0379 / 0.9051 / 0.9014): ", Flatten[check, 1]];

(* options as changes to root alone's counts (word only; root_test, confirm_td unchanged), and per-polynomial / per-A / per-candidate word *)
opts = {
  {"today", 0, R, 0, 0},
  {"1 in-place store", 2 Tp A, R, 2 Tp, 0},
  {"2-literal (sign fix on x<0)", -R P + 2 Tp A + negfrac nc Tp, 0, 2 Tp, negfrac Tp},
  {"2-fused (sign fix in root_test)", -R P + 2 Tp A, 0, 2 Tp, 0},
  {"2' root mode only", -2 R P + (R + 2 Tp) A, -R, R + 2 Tp, 0}};
prices = {{"official", official}, {"ruint", ruint}, {"montgomery", mont}};
Print["option | dword/number | word per polynomial (vs full pass) | word per A | extra word per candidate | official | ruint | montgomery (ratio to the reference)"];
Do[With[{t = Join[root, <|"word" -> root["word"] + o[[2]]|>]},
  Print[o[[1]], " | ", Round[o[[2]]], " | ", o[[3]], " | ", o[[4]], " | ", o[[5]], " | ",
    Table[fmt[cost[t, p[[2]]]/cost[ref, p[[2]]]], {p, prices}]]], {o, opts}];
(* 2' card-wide: the reference also keeps offsets in the Gray code *)
newref = Join[ref, <|"word" -> ref["word"] - R P + R A|>];
t2 = Join[root, <|"word" -> root["word"] - 2 R P + (R + 2 Tp) A|>];
Print["2' card-wide: new reference / reference ", Table[fmt[cost[newref, p[[2]]]/cost[ref, p[[2]]]], {p, prices}],
  "; root / new reference ", Table[fmt[cost[t2, p[[2]]]/cost[newref, p[[2]]]], {p, prices}]];
(* sensitivity of 2-literal to the negative share, and of 2-fused to a root_test re-price *)
Print["2-literal official at negfrac 0.3 / 0.5 / 0.7: ", Table[fmt[cost[Join[root, <|"word" -> root["word"] - R P + 2 Tp A + f nc Tp|>], official]/cost[ref, official]], {f, {0.3, 0.5, 0.7}}]];
Print["2-fused ruint with root_test x 1.0 / 1.1 / 1.25: ", Table[fmt[cost[Join[root, <|"word" -> root["word"] - R P + 2 Tp A|>], Join[ruint, <|"root_test" -> 0.0581 s|>]]/cost[ref, ruint]], {s, {1.0, 1.1, 1.25}}]];
