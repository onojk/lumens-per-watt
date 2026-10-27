(* W2: kept-relation copies (lp:copy): wall excess over price against size, and a forecast to 100-128 bits
   (model, not a verdict; information only).
   Inputs, copied from evolve/meterhealth_run.json (overnight stage 4b, information only; cap 2,400 MHz, AC), cell 2'a:
   - timed wall per number (mean of 4 replicates, flags off) and the cell's ruint total -> the cell's rate (ns per ruint);
   - the breakdown pass (sub-timers on): lp:copy wall, its ruint price, and copies per number (calls).
   Cross-check: shiftrun_B (72, 84) and shiftrun_A / i032shift (96) give lp:copy 13.2 / 41.9 / 153.0 us for 2'a, against
   12.9 / 37.2 / 157.4 here. Sub-timer overhead is inside lp:copy's wall (not measured separately).
   Excess = copy wall - copy ruint x cell rate (the stage-5 definition; 0.59 / 1.33 / 2.59 x price, +94 us at 96). *)
f[x_, d_] := ToString[NumberForm[N@x, {8, d}], OutputForm];
nb = {72, 84, 96}; nF = {57.5, 95.3, 139.8};
wall = {788.6, 1644.3, 3754.1}; cellRu = {8743.2, 22338.0, 58145.3};
copyUs = {12.9, 37.2, 157.4}; copyRu = {250.5, 427.9, 899.2}; calls = {302.9, 488.5, 994.0};
rate = wall/cellRu;   (* us per ruint *)
excess = copyUs - copyRu rate;
Print["Measured (2'a): per size ", nb];
Print["  copies per number ", f[#, 0] & /@ calls, "; ns per copy ", f[#, 1] & /@ (1000 copyUs/calls), "; ruint per copy ", f[#, 3] & /@ (copyRu/calls)];
Print["  cell rate ", f[#, 1] & /@ (1000 rate), " ns per ruint; copy wall / price ", f[#, 2] & /@ (copyUs/(copyRu rate))];
Print["  excess ", f[#, 1] & /@ excess, " us per number; share of wall ", f[#, 2] & /@ (100 excess/wall), "%; copies' whole wall share ", f[#, 2] & /@ (100 copyUs/wall), "%"];
(* log-linear in bits for each factor; 1 residual df each *)
fitLog[ys_] := LinearModelFit[Transpose[{nb, Log[ys]}], z, z];
mods = <|"calls" -> fitLog[calls], "nsPerCopy" -> fitLog[1000 copyUs/calls], "ruPerCopy" -> fitLog[copyRu/calls], "rate" -> fitLog[rate], "wall" -> fitLog[wall]|>;
Print["\nLog-linear fits in bits (growth per 12 bits; R^2):"];
KeyValueMap[Print["  ", #1, ": x", f[Exp[12 #2["BestFitParameters"][[2]]], 3], " per 12 bits, R^2 ", f[#2["RSquared"], 4]] &, mods];
Print["  ns per copy against F (power): exponent ", f[(LinearModelFit[Transpose[{Log[nF], Log[1000 copyUs/calls]}], z, z])["BestFitParameters"][[2]], 2],
  " (a copy moves an F-length list: exponent 1 would be linear in list length)"];
fc[k_, b_] := Exp[mods[k][b]];
t1 = InverseCDF[StudentTDistribution[1], 0.975];
Print["\nForecast (each factor extrapolated log-linearly; model A):"];
Print["  bits | copies | ns/copy | copy wall us | excess us | wall us | excess share | copy share"];
Do[With[{c = fc["calls", b], ns = fc["nsPerCopy", b], ru = fc["ruPerCopy", b], rt = fc["rate", b], w = fc["wall", b]},
  With[{cw = c ns/1000, ex = c ns/1000 - c ru rt},
    Print["  ", b, " | ", f[c, 0], " | ", f[ns, 0], " | ", f[cw, 0], " | ", f[ex, 0], " | ", f[w, 0], " | ", f[100 ex/w, 1], "% | ", f[100 cw/w, 1], "%"]]], {b, {96, 100, 108, 116, 128}}];
(* model B: ns per copy grows only as fast as from 84 to 96 is not assumed; instead it saturates at the 96 value (cache-resident limit already hit) *)
Print["\nModel B (ns per copy held at the 96 value, 158 ns: the growth stops; copies and wall extrapolated as in A):"];
Do[With[{c = fc["calls", b], ns = 1000 copyUs[[3]]/calls[[3]], ru = fc["ruPerCopy", b], rt = fc["rate", b], w = fc["wall", b]},
  With[{cw = c ns/1000, ex = c ns/1000 - c ru rt},
    Print["  ", b, " | ", f[c, 0], " | ", f[ns, 0], " | ", f[cw, 0], " | ", f[ex, 0], " | ", f[w, 0], " | ", f[100 ex/w, 1], "% | ", f[100 cw/w, 1], "%"]]], {b, {100, 108, 116, 128}}];
Print["\nUncertainty: each log-linear fit has one residual degree of freedom (t = ", f[t1, 1], "). 95% band on ns per copy at 128 bits: ",
  f[Exp[mods["nsPerCopy"]["MeanPredictionBands", ConfidenceLevel -> 0.95][[1]] /. z -> 128], 0], " to ",
  f[Exp[mods["nsPerCopy"]["MeanPredictionBands", ConfidenceLevel -> 0.95][[2]] /. z -> 128], 0], " ns."];
