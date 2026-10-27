(* pp 3's meter-wall gap on 2'b (NOTES, "pp 3 on 2'b: the meter against wall-clock"). Post hoc (after the i032-2prime run,
   9b94247); model reconciliation, not a verdict. 96 bits, means per number over the 640 map numbers.
   Wall (us at 2.4 GHz): from the sealed run's i032time.json (8 replicates; only wall, sieve and confirm were saved, so
   the other regions are one remainder). Priced (ruint) per region: lampcore --phasetime's per-region type counts
   (counts only, ns discarded), with root_test added to confirm by hand (phasetime's per-region accumulator omits the
   root_test column). Per-type counts: run_many --types. *)
wall = <|"2'b" -> <|"total" -> 3407.9, "sieve" -> 968.6, "confirm" -> 606.3|>,
         "2'b+pp3" -> <|"total" -> 3475.3, "sieve" -> 906.5, "confirm" -> 732.0|>|>;
rootTest = <|"2'b" -> 135730.56, "2'b+pp3" -> 135730.56 + 28711.9|>; pRoot = 0.0581;
pr = <|"2'b" -> <|"mult" -> 61.8, "fb" -> 2414.4, "setup" -> 11092.1, "gray" -> 926.2, "sieve" -> 23455.0, "confirm" -> 1697.3, "lp_ledger" -> 1919.9, "solve" -> 2158.7|>,
       "2'b+pp3" -> <|"mult" -> 61.8, "fb" -> 2414.4, "setup" -> 10004.0, "gray" -> 834.3, "sieve" -> 21152.0, "confirm" -> 2100.1, "lp_ledger" -> 2294.2, "solve" -> 2183.3|>|>;
totalRuint = <|"2'b" -> 51614.6, "2'b+pp3" -> 50601.7|>;
polys = <|"2'b" -> 156.04, "2'b+pp3" -> 140.48|>; cands = <|"2'b" -> 1012.75, "2'b+pp3" -> 1227.42|>;
lp = <|"2'b" -> <|"copy" -> 994.0, "hash" -> 916.3, "comb" -> 71.9|>, "2'b+pp3" -> <|"copy" -> 1191.9, "hash" -> 1121.1, "comb" -> 78.6|>|>;
hashOps = 402.7; pHash = 0.3638;   (* type "hash": +402.7 ops per number, pp3 - 2'b *)
r[x_] := Round[x, 0.01];

regionPriced[c_] := <|"sieve" -> pr[c]["sieve"], "confirm" -> pr[c]["confirm"] + pRoot rootTest[c],
   "rest" -> Total[KeyDrop[pr[c], {"sieve", "confirm"}]]|>;
regionWall[c_] := <|"sieve" -> wall[c]["sieve"], "confirm" -> wall[c]["confirm"], "rest" -> wall[c]["total"] - wall[c]["sieve"] - wall[c]["confirm"]|>;
Print["check: regions' ruint + root_test = total: ", Table[{c, r[Total[regionPriced[c]]], totalRuint[c]}, {c, {"2'b", "2'b+pp3"}}]];
Print["region | wall 2'b -> pp3 (us, %) | ruint 2'b -> pp3 (%) | us per ruint 2'b, pp3 | wall change at 2'b's us/ruint | gap (wall above price, us)"];
Do[Module[{w0 = regionWall["2'b"][k], w1 = regionWall["2'b+pp3"][k], p0 = regionPriced["2'b"][k], p1 = regionPriced["2'b+pp3"][k], exp},
   exp = (p1 - p0) w0/p0;
   Print[k, " | ", r[w0], " -> ", r[w1], " (", r[100 (w1/w0 - 1)], "%) | ", r[p0], " -> ", r[p1], " (", r[100 (p1/p0 - 1)], "%) | ",
     Round[w0/p0, 0.0001], ", ", Round[w1/p1, 0.0001], " | ", r[exp], " | ", r[(w1 - w0) - exp]]], {k, {"sieve", "confirm", "rest"}}];
Print["total | wall ", r[100 (wall["2'b+pp3"]["total"]/wall["2'b"]["total"] - 1)], "% | ruint ", r[100 (totalRuint["2'b+pp3"]/totalRuint["2'b"] - 1)], "%"];
Print["per polynomial: sieve wall ", r[wall["2'b"]["sieve"]/polys["2'b"]], " -> ", r[wall["2'b+pp3"]["sieve"]/polys["2'b+pp3"]], " us; sieve ruint ",
  r[pr["2'b"]["sieve"]/polys["2'b"]], " -> ", r[pr["2'b+pp3"]["sieve"]/polys["2'b+pp3"]]];
Print["per candidate: confirm wall ", Round[wall["2'b"]["confirm"]/cands["2'b"], 0.0001], " -> ", Round[wall["2'b+pp3"]["confirm"]/cands["2'b+pp3"], 0.0001], " us"];
Print["large-prime table: partials looked up (lp:hash) ", lp["2'b"]["hash"], " -> ", lp["2'b+pp3"]["hash"], " (", r[100 (lp["2'b+pp3"]["hash"]/lp["2'b"]["hash"] - 1)],
  "%); kept-relation copies (lp:copy) ", lp["2'b"]["copy"], " -> ", lp["2'b+pp3"]["copy"], "; combinations ", lp["2'b"]["comb"], " -> ", lp["2'b+pp3"]["comb"]];
Print["hash hypothesis (hash at 1.4-1.7x its price): unpriced excess = (0.4..0.7) x ", r[hashOps pHash], " ruint = ", r[0.4 hashOps pHash], "..", r[0.7 hashOps pHash],
  " ruint, i.e. ", r[0.4 hashOps pHash wall["2'b"]["total"]/totalRuint["2'b"]], "..", r[0.7 hashOps pHash wall["2'b"]["total"]/totalRuint["2'b"]], " us at 2'b's mean us/ruint"];
