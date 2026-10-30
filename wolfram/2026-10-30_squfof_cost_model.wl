(* Cost model, before code: half-size square-form walks (SQUFOF-like), the next family (the user's ruling, Oct 30).
   Expected cost ratio against rho at 48 / 64 / 80 bits under official, ruint, Montgomery and op-class v1.
   A MODEL with two unmeasured constants and one pricing decision; never a verdict.

   Per form step (forward or reverse), all operands < 2 Sqrt[k N] < 2^64 for k N < 2^126 (one machine word):
     1 word division b = (P0 + P_i) div Q_i            -> D word ops (D: the pricing decision, see NOTES)
     2 word multiplies, 4 word adds / subtracts         -> 6 word ops
     forward only, every other step: a square test of Q_i -> 1/2 root_test (a residue filter + isqrt, word-size)
   Per number: S = A (k N)^(1/4) steps in all, A = alpha (1 + beta): alpha = forward steps / (k N)^(1/4) to the first
   proper square, beta = reverse steps / forward steps; one isqrt of k N per multiplier (charged 2 mul) and one
   gcd(N, P) (1 gcd); k = 1 here (multipliers raise S by k^(1/4) and change alpha; measured later).
   rho: its mean training cost per number per pricing (arrangement-v1's re-run record, 48 per size), copied below. *)
price = <|
  "official"   -> <|"word" -> 1, "root" -> 1, "mul" -> 1, "gcd" -> 1|>,
  "ruint"      -> <|"word" -> 0.03, "root" -> 0.06, "mul" -> 1, "gcd" -> 7.86|>,
  "montgomery" -> <|"word" -> 0.10, "root" -> 0.21, "mul" -> 1, "gcd" -> 29.06|>,
  "opclass_v1" -> <|"word" -> 55.5685, "root" -> 52.2928, "mul" -> 554.8616, "gcd" -> 1401.7489|>|>;
rho = <|48 -> <|"official" -> 7368.1, "ruint" -> 7636.1, "montgomery" -> 8464.1, "opclass_v1" -> 4121359.7|>,
        64 -> <|"official" -> 113566.6, "ruint" -> 117053.6, "montgomery" -> 127827.6, "opclass_v1" -> 63444227.2|>,
        80 -> <|"official" -> 1963752.6, "ruint" -> 2024000.6, "montgomery" -> 2210153.4, "opclass_v1" -> 1097048485.6|>|>;
q4 = <|48 -> 3534.0, 64 -> 56631.9, 80 -> 895761.8|>;   (* mean N^(1/4) of the training numbers *)
sq[pr_, b_, A_, D_] := Module[{p = price[pr], s = A q4[b]},
  s ((D + 6) p["word"] + p["root"]/2 (1/(1 + 0.5))) + 2 p["mul"] + p["gcd"]];
(* the square test runs on forward steps only, every other one: per step of S that is (1/2) alpha / (alpha (1 + beta));
   with beta = 1/2 assumed here for that share alone, 1/(2 (1 + 1/2)) of the steps *)
Print["rho, official ops per N^(1/4): ", Table[b -> Round[rho[b]["official"]/q4[b], 0.01], {b, {48, 64, 80}}]];
Do[
  Print["\nD = ", D, " word ops per word division"];
  Do[
    Print["  A = alpha (1 + beta) = ", A, ": ",
      StringRiffle[Table[pr <> " " <> StringRiffle[Table[ToString[b] <> ": " <> ToString[NumberForm[sq[pr, b, A, D]/rho[b][pr], {4, 3}]], {b, {48, 64, 80}}], ", "],
        {pr, {"official", "ruint", "montgomery", "opclass_v1"}}], "; "]],
    {A, {1.5, 3, 6}}],
  {D, {1, 20}}];
Print["\nbreak-even A (ratio = 1) at 80 bits: ",
  StringRiffle[Table[pr <> " D=1: " <> ToString[NumberForm[A /. First@Solve[sq[pr, 80, A, 1] == rho[80][pr], A], {4, 2}]] <>
    ", D=20: " <> ToString[NumberForm[A /. First@Solve[sq[pr, 80, A, 20] == rho[80][pr], A], {4, 2}]],
    {pr, {"official", "ruint", "montgomery", "opclass_v1"}}], "; "]];
