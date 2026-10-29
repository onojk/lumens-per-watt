(* Value-line lens cross-check (the user's "Seven of Nine" card, stage 1, Oct 28): information only.
   For N = 77: the collision tags of tower N on smaller towers, the fresh / collision counts, and EulerPhi.
   For semiprimes N = p q with odd primes p < q < 200: collisions (k = 1..N, GCD[k, N] > 1) = N - EulerPhi[N] = p + q - 1. *)
n0 = 77;
col = Select[Range[n0], GCD[#, n0] > 1 &];
Print["N = 77: collisions ", Length[col], ", fresh ", n0 - Length[col], ", EulerPhi ", EulerPhi[n0]];
Print["tags: ", StringRiffle[(ToString[#] <> " of 77 -> " <> ToString[Numerator[#/n0]] <> " of " <> ToString[Denominator[#/n0]]) & /@ col, ", "]];
Print["lowest tower = N / GCD[k, N] for every collision: ", AllTrue[col, Denominator[#/n0] == n0/GCD[#, n0] &]];
ps = Prime[Range[2, PrimePi[200]]];
pairs = Select[Tuples[ps, 2], #[[1]] < #[[2]] &];
chk = ({p, q} |-> With[{N = p q}, {Count[Range[N], k_ /; GCD[k, N] > 1], N - EulerPhi[N], p + q - 1}]) @@@ pairs;
Print["semiprimes checked: ", Length[pairs], "; collisions == N - EulerPhi == p + q - 1 on all: ",
  AllTrue[chk, Equal @@ # &]];
