(* W5 (reduced): light-meter per-number check (model, not a verdict; information only).
   I-033 asks for predicted against measured yield per decile of numbers at 72 / 84 / 96. The repo does not hold that:
   - stage F (evolve/stagef.json, 352cfa8) ran the yield model on stage B's 8 map numbers per size, at 84 and 96 only (no 72);
   - measured true fulls and partials (evolve/step9.json) are pooled per size, not per number.
   So no decile curve is possible. What is per number in stagef.json: polynomials to completion and combinations,
   model (given stage B's pooled capture) against the card. Those are checked here: does one factor fit, and does the model
   rank the numbers? Copied from evolve/stagef.json rows: {polys_model, polys_card, combos_model, card_combos}. *)
f[x_, d_] := ToString[NumberForm[N@x, {8, d}], OutputForm];
data = <|"84" -> {{74.7467, 88, 42.9532, 36}, {51.1849, 58, 42.7766, 52}, {47.9477, 51, 43.0424, 45}, {115.7763, 102, 48.8537, 53}, {76.3492, 82, 44.7062, 49}, {93.3153, 75, 47.2093, 48}, {44.5860, 48, 42.8722, 40}, {75.2278, 80, 45.4071, 55}}, "96" -> {{122.0691, 121, 70.1982, 57}, {85.0344, 81, 64.0908, 57}, {174.0058, 207, 71.7579, 82}, {164.0650, 189, 64.3167, 74}, {143.9925, 117, 69.5730, 76}, {268.1332, 325, 67.1304, 68}, {129.6699, 144, 67.5772, 51}, {119.9254, 101, 71.3314, 91}}|>;
Do[With[{x = data[b]}, Module[{pm = x[[All, 1]], pc = x[[All, 2]], cm = x[[All, 3]], cc = x[[All, 4]], k, resid, lm},
  Print["== ", b, " bits (8 numbers)"];
  Print["  polynomials to completion, model / card per number: ", f[#, 3] & /@ (pm/pc)];
  k = Total[pc]/Total[pm]; resid = pc - k pm;
  lm = LinearModelFit[Transpose[{Log[pm], Log[pc]}], z, z];
  Print["  one factor (card = k x model): k = ", f[k, 3], "; residual sd after the factor ", f[100 StandardDeviation[resid/pc], 1], "% of card; before ", f[100 StandardDeviation[(pc - pm)/pc], 1], "%"];
  Print["  log card on log model: slope ", f[lm["BestFitParameters"][[2]], 3], " (95% ", f[#, 3] & /@ lm["ParameterConfidenceIntervals"][[2]], "); slope 1 = a single factor fits"];
  Print["  ranking: Spearman rho (model vs card) ", f[SpearmanRho[pm, pc], 3], "; Pearson on logs ", f[Correlation[Log[pm], Log[pc]], 3]];
  Print["  combinations, model / card per number: ", f[#, 2] & /@ (cm/cc), "; Spearman rho ", f[SpearmanRho[cm, cc], 3]];
  Print["  over-count against the card by model-polys rank (rank 1 = fewest predicted polynomials = highest predicted yield):"];
  With[{o = Ordering[pm]}, Print["    ", Table[f[pm[[i]]/pc[[i]], 3], {i, o}]]]]], {b, {"84", "96"}}];
