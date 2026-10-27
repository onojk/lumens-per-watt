(* W1: where root confirm (2'b vs 2'a) would cross 1.000 under official (model, not a verdict; information only).
   Inputs (deterministic priced ratios of mean cost over the map numbers, copied from committed run JSONs):
   72, 84 bits: evolve/shiftrun_C.json (2b-sizes); 96 bits: evolve/i032time.json (i032-2prime). Neither cell uses pp,
   so the free-2 correction (6031239) does not touch them.
   F (factor-base size, mean over all map numbers: 480 / 560 / 640) computed with Python traces of the reference
   genes with goff = 1 (no timing, no priced totals): 57.5 / 95.3 / 139.8 (card_params gives 138 at 96 from stage G).
   Three points: a straight line leaves one residual degree of freedom; any 3-parameter curve leaves none. *)
f[x_, d_] := ToString[NumberForm[N@x, {8, d}], OutputForm];
nb = {72, 84, 96}; nF = {57.5, 95.3, 139.8};
r = <|"official" -> {1.0403464, 1.0242358, 1.0136844}, "ruint" -> {0.8895660, 0.8698985, 0.8876841},
      "montgomery" -> {0.8819766, 0.8637978, 0.8837808}|>;
t1 = InverseCDF[StudentTDistribution[1], 0.975];
lineFit[xs_, ys_] := LinearModelFit[Transpose[{xs, ys}], z, z];
report[xs_, xname_, key_] := Module[{lm, a, b, s, cross, bands, lo, hi},
  lm = lineFit[xs, r[key]]; {a, b} = lm["BestFitParameters"]; s = Sqrt[lm["EstimatedVariance"]];
  Print["  ", key, " vs ", xname, ": intercept ", f[a, 5], ", slope ", f[b, 6], ", residual sd ", f[s, 5], ", R^2 ", f[Chop[lm["RSquared"], 10^-4], 4]];
  If[key == "official",
    cross = (1 - a)/b;
    bands = lm["MeanPredictionBands", ConfidenceLevel -> 0.95];
    lo = Quiet@Check[z /. FindRoot[bands[[1]] == 1, {z, cross}], Missing[]];
    hi = Quiet@Check[z /. FindRoot[bands[[2]] == 1, {z, cross}], Missing[]];
    Print["    official reaches 1.000 at ", xname, " = ", f[cross, 2], "; where the line's 95% band (t on 1 df = ", f[t1, 2], ") reaches 1.000: ",
      If[NumericQ[lo], f[lo, 2], "none"], " (lower edge) to ", If[NumericQ[hi], f[hi, 2], "none"], " (upper edge)"];
    {cross, lo, hi}, Null]];
Print["== Linear in bits"];
cb = report[nb, "bits", "official"];
report[nb, "bits", #] & /@ {"ruint", "montgomery"};
Print["\n== Linear in log F (natural log)"];
cf = report[Log[nF], "log F", "official"];
report[Log[nF], "log F", #] & /@ {"ruint", "montgomery"};
lf = lineFit[nb, Log[nF]];
bitsAt[lF_] := (lF - lf["BestFitParameters"][[1]])/lf["BestFitParameters"][[2]];
Print["    log F against bits on these three points: slope ", f[lf["BestFitParameters"][[2]], 4], " per bit, R^2 ", f[lf["RSquared"], 4],
  " (an extrapolation of F, itself a model)"];
Print["    so the log-F crossing, F = ", f[Exp[cf[[1]]], 0], ", sits at about ", f[bitsAt[cf[[1]]], 1], " bits (band ",
  If[NumericQ[cf[[2]]], f[bitsAt[cf[[2]]], 1], "none"], " to ", If[NumericQ[cf[[3]]], f[bitsAt[cf[[3]]], 1], "none"], " bits)"];

Print["\n== Other shapes for official's excess e = ratio - 1 (exact or near-exact through the three points)"];
e = r["official"] - 1;
Print["  excess ", f[#, 4] & /@ e, " at ", nb, " bits; drops ", f[#, 4] & /@ (-Differences[e]), " per 12 bits (ratio of drops ", f[Divide @@ Reverse[-Differences[e]], 3], ")"];
pw = NonlinearModelFit[Transpose[{nF, e}], cc FF^-pp, {{cc, 1}, {pp, 1}}, FF];
Print["  power law in F, e = c F^-p: p = ", f[pp /. pw["BestFitParameters"], 3], ", residual sd ", f[Sqrt[pw["EstimatedVariance"]], 5], "; e > 0 for every F: never crosses"];
pb = NonlinearModelFit[Transpose[{nb, e}], cc Exp[-kk (bb - 72)], {{cc, 0.04}, {kk, 0.04}}, bb];
Print["  exponential in bits, e = c exp(-k (bits - 72)): k = ", f[kk /. pb["BestFitParameters"], 4], " per bit, residual sd ", f[Sqrt[pb["EstimatedVariance"]], 5], "; never crosses"];
(* geometric drops with an offset: exact through 3 points *)
q = Divide @@ Reverse[-Differences[e]]; d1 = -Differences[e][[1]];
c0 = e[[1]] - d1/(1 - q);
Print["  exact 3-point exponential with offset, e = c0 + c1 q^((bits - 72)/12): q = ", f[q, 3], ", c0 = ", f[c0, 4],
  If[c0 > 0, " > 0: official levels off at " <> f[1 + c0, 4] <> ", never crosses", " < 0: crosses at " <> f[72 + 12 Log[q, -c0/(e[[1]] - c0)], 1] <> " bits"]];
qd = InterpolatingPolynomial[Transpose[{nb, e}], bb];
roots = Select[Cases[NSolve[qd == 0, bb, Reals], (bb -> v_) :> v, Infinity], # > 96 &];
Print["  quadratic in bits (exact): ", If[roots == {}, "no crossing after 96; minimum e = " <> f[MinValue[qd, bb], 4] <> " at " <> f[bb /. Last@Minimize[qd, bb], 1] <> " bits", "crosses at " <> f[Min[roots], 1] <> " bits"]];
