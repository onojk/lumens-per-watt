(* W3: cross-run drift of wall ratios (model, not a verdict; information only).
   Inputs: per-replicate paired wall ratios (cell / base, same replicate) copied from committed run JSONs:
   evolve/i032time.json (i032-2prime), i032shift.json (pp3-gap-and-shift), shiftrun_A.json (shift-past-2),
   shiftrun_B.json (shift-72-84), shiftrun_C.json (2b-sizes), meterhealth_run.json (overnight stage 4b, info only).
   Every run: cap 2,400 MHz, AC, same S2.map_nums numbers per size. Only cell pairs timed in two or more runs.
   "2'b+pp3" in i032-2prime is the +0 shift. Units: points = 100 x ratio. *)
data = {{"72 bits: 2'b / 2'a", {{"2b-sizes", {0.9007383801, 0.9091559505, 0.9059120578, 0.9082775642, 0.8862372703, 0.9024606993, 0.9067511128, 0.9107005404}}, {"meterhealth", {0.8907790194, 0.9014271571, 0.9073103934, 0.8946515835}}}},
 {"84 bits: 2'b / 2'a", {{"2b-sizes", {0.8627796223, 0.8584314457, 0.8745313184, 0.8809319659, 0.8696355820, 0.8871146959, 0.8595086039, 0.8722303833}}, {"meterhealth", {0.8750441132, 0.8778257739, 0.8708531358, 0.8632356310}}}},
 {"96 bits: 2'b / 2'a", {{"i032-2prime", {0.8818251161, 0.8852103750, 0.8998646147, 0.8771020276, 0.8830174845, 0.8778591049, 0.8858296859, 0.8803337128}}, {"shift-past-2", {0.8761535826, 0.8985074729, 0.8981698749, 0.8850133724, 0.8891567361, 0.8878293688, 0.8869647543, 0.8798247079}}, {"meterhealth", {0.8838850683, 0.8814064151, 0.8817279068, 0.8999022937}}}},
 {"96 bits: 2'b+pp3 +0 / 2'a", {{"i032-2prime", {0.9093908252, 0.8755477672, 0.9170091883, 0.9173059854, 0.8956525352, 0.9172340727, 0.9012484096, 0.8776786430}}, {"pp3-gap-and-shift", {0.8861869398, 0.9165384049, 0.9095255212, 0.9490474382, 0.8915649026, 0.9172423275, 0.8968881042, 0.8819518301}}}},
 {"96 bits: 2'b+pp3 +0 / 2'b", {{"i032-2prime", {1.0312598367, 0.9890843939, 1.0190523922, 1.0458372647, 1.0143089473, 1.0448534025, 1.0174059686, 0.9969840189}}, {"2b-sizes", {1.0314858370, 1.0110997854, 1.0615098173, 1.0515739213, 1.0287805973, 1.0142897756, 1.0585365644, 1.0233057825}}}},
 {"96 bits: 2'b+pp3 +1 / 2'a", {{"pp3-gap-and-shift", {0.8995853615, 0.8913766198, 0.8869948908, 0.9138611981, 0.8805411133, 0.8873403465, 0.8920316654, 0.8819062796}}, {"shift-past-2", {0.8758688599, 0.9100238003, 0.9000567348, 0.8822252619, 0.8837140611, 0.9131742754, 0.8920369518, 0.8956091568}}}},
 {"96 bits: 2'b+pp3 +2 / 2'a", {{"pp3-gap-and-shift", {0.8693200820, 0.8801478263, 0.8600452651, 0.8865130384, 0.8654024042, 0.8557791699, 0.8373552852, 0.8652540149}}, {"shift-past-2", {0.8670000781, 0.8731387417, 0.8960105141, 0.8899692211, 0.8730478222, 0.8736235683, 0.8714031925, 0.8966205243}}}}};
f[x_, d_] := ToString[NumberForm[N@x, {8, d}], OutputForm];
pts[r_] := 100 r;
stats[runs_] := Table[With[{x = pts[r[[2]]]}, {r[[1]], Length[x], Mean[x], Variance[x]/Length[x]}], {r, runs}];
Print["Per group: run, n, mean (points), within-run s.e. of the mean (points)"];
Do[Print[g[[1]]]; Do[Print["   ", s[[1]], "  n=", s[[2]], "  mean ", f[s[[3]], 2], "  se ", f[Sqrt[s[[4]]], 2]], {s, stats[g[[2]]]}], {g, data}];

(* random-effects model per group: run mean m_i = mu_g + b_i + e_i, b_i ~ N(0, tau^2), e_i ~ N(0, se_i^2); tau^2 shared across groups *)
qstat[t2_, sel_] := Total[Table[With[{s = stats[g[[2]]]}, With[{w = 1/(s[[All, 4]] + t2)}, With[{mb = Total[w s[[All, 3]]]/Total[w]}, Total[w (s[[All, 3]] - mb)^2]]]], {g, data[[sel]]}]];
dfof[sel_] := Total[Length[#[[2]]] - 1 & /@ data[[sel]]];
analyse[sel_, label_] := Module[{q0, df, c, t2dl, up, lo, sew, cross, crossup},
  q0 = qstat[0, sel]; df = dfof[sel];
  c = Total[Table[With[{w = 1/stats[g[[2]]][[All, 4]]}, Total[w] - Total[w^2]/Total[w]], {g, data[[sel]]}]];
  t2dl = Max[0, (q0 - df)/c];
  up = Quiet@If[qstat[0, sel] <= InverseCDF[ChiSquareDistribution[df], 0.025], 0, t2 /. FindRoot[qstat[t2, sel] == InverseCDF[ChiSquareDistribution[df], 0.025], {t2, 1}]];
  lo = If[q0 <= InverseCDF[ChiSquareDistribution[df], 0.975], 0, t2 /. FindRoot[qstat[t2, sel] == InverseCDF[ChiSquareDistribution[df], 0.975], {t2, 1}]];
  sew = Sqrt[Median[Flatten[Table[stats[g[[2]]][[All, 4]], {g, data[[sel]]}]]]];
  Print["\n== ", label, ": groups ", Length[sel], ", df ", df];
  Print["  Cochran Q (tau=0) = ", f[q0, 2], " on ", df, " df; p = ", f[1 - CDF[ChiSquareDistribution[df], q0], 3]];
  Print["  between-run sd tau: DL ", f[Sqrt[t2dl], 2], " points; Q-profile 95% [", f[Sqrt[lo], 2], ", ", f[Sqrt[up], 2], "]"];
  Print["  typical within-run s.e. of a run's mean ratio: ", f[sew, 2], " points (8-replicate runs dominate)"];
  cross = 1.96 Sqrt[2 t2dl + 2 sew^2]; crossup = 1.96 Sqrt[2 up + 2 sew^2];
  Print["  95% half-width for (run X ratio) - (run Y ratio), same cell pair: DL ", f[cross, 2], " points; at tau's upper bound ", f[crossup, 2]];
  Print["  95% half-width for one run's ratio as an estimate of the long-run ratio: ", f[1.96 Sqrt[t2dl + sew^2], 2], " (upper ", f[1.96 Sqrt[up + sew^2], 2], ")"]];
all = Range[Length[data]];
analyse[all, "all repeated groups"];
noMeter = Select[all, ! StringContainsQ[data[[#, 1]], "+0 / 2'b"] &];
analyse[noMeter, "excluding 96 +0 / 2'b (its two runs straddle the free-2 meter correction, 6031239)"];
only2b = Select[all, StringContainsQ[data[[#, 1]], "2'b / 2'a"] &];
analyse[only2b, "2'b / 2'a only (the adoption-relevant pair)"];
