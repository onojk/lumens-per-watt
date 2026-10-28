(* Light spectrum v1 plot (post hoc, information only; data: evolve/light_spectrum.csv from the sealed run 721af65).
   Light = successes per million op-class v1 units, each lamp alone, per theta band (lower edge), per size; log scale;
   a lamp with no success in a band is not drawn there. Shaded (post hoc): bands where the best non-QS lamp's light is
   within 2.5x of QS's under op-class v1 (the committed twilight definition used ruint, under which CFRAC's lumped type
   is unpriced). *)
data = Import[FileNameJoin[{DirectoryName[$InputFileName], "..", "evolve", "light_spectrum.csv"}], "CSV"];
rows = Rest[data];
lamps = {"td", "rho", "pm1", "ecm", "cfrac", "qs"};
panel[bits_] := Module[{sel, series, tw},
  sel = Select[rows, #[[1]] == bits &];
  series = Table[Select[{#[[2]] + 0.01, #[[6]]} & /@ Select[sel, #[[3]] == l &], #[[2]] > 0 &], {l, lamps}];
  tw = Select[Union[sel[[All, 2]]], Function[lo,
      Module[{c = Select[sel, #[[2]] == lo &], q, o},
        q = First[Select[c, #[[3]] == "qs" &]][[6]];
        o = Max[Select[c, #[[3]] != "qs" &][[All, 6]]];
        q > 0 && 0.4 <= o/q <= 2.5]]];
  Show[
   ListLogPlot[series, Joined -> True, PlotMarkers -> Automatic, PlotLegends -> lamps,
    Frame -> True, FrameLabel -> {"theta (smaller factor bits / N bits)", "light: successes per 10^6 op-class units"},
    PlotLabel -> ToString[bits] <> " bits", ImageSize -> 520,
    Epilog -> {Opacity[0.15], Gray, Table[Rectangle[{lo, -20}, {lo + 0.02, 20}], {lo, tw}]}]]];
g = GraphicsColumn[{panel[72], panel[84], panel[96]}, ImageSize -> 600];
Export[FileNameJoin[{DirectoryName[$InputFileName], "..", "evolve", "light_spectrum_v1.png"}], g];
Print["exported light_spectrum_v1.png"];
