(* Forecast for the 64-bit division of hits (NOTES.md, "Cost note (before code): divide hits in 64-bit hardware
   steps"); a model, not a verdict; the rho rule (PROTOCOL.md, counts-identical changes). Inputs (measured, balanced
   band, 80 numbers, the current card f6aa08d; evolve/div_calls.json from the second gap run's callgrind files):
   calls into __modti3 / __divti3 from "divide hits" and "A-prime and even checks", per number: 8430 / 13705 / 20875
   their inclusive instructions per number: 0.4955 / 0.8058 / 1.2276 M (58-60 per call)
   the card's instructions per number: 5.776 / 12.906 / 32.212 M
   New cost per division, inline 64-bit (v < 2^64: v <= M sqrt(kN / 2), about 2^61 at 96 bits): c instructions,
   c in [5, 10] (the divide, the zero test, the update, the loop branch). *)
calls = {8430, 13705, 20875};
old = {0.4955, 0.8058, 1.2276} 10^6;
tot = {5.776, 12.906, 32.212} 10^6;
rem[c_] := old - c calls;
Print["instructions removed per number (M), c = 5 / 7.5 / 10: ",
  ToString[NumberForm[Table[rem[c]/10^6, {c, {5, 7.5, 10}}], {4, 3}], OutputForm]];
share[c_] := rem[c]/tot;
Print["instruction share removed (%), c = 7.5: ", ToString[NumberForm[100 share[7.5], {4, 2}], OutputForm],
  "; range over c in [5, 10]: ", ToString[NumberForm[{100 share[10], 100 share[5]}, {4, 2}], OutputForm]];
(* rho: the measured class (b) default 0.85-1.06; the removed code is class (a), register-resident arithmetic in a
   software routine (the lower side extended to 0.40, Grok's direction); the upper side extended to 1.30 because the
   change also halves the hardware divides per hit (the quotient and the remainder from one divide), a long-latency
   instruction that counts as one. *)
lo = 0.40; mid = 0.85; hi = 1.30;
Print["wall change (%), rho 0.40 / 0.85 / 1.30, c = 7.5: ",
  ToString[NumberForm[Table[-100 r share[7.5], {r, {lo, mid, hi}}], {4, 2}], OutputForm]];
Print["band (%), rho in [0.40, 1.30] and c in [5, 10]: ",
  ToString[NumberForm[Transpose[{-100 hi share[5], -100 lo share[10]}], {4, 2}], OutputForm]];
