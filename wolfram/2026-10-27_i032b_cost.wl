(* I-032 2'b cost model with exact structural counts (NOTES, "I-032 option 2'b: root confirm reads the kept offsets —
   cost model"). Model, not a verdict; inputs copied from card runs and Python traces made before any 2'b code.
   96 bits, means per number over the 640 map numbers, card a6d67a2 (2'a built, 2'b not).
   Base counts: the reference and today's root mode (run_many --types, Oct 27; the same inputs as
   2026-10-27_i032_cost.wl, f12ae23). Structure (Python traces of the reference genes, all 640 numbers; polynomials
   and setup_gray agree exactly with lampcore): *)
P = 156.0421875;          (* polynomials *)
nA = 19.9546875;          (* A's *)
nst = 2638.0765625;       (* sieved odd primes, summed over A's (132.2 per A) *)
rpoly = 41162.74375;      (* sieved roots, summed over polynomials: today's root pass, word x roots *)
gray = 35897.3875;        (* setup_gray = sieved roots x (polynomials - 1), summed over A's *)
rA = rpoly - gray;        (* sieved roots, summed over A's: 2'a's per-A conversion *)

ref = <|"mult" -> 117.0, "fb" -> 7877.86, "setup_euclid" -> 15595.84, "setup_small" -> 16125.92,
  "sieve_update" -> 751178.61, "sieve_scan" -> 329844.28, "confirm_td" -> 142064.29, "la" -> 49193.15,
  "sqrt_mul" -> 1070.54, "sqrt_gcd" -> 94.46, "lp_full" -> 71.92, "lp_small" -> 916.32, "word" -> 103028.95,
  "setup_gray" -> 35897.39, "hash" -> 1910.27, "sort_cmp" -> 2350.28, "f64_log" -> 3651.9, "f64_div" -> 25.47,
  "root_test" -> 0.|>;
root = Join[ref, <|"setup_small" -> 16263.74, "confirm_td" -> 12363.0, "word" -> 152250.29, "root_test" -> 135730.56|>];
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
prices = {{"official", official}, {"ruint", ruint}, {"montgomery", mont}};
cost[t_, pr_] := Total[KeyValueMap[#2 pr[#1] &, t]];
fmt[x_] := Round[x, 0.0001];

(* today's root mode against the reference: the per-polynomial pass (rpoly) plus per-candidate words *)
percand = root["word"] - ref["word"] - rpoly;
(* 2'a: the reference with the sieve's per-root start-offset word replaced by the per-A conversion: word - gray (exact, a6d67a2 acceptance) *)
a2 = Join[ref, <|"word" -> ref["word"] - gray|>];
(* 2'b: 2'a plus root confirm without its per-polynomial pass; per A, ka (first-root index) and tm (reciprocal) built, 2 word per sieved prime;
   per candidate unchanged (root_test x primes, the low-bit test, the merged list); no negative-x handling (offsets are in sieve coordinates, i0 >= 0) *)
b2 = Join[a2, <|"setup_small" -> root["setup_small"], "confirm_td" -> root["confirm_td"], "root_test" -> root["root_test"],
   "word" -> a2["word"] + percand + 2 nst|>];
(* the same 2'b with the earlier estimate's per-A build (2 x 134.02 primes x 19.955 A's), for the comparison *)
Print["structure: P ", P, ", A ", nA, ", P/A ", P/nA, ", sieved primes per A ", nst/nA, ", roots per polynomial ", rpoly/P, ", roots per A ", rA/nA];
Print["per-candidate root-mode word per number ", percand, " (", percand/1012.748, " per candidate)"];
Print["2'b word changes against 2'a: +", percand, " per-candidate, +", 2 nst, " per-A ka and tm; root pass removed (", rpoly, " not charged)"];
Print["model 2'a / REF: ", Table[fmt[cost[a2, p[[2]]]/cost[ref, p[[2]]]], {p, prices}], "  (f12ae23: 0.9754 / 0.9843 / 0.9842)"];
Print["model 2'b / 2'a (exact structure): ", Table[fmt[cost[b2, p[[2]]]/cost[a2, p[[2]]]], {p, prices}], "  (f12ae23: 1.0137 / 0.8877 / 0.8838)"];
Print["model 2'b / REF (information): ", Table[fmt[cost[b2, p[[2]]]/cost[ref, p[[2]]]], {p, prices}]];
Print["model 2'b / today's root (information): ", Table[fmt[cost[b2, p[[2]]]/cost[root, p[[2]]]], {p, prices}]];
