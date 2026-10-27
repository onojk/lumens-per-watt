(* Open meter questions, cost notes only (NOTES, "Open meter questions: cost notes (overnight stage 5)"). Model, not a
   verdict; no code changed. Inputs copied from card counts (lampcore --types, card 6031239; the 2'a reference = goff 1,
   all map numbers), Python traces (40 numbers per size: A's per number, F), lampcore --phasetime with confirm = resieve
   (every 8th number; priced counts only) and the LPBREAK passes of runs B (72, 84; 6810e24) and A (96; 3816bb4):
   sub-timers on, ns net of the per-region overhead. *)
ruP = <|"setup_small" -> 0.306483228338059, "hash" -> 0.3638|>;
moP = <|"setup_small" -> 1.1372719610668551, "hash" -> 1.3427|>;
tot = <|72 -> {149728.8, 8743.21, 31113.85}, 84 -> {454579.6, 22337.98, 80953.42}, 96 -> {1425117.1, 58145.28, 213006.40}|>;  (* official, ruint, Montgomery *)
wall = <|72 -> 787.0, 84 -> 1650.2, 96 -> 3825.8|>;  (* 2'a wall per number, us at 2.4 GHz (runs B and A) *)
red = <|72 -> 386.0, 84 -> 1000.9, 96 -> 2707.1|>;   (* A x (F - 2) per number: one A mod p per base prime per A *)
hash = <|72 -> 570.87, 84 -> 920.77, 96 -> 1910.27|>;
lp = <|72 -> <|"copy" -> {13.25, 250.52, 302.91}, "hash" -> {24.34, 182.67, 267.96}|>,   (* us, ruint, calls *)
       84 -> <|"copy" -> {41.94, 427.87, 488.47}, "hash" -> {38.71, 296.43, 432.30}|>,
       96 -> <|"copy" -> {153.06, 899.23, 993.97}, "hash" -> {109.94, 640.54, 916.31}|>|>;
rs = <|72 -> {947.36, 1000.09}, 84 -> {3616.96, 1644.94}, 96 -> {13849.39, 2426.80}|>;  (* resieve on: resieve, confirm region ruint *)
pc[x_] := Round[100 x, 0.01];
Print["== 1. audit item 17: A mod p per base prime per A, uncharged; typed setup_small (a small-modulus reduction) =="];
Do[Module[{n = red[s]},
   Print[s, " bits: ", Round[n, 0.1], " reductions per number (lower: once per prime; upper x2: Rust reduces twice for non-A primes)"];
   Print["   added share of the total, official / ruint / Montgomery: lower ", pc[n/tot[s][[1]]], "% / ", pc[n ruP["setup_small"]/tot[s][[2]]], "% / ", pc[n moP["setup_small"]/tot[s][[3]]],
     "%; upper ", pc[2 n/tot[s][[1]]], "% / ", pc[2 n ruP["setup_small"]/tot[s][[2]]], "% / ", pc[2 n moP["setup_small"]/tot[s][[3]]], "%"]], {s, {72, 84, 96}}];
Print["== 2. the large-prime hash: measured against its price; and the 1.4-1.7x of step 3 =="];
Do[Module[{rate = wall[s]/tot[s][[2]], h = lp[s]["hash"], pr},
   pr = h[[2]] rate;
   Print[s, " bits: cell rate ", Round[1000 rate, 0.1], " ns per ruint; lp:hash ", h[[1]], " us measured (sub-timers on) against ", Round[pr, 0.1], " us priced = ",
     Round[h[[1]]/pr, 0.01], "x; ", Round[1000 h[[1]]/h[[3]], 0.1], " ns per lookup against ", Round[1000 pr/h[[3]], 0.1], " priced"];
   Print["   at 1.4-1.7x: unpriced ", Round[0.4 hash[s] ruP["hash"], 0.1], "..", Round[0.7 hash[s] ruP["hash"], 0.1], " ruint = ", pc[0.4 hash[s] ruP["hash"]/tot[s][[2]]], "..",
     pc[0.7 hash[s] ruP["hash"]/tot[s][[2]]], "% of ruint; at the measured ratio: ", Round[h[[1]] - pr, 0.1], " us = ", pc[(h[[1]] - pr)/wall[s]], "% of wall"]], {s, {72, 84, 96}}];
Print["== 3. kept-relation copies =="];
Do[Module[{rate = wall[s]/tot[s][[2]], c = lp[s]["copy"], pr},
   pr = c[[2]] rate;
   Print[s, " bits: ", c[[3]], " copies per number; ", Round[1000 c[[1]]/c[[3]], 0.1], " ns per copy measured (sub-timers on) against ", Round[1000 pr/c[[3]], 0.1],
     " ns priced (", Round[c[[2]]/c[[3]], 0.001], " ruint each) = ", Round[c[[1]]/pr, 0.01], "x; excess ", Round[c[[1]] - pr, 0.1], " us = ", pc[(c[[1]] - pr)/wall[s]], "% of wall"]], {s, {72, 84, 96}}];
Print["== 4. re-sieve: the priced cost of the walk region (confirm = resieve), for the measurement to come =="];
Do[Print[s, " bits: resieve region ", rs[s][[1]], " ruint (", pc[rs[s][[1]]/tot[s][[2]]], "% of 2'a's ruint), confirm with re-sieve ", rs[s][[2]],
   " ruint; at 2'a's cell rate the walk would be priced at ", Round[rs[s][[1]] wall[s]/tot[s][[2]], 0.1], " us"], {s, {72, 84, 96}}];
