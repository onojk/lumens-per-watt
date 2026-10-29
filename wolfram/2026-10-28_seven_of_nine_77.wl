N0 = 77;
dots = Flatten[Table[{k/n, n}, {n, 1, N0 - 1}, {k, 1, n}], 1];
top = Table[{k/N0, N0, k}, {k, 1, N0}];
hit = Select[top, GCD[#[[3]], N0] > 1 &];
free = Complement[top, hit];
lab[k_] := With[{r = k/N0}, Row[{Numerator[r], " of ", Denominator[r]}]];
g = Graphics[{
   {GrayLevel[0.75], PointSize[0.004], Point[dots]},
   {RGBColor[0.55, 0.7, 0.9], PointSize[0.006], Point[free[[All, ;; 2]]]},
   {Red, Dashed, Thin,
    Line[{{#[[1]], N0}, {#[[1]], Denominator[#[[1]]]}}] & /@ hit},
   {Red, PointSize[0.009], Point[hit[[All, ;; 2]]],
    Point[{#[[1]], Denominator[#[[1]]]} & /@ hit]},
   {Red, Text[Style[lab[#[[3]]], 7], {#[[1]], Denominator[#[[1]]]}, {0, 1.6}] & /@ hit}},
  Frame -> True, FrameLabel -> {"value k/n (0 to 1)", "tower n"},
  AspectRatio -> 0.6, ImageSize -> 1200,
  PlotLabel -> Row[{"Tower 77 dropped on towers 1-76: ", Length[hit],
     " collisions (p+q-1), ", Length[free], " on fresh ground (phi)"}]];
Export["seven_of_nine_77.png", g]
