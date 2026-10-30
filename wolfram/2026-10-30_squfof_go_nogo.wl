(* Family (2) SQUFOF-like, go / no-go (the user's ruling, Oct 30): the expected cost ratio against rho per pricing, with
   the MEASURED A = alpha (1 + beta) (explore/squfof_constants.py, de2dd03; the multiplier sequence S2, mean and 95% interval)
   and the per-pricing word-division price D (7c96549: op-class v1 1 by definition; ruint and Montgomery timed; official 1).
   Per form step: (D + 6) word + root_test on half the forward steps (a share 1 / (2 (1 + beta)) of all steps); per number:
   ~2 gcd(N, P) (the measured reverse attempts), one isqrt (2 mul) per multiplier (1.0). rho: mean training cost per number
   per pricing (arrangement-v1's re-run record). Worst-of = max over op-class v1, ruint, Montgomery, scaled gcd (the family's
   set; official reported, no veto). A model, never a verdict. *)
w  = <|"official" -> 1, "ruint" -> 0.03, "montgomery" -> 0.10, "opclass_v1" -> 55.5685, "scaled" -> 55.5685|>;
rt = <|"official" -> 1, "ruint" -> 0.06, "montgomery" -> 0.21, "opclass_v1" -> 52.2928, "scaled" -> 52.2928|>;
mu = <|"official" -> 1, "ruint" -> 1, "montgomery" -> 1, "opclass_v1" -> 554.8616, "scaled" -> 554.8616|>;
gc[pr_, b_] := Switch[pr, "official", 1, "ruint", 7.86, "montgomery", 29.06, "opclass_v1", 1401.7489,
   "scaled", <|48 -> 356.9, 64 -> 355.8, 80 -> 501.6|>[b]];   (* gcd(N, P): P < sqrt(kN) < 2^64, the small-k curve (v2) *)
dd[pr_, b_] := If[MemberQ[{"ruint", "montgomery"}, pr], <|48 -> 4.01, 64 -> 4.01, 80 -> 4.76|>[b], 1];
rho = <|48 -> <|"official" -> 7368.1, "ruint" -> 7636.1, "montgomery" -> 8464.1, "opclass_v1" -> 4121359.7, "scaled" -> 4096112.5|>,
        64 -> <|"official" -> 113566.6, "ruint" -> 117053.6, "montgomery" -> 127827.6, "opclass_v1" -> 63444227.2, "scaled" -> 63204438.5|>,
        80 -> <|"official" -> 1963752.6, "ruint" -> 2024000.6, "montgomery" -> 2210153.4, "opclass_v1" -> 1097048485.6, "scaled" -> 1096520722.4|>|>;
q4 = <|48 -> 3534.0, 64 -> 56631.9, 80 -> 895761.8|>;
Am = <|48 -> {3.18, 3.55, 3.95}, 64 -> {2.80, 3.13, 3.48}, 80 -> {3.06, 3.67, 4.39}|>;   (* {low, mean, high} *)
be = <|48 -> 0.956, 64 -> 0.897, 80 -> 0.945|>;
att = <|48 -> 1.98, 64 -> 1.89, 80 -> 2.05|>;
cost[pr_, b_, A_] := A q4[b] ((dd[pr, b] + 6) w[pr] + rt[pr]/(2 (1 + be[b]))) + 2 mu[pr] + att[b] gc[pr, b];
prs = {"official", "ruint", "montgomery", "opclass_v1", "scaled"};
Do[
  Print[b, " bits (A low / mean / high = ", Am[b], "):"];
  Do[Print["   ", pr, ": ", StringRiffle[ToString[NumberForm[cost[pr, b, #]/rho[b][pr], {4, 3}]] & /@ Am[b], " / "]], {pr, prs}];
  Print["   worst-of (op-class, ruint, Montgomery, scaled): ",
    StringRiffle[ToString[NumberForm[Max[Table[cost[pr, b, #]/rho[b][pr], {pr, {"ruint", "montgomery", "opclass_v1", "scaled"}}]], {4, 3}]] & /@ Am[b], " / "],
    "  (binding: ", First@MaximalBy[{"ruint", "montgomery", "opclass_v1", "scaled"}, cost[#, b, Am[b][[1]]]/rho[b][#] &], ")"];
  Print["   break-even A under the worst-of: ",
    N[Round[Min[Table[A /. First@Solve[cost[pr, b, A] == rho[b][pr], A], {pr, {"ruint", "montgomery", "opclass_v1", "scaled"}}]], 0.01]]],
  {b, {48, 64, 80}}];
