(* Wall forecast for the allocation change (NOTES.md, "Cost note (before code): allocate once per attempt"); a model,
   not a verdict. Inputs (measured, balanced band, 80 numbers):
   removed allocation Ir per number at the targeted sites (evolve/alloc_estimate.out): 1.961 / 2.107 / 2.728 M
   the card's Ir per number (evolve/gap_table.out): 8.215 / 15.597 / 35.820 M
   the card's wall per number, balanced band (Run C, the current card): 0.876 / 1.592 / 3.425 ms
   Model: saved wall = k * removed Ir * (card wall / card Ir); k = the allocator's time per instruction relative to the
   card's average. k = 1 is proportional; the band k in [0.7, 2.0] (malloc / free: pointer-chasing, branchy code, lower
   IPC than the card's loops, upper end; freed cache lines and fewer page touches, lower end). The removed Ir counts only
   the libc allocator's instructions, not the Rust wrappers (RawVec grow, drop glue) around them: a lower bound. *)
sizes = {72, 84, 96};
rem = {1.961, 2.107, 2.728};
ir = {8.215, 15.597, 35.820};
wall = {0.876, 1.592, 3.425};
frac[k_] := k rem/ir;
Print["instruction share removed (%): ", ToString[NumberForm[100 rem/ir, {4, 1}], OutputForm]];
Do[Print["k = ", k, ": wall change (%) at 72 / 84 / 96: ", ToString[NumberForm[-100 frac[k], {4, 1}], OutputForm],
   "; ms per number saved: ", ToString[NumberForm[k rem wall/ir, {4, 3}], OutputForm]], {k, {0.7, 1.0, 1.3, 2.0}}];
Print["forecast band (k in [0.7, 2.0]), wall change (%): ",
  ToString[Table[NumberForm[{-100 frac[2.0][[i]], -100 frac[0.7][[i]]}, {4, 1}], {i, 3}], OutputForm],
  "; central (k = 1): ", ToString[NumberForm[-100 frac[1.0], {4, 1}], OutputForm]];
