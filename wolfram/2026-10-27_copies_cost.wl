(* Stage 3: kept-relation copies, cost note (model, not a verdict; information only; no code or meter change).
   Inputs, copied from committed or session outputs:
   - mean priced cost per number of 2'a and 2'b, all map numbers, lampcore --types (the frozen release binary), under
     op-class v1, ruint, Montgomery, official: {bits, 2'a x4, 2'b x4};
   - evolve/copybench_run.json (capped 2,400 MHz, core 2, 5 replicates, medians): {bits, kept relations per number,
     A-prime mean base index, ns per kept relation for the s = 4 A-prime lookups (qs.rs 607 pos: a linear scan),
     ns per copy alone}; 100-128 bits are model inputs (log-linear in bits);
   - word prices: op-class v1 55.57 Ir, ruint 0.0258, Montgomery 0.0951, official 1;
   - the reference's wall per number (Stage 2, evolve/baseline_msieve.out, the qs card): 846 / 1,594 / 3,540 us; 100-128
     from W2's 2'a wall model (4,796 / 8,068 / 13,572 / 29,612 us).
   Option (1), code: look up the A-primes' base indices once per A (2'b already computes them, `aj`) instead of a linear
     scan per kept relation. Counts identical: no priced change; wall saved = kept x lookup ns.
   Option (2), meter: keep the code and charge the scan, one word per base entry compared: 4 (index + 1) per kept
     relation, added to 2'a and 2'b alike (identical relations and A's). *)
f[x_, d_] := ToString[NumberForm[N@x, {9, d}], OutputForm];
pr = {"op-class", "ruint", "Montgomery", "official"};
wp = {55.568512, 0.0258, 0.0951, 1.0};
means = {{72, 6504340.082851, 8743.208368, 31113.847241, 149728.831250, 5630640.836674, 7777.660619, 27441.686690, 155769.850000}, {84, 16029031.616439, 22337.980156, 80953.415832, 454579.628571, 13293088.682860, 19431.776198, 69927.382826, 465596.725000}, {96, 39658433.587089, 58145.277224, 213006.401595, 1425117.065625, 33454272.321742, 51614.636177, 188250.972482, 1444618.898438}};
bench = {{72, 296, 21.600000, 46.610000, 22.910000}, {84, 462, 38.700000, 81.820000, 22.420000}, {96, 927, 79.500000, 165.060000, 51.860000}, {100, 1075.300437, 96.557542, 184.990000, 88.070000}, {108, 1573.231004, 149.081582, 245.960000, 78.330000}, {116, 2301.734202, 230.176926, 339.200000, 85.580000}, {128, 4073.326124, 441.589231, 567.840000, 70.090000}};
wall = <|72 -> 846., 84 -> 1594., 96 -> 3540., 100 -> 4796., 108 -> 8068., 116 -> 13572., 128 -> 29612.|>;
Print["== Option (1), the code fix (counts identical): wall saved per number"];
Do[With[{b = r[[1]], k = r[[2]], ns = r[[4]]}, Print["  ", b, " bits", If[b > 96, " (model)", ""], ": ", f[k, 0], " kept x ", f[ns, 1], " ns = ",
   f[k ns/1000, 1], " us per number, ", f[100 k ns/1000/wall[b], 2], "% of the reference's wall; 2'a and 2'b alike, so 2'b/2'a moves by under 0.1 point"]], {r, bench}];
Print["\n== Option (2), the re-price: extra word ops per number and the effect on 2'b / 2'a"];
Do[With[{b = r[[1]], a = r[[2 ;; 5]], bb = r[[6 ;; 9]], k = Select[bench, #[[1]] == r[[1]] &][[1]]},
  With[{dw = k[[2]] 4 (k[[3]] + 1)},
   Print["  ", b, " bits: + ", f[dw, 0], " word per number (", f[k[[2]], 0], " kept x 4 x (", f[k[[3]], 1], " + 1))"];
   Do[With[{d = dw wp[[i]]}, Print["      ", pr[[i]], ": 2'a +", f[100 d/a[[i]], 2], "%, 2'b +", f[100 d/bb[[i]], 2], "%; 2'b/2'a ",
      f[bb[[i]]/a[[i]], 4], " -> ", f[(bb[[i]] + d)/(a[[i]] + d), 4]]], {i, 4}]]], {r, means}];
Print["\nCaveat on option (2) under op-class: v1's word weight (55.6 Ir) is an average over heterogeneous word sites; one scan"];
Print["compare is about 1-2 instructions, so pricing it at the word weight would overprice it by about 30x (v1 issue 2)."];
