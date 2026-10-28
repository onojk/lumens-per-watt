(* Forecast for the fixed-size partials table (NOTES.md, "Cost note (before code): a fixed-size partials table"); a
   model, not a verdict; the rho rule (PROTOCOL.md). Inputs (measured, balanced band, 80 numbers; the second gap run's
   callgrind files, lampcore f6aa08d; the hash op counts from lampcore --types):
   HashMap get + insert, inclusive instructions per number: 0.1949 / 0.2957 / 0.6763 M (SipHash, hashbrown probes, the
   rehashes as the map grows from empty)
   hash ops per number (charged: lookups and inserts): 580 / 922 / 1924
   the card's instructions per number after div64 (evolve/div64_check.out): 5.270 / 12.082 / 30.957 M
   New cost per op: c instructions, c in [15, 30] (a multiplicative hash, a probe or two, the compare, the store);
   plus the table's clear once per attempt (about 2 k instructions, AVX2 memset; included as 2 k per number). *)
old = {0.1949, 0.2957, 0.6763} 10^6;
ops = {580, 922, 1924};
tot = {5.270, 12.082, 30.957} 10^6;
rem[c_] := old - c ops - 2000;
Print["instructions removed per number (M), c = 15 / 22.5 / 30: ",
  ToString[NumberForm[Table[rem[c]/10^6, {c, {15, 22.5, 30}}], {4, 3}], OutputForm]];
share[c_] := rem[c]/tot;
Print["instruction share removed (%), c = 22.5: ", ToString[NumberForm[100 share[22.5], {4, 2}], OutputForm]];
(* rho: the removed code is mostly class (a), hashing arithmetic and probes into a table that fits in L2 (lower side
   extended to 0.40, Grok's direction); the upper side extended to 1.20 for the rehashes' block moves (class b-like). *)
Print["wall change (%), rho 0.40 / 0.85 / 1.20, c = 22.5: ",
  ToString[NumberForm[Table[-100 r share[22.5], {r, {0.40, 0.85, 1.20}}], {4, 2}], OutputForm]];
Print["band (%), rho in [0.40, 1.20], c in [15, 30]: ",
  ToString[NumberForm[Transpose[{-100 1.20 share[15], -100 0.40 share[30]}], {4, 2}], OutputForm]];
