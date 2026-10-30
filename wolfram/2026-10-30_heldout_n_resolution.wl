(* Held-out set size per size needed to resolve +/-5% (arrangement-v1 round notes, the user's request, Oct 30).
   Inputs: the 95% paired-bootstrap intervals of the sealed scoring run f527a0a (48 numbers per size, seeds 9930000 + bits),
   copied here. Model: the interval's half-width shrinks as 1/Sqrt[n] (central-limit scaling of a ratio of means over
   paired numbers), so n(5%) = 48 (w / 0.05)^2, w = relative half-width = (hi - lo) / 2 / point. A model, not a verdict. *)
n0 = 48;
rows = {
  {"cost/rho at 64 bits, op-class v1", 0.98962, 0.82960, 1.17760},
  {"cost/rho at 80 bits, op-class v1", 0.98724, 0.80290, 1.21900},
  {"cost/rho at 64 bits, robust", 0.99283, 0.83090, 1.18020},
  {"cost/rho at 80 bits, robust", 0.98765, 0.80660, 1.21830},
  {"G_rho 48-80, worst-of", 0.96796, 0.91258, 1.02749},
  {"D-44 band average (64, 80)", 0.98840, 0.86110, 1.13310}
};
Do[
  {name, pt, lo, hi} = r;
  w = (hi - lo)/2/pt;
  n5 = n0 (w/0.05)^2;
  Print[name, ": relative half-width at n = 48: ", N[Round[100 w, 0.1]], "%; n for +/-5%: ",
    Ceiling[n5], "; for +/-10%: ", Ceiling[n0 (w/0.10)^2]],
  {r, rows}];
