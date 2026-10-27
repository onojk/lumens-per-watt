(* Meter correction, cost note only (NOTES, "Meter correction (proposed): pp's free-2 initialisation"): pp's free-2
   initialisation (stage H: one stride-2 byte store over half the sieve interval per polynomial) is uncharged, under the
   width charge. If charged: one op per cell written, typed sieve_scan (proposed) or sieve_update (alternative),
   count per polynomial ceil((width - par)/2), i.e. sieve_scan/2 per number (sieve_scan = width per polynomial),
   within +-polys/2 (par is 0 or 1; width = 2M + 1 is odd). Model, not a verdict; counts copied from lampcore --types
   (run_many, Oct 27, card d269cc8; identical to the sealed runs' counts). Means per number over all map numbers
   (480 / 560 / 640). 2'b at 72 and 84 is deliberately left out (it is the subject of sealed predictions, 2b-sizes). *)
ruintP = <|"sieve_scan" -> 0.012353034197935398, "sieve_update" -> 0.0258|>;
montP = <|"sieve_scan" -> 0.04662733476523205, "sieve_update" -> 0.0951|>;
(* {official, ruint, montgomery, sieve_scan count} *)
d = <|
  72 -> <|"2'a" -> {149728.8312, 8743.2084, 31113.8472, 26802.7313}, "+0" -> {154059.5500, 7906.7102, 27911.4565, 23834.2979},
          "+1" -> {152291.7229, 7675.4784, 27061.5925, 25521.7167}, "+2" -> {152514.8208, 7510.6126, 26550.9998, 27443.1104}|>,
  84 -> <|"2'a" -> {454579.6286, 22337.9802, 80953.4158, 93988.3750}, "+0" -> {455467.8946, 19669.1150, 70754.4083, 85014.3732},
          "+1" -> {453986.7839, 19136.5844, 68853.9846, 89689.5089}, "+2" -> {459492.7214, 18960.8815, 68097.2613, 95613.3929}|>,
  96 -> <|"2'a" -> {1425117.0656, 58145.2772, 213006.4016, 329844.2766}, "2'b" -> {1444618.8984, 51614.6362, 188250.9725, 329844.2766},
          "+0" -> {1370608.8594, 50601.7086, 184380.7525, 296918.3469}, "+1" -> {1397547.3359, 50417.7557, 183613.4584, 314800.9625},
          "+2" -> {1444721.2047, 50867.2875, 185527.8065, 336959.2344}, "+3" -> {1509863.6453, 52001.4660, 189845.5595, 363185.9516}|>|>;
fmt[x_] := Round[x, 0.0001];
corr[v_, ty_] := Module[{n = v[[4]]/2}, {v[[1]] + n, v[[2]] + n ruintP[ty], v[[3]] + n montP[ty]}];
ratios[a_, b_] := fmt /@ (a/b);
Do[Module[{base = d[s]["2'a"][[1 ;; 3]]},
  Print["--- ", s, " bits (base 2'a, uncharged by pp, unchanged) ---"];
  Do[If[StringStartsQ[c, "+"],
     Module[{v = d[s][c], free2 = d[s][c][[4]]/2, r0, rs, ru},
      r0 = ratios[v[[1 ;; 3]], base]; rs = ratios[corr[v, "sieve_scan"], base]; ru = ratios[corr[v, "sieve_update"], base];
      Print["2'b+pp3 ", c, ": free-2 writes per number ", Round[free2, 0.1], " (", Round[100 free2/v[[1]], 0.01], "% of official)"];
      Print["   as now (official/ruint/Montgomery): ", r0, " robust ", Max[r0]];
      Print["   charged as sieve_scan (proposed):   ", rs, " robust ", Max[rs]];
      Print["   charged as sieve_update (altern.):  ", ru, " robust ", Max[ru]]]], {c, Keys[d[s]]}]], {s, {72, 84, 96}}];
Print["--- 96 bits, 2'b+pp3 against 2'b (2'b has no pp: unchanged) ---"];
Do[Module[{v = d[96][c], b = d[96]["2'b"][[1 ;; 3]]},
   Print[c, ": as now ", ratios[v[[1 ;; 3]], b], "; sieve_scan ", ratios[corr[v, "sieve_scan"], b], "; sieve_update ", ratios[corr[v, "sieve_update"], b]]],
  {c, {"+0", "+1", "+2", "+3"}}];
Print["count bound: +-polys/2 per number, at most ", fmt[0.5/2113.], " of the free-2 count at 96 (width ~2,113)"];
