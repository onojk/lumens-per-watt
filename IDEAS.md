# Ideas and opportunities

A running log of new ideas, opportunities and method changes for lumens-per-watt, with how each was evaluated and what was decided. It is separate from predictions (NOTES.md), candidate moves (MOVES.md) and the plan (PLAN.md): an idea lives here until it is adopted, parked or rejected, and adopted ideas move to MOVES.md or PLAN.md.

## Rules

1. When to add or review entries (checkpoints):
   - a scored result lands (a round, a sealed check, a replacement test);
   - a phase or meter correction closes;
   - an outside-reviewer round finishes;
   - a surprise: a result far from every prediction, a meter hole, a failed acceptance or parity check;
   - otherwise, at least once per working session.
   At each checkpoint: add any new ideas, and check parked entries whose revisit trigger has fired.
2. Who proposes:
   - Claude chat proposes at every checkpoint, without being asked.
   - Claude Code may add entries found while working (marked "Claude Code"), but never acts on them without the user's decision.
   - Outside reviewers' suggestions are entered with their source.
   - The user decides.
3. Every entry has:
   - ID (I-001, I-002, ...), date, source, and the trigger (what result or event prompted it);
   - the idea in plain English, mapped to the concept deck (lamps, walls, towers, the theta line) where it fits; new concepts only when nothing in the deck serves;
   - why now: the evidence behind it, with pointers to NOTES or commits;
   - expected payoff and cost, each labelled "computed" (with the arithmetic) or "estimated";
   - interactions and risks (what it could break or confound);
   - recommended timing: now / after a named step / park with a revisit trigger;
   - decision (user, with date): adopted (and where it went: MOVES row or PLAN section), parked (with its revisit trigger), or rejected (with the reason);
   - outcome, once known (link to the result).
4. Evaluation, in priority order:
   - measurement integrity first: anything that finds or prevents meter holes, mispricing or confounding goes ahead of performance ideas and may enter the current queue;
   - then payoff per cost, the strength of the evidence, and whether it reuses existing machinery;
   - ideas never jump the queue otherwise; they are scheduled.
5. Ideas are not predictions. If an idea makes a quantitative claim that a result will test, register it as a prediction in NOTES.md before the result, with falsification criteria.
6. Nothing is deleted. Rejected and parked entries stay, with their reasons; superseded entries point to what replaced them.
7. Each checkpoint review ends with a one-line summary in NOTES.md: "Ideas checkpoint (date): added I-..., decided I-..., parked triggers checked."

## Log

### I-001 — Charged integer types in lampcore (uncharged op becomes a compile error)
- Date: 2026-10-26. Source: Claude chat. Trigger: four meter holes in one night (audit items 0, 9, 10, 11), all arithmetic written outside the meter.
- Idea: hot-path numbers live in small wrapper types (word-level value, small-modulus residue, mod-N number) whose arithmetic requires the meter and charges by type automatically. The classification rule is carried by the types, so an uncharged op or a mis-typed op mostly cannot compile.
- Why now: holes found by reading code, one at a time; the audit is in progress.
- Payoff: structural prevention of meter holes and mis-typing (estimated: removes most of the audit's failure classes). Cost: a refactor of lampcore's hot paths plus parity (estimated: large).
- Interactions: must keep op counts identical (parity) except where it reveals real holes, which are then meter corrections reported separately. Performance of lampcore must not drop materially.
- Recommended timing: after the 2x2. The Phase 1 watt meter then checks a meter correct by construction.
- Decision: pending.

### I-002 — Score the reviewers, not only their predictions
- Date: 2026-10-26. Source: Claude chat. Trigger: dozens of scored predictions from DeepSeek, Grok and Claude chat, with recurring error patterns (wrong base, wrong old price, reversed falsifiers, internally inconsistent ranges).
- Idea: a small table per reviewer: hit rate (ranges held), calibration (stated confidence vs outcome), and error types. Used to weight their input and to pre-empt recurring slips in each new seed or update.
- Why now: NOTES already holds every score.
- Payoff: better-weighted outside input; fewer annotation rounds (estimated). Cost: a one-off tally from NOTES (estimated: small); then one line per scored prediction.
- Interactions: none on the card or meter. Claude chat is scored by the same table.
- Recommended timing: now, as a one-off tally; keep it only if it proves useful.
- Decision: pending.

### I-003 to I-007 — The Illumination program (watt meter, price map, light spectrum, hazard monitor, dark mass)
- Date: 2026-10-26. Source: Claude chat. Trigger: the user's question about better measures than a single efficiency number.
- Decision: adopted (user, Oct 26) as the Illumination program; see PLAN.md, "Illumination program (Oct 26)", and the five MOVES rows.

### I-008 — Index rule for the hazard monitor (Gittins / Sidney prefix ratio)
- Date: 2026-10-26. Source: Claude chat. Trigger: the dark-mass prototype's one-step greedy lost 2-5% at 84-96 (rho's toll).
- Idea: score each lamp by its best AVERAGE light per cost over any continuation (from now to its best stopping level) and run that whole stretch; qs's index = remaining dark mass / qs cost. This is the correct form of Phase 4's hazard monitor ("how bright does this lamp get once its toll is paid"), and it makes Phases 4 and 5 one mechanism.
- Why now: the one-step rule's failure is structural, not a tuning issue.
- Payoff/cost: estimated; being tested by the user's next Mathematica run (index rule vs fixed vs one-step). Cost: small (a scheduler change in the prototype; later in the harness).
- Recommended timing: settle in the prototype now; carry into Phase 4's design in PLAN.md.
- Decision: superseded by I-009 (2026-10-26); kept as a diagnostic (a lamp's toll) in the Phase 4 picture.
- Outcome: works (0-2.7% above the exact DP optimum) but unnecessary in this model; NOTES, "Index rule and the exact optimum".

### I-009 — Re-prioritize the Illumination program after the DP result
- Date: 2026-10-26. Source: Claude chat. Trigger: the exact DP optimum is within 0.2-1.3% of the best fixed pipeline; the theta prior is worth 25-45%.
- Idea: (a) Phase 3 (light spectrum per theta band) moves to the front after Phase 1; (b) Phases 4-5 become diagnostic and explanatory (the dark-mass picture, a lamp's toll), not production schedulers, unless Phase 3's measured curves reopen the gap (re-run the DP on measured curves: cheap); (c) every "best pipeline" claim names its theta prior / test-set composition.
- Why now: NOTES, "Index rule and the exact optimum" and "Dark-mass scheduler prototype".
- Decision: pending.

### I-010 — Check the card's small-factor end at 72 bits
- Date: 2026-10-26. Source: Claude chat. Trigger: the DP optimum uses trial division to ~2^15-2^16 instead of rho at 72.
- Idea: confirm whether the evolved pipelines at 72 include a td stage with a free bound, and whether td could replace rho there; an information step from existing results first.
- Note (Claude Code, from the code): the size-scaling pipelines fix td off (sizescale.pipeline sets td's ob = 0); td's depth was searched only in the 84-bit partition study (turned off there). So td at 72 has not been tested in the current pipelines.
- Decision: pending.

### I-011 — Use the primehelix theta distribution as the prior for Phase 3 and the dark-mass work
- Date: 2026-10-26. Source: Claude chat, from the user's primehelix repo (github.com/onojk/primehelix; paper "On the Distribution of Smaller Factors in Semiprimes", submitted to Integers).
- Trigger: the dark-mass prototype needed a prior over theta = log p / log N and used an improvised 1/(theta(1-theta)).
- Idea: use the paper's measured P(N, theta0) (exact to 1e8-1e9) and its heuristic P ~ 1 - f(theta0)/log log N, f(theta0) = log(1/theta0) - theta0 - log 2 + 1/2 (density ~ (1/theta + 1)/log log N), as the random-semiprime prior at 72-96 bits. Heuristic values: P(theta <= 0.1 / 0.2 / 0.3 / 0.4) = 0.49 / 0.69 / 0.82 / 0.92 at 72 bits, 0.52 / 0.71 / 0.83 / 0.92 at 96. Conditioned on p >= 2^8 it agrees closely with the improvised prior (96 bits: 9% vs 8% below 0.1; 68% vs 65% below 0.3), so the prototype's conclusions stand.
- Use: (a) Phase 3 reports per theta band and weights bands by P(N, theta0) when a "random semiprime" summary is wanted; (b) every "best pipeline" claim names its prior (balanced/RSA-style vs random semiprime); (c) the dark-mass DP is re-run with this prior once measured lamp curves exist.
- Caveat: the constant 1/2 is conjectural in the paper; 72-96 bits is far beyond enumeration, so it is a heuristic prior and is labelled as such.
- Caveat (DeepSeek review, Oct 26, accepted): it is an extrapolation (C = 1/2 open, in-sample fit only); report the finite-N drift of the fitted constant and the sensitivity to the conditioning cut. The relevant cut is the pipeline's own trial-division bound, so the prior is quoted conditioned on p above that bound, at several bounds, and labelled as an extrapolation.
- Not useful (recorded so it isn't revisited): primehelix's geometric/spectral embeddings (the paper's own separation result: theta is not recoverable from n alone) and residue labels (they need the factors first).
- Decision: pending.

### I-012 — The theta tower: primehelix's spine/skin visual as the Illumination picture
- Date: 2026-10-26. Source: Claude chat, from the user's primehelix repo (scripts/primehelix_viz.py).
- What exists: semiprimes split into lopsided (bit gap > 8, wound on a helix "skin", colored by residue family) and balanced (on the central axis, the "spine"). The helix angle is list order; the repo's own test (helix_factor_prediction_test.py; datasets/clustering_results.json: z = 0.40, not significant) shows it carries no factor information -- "visualization only".
- Idea: rebuild it with theta in the geometry: radius proportional to (1/2 - theta) (balanced on the spine, lopsided outward), height = log N. Then each lamp lights a SHELL; a pipeline run animates trial division lighting the outer skin, rho / p-1 moving inward, qs lighting the spine; the unlit volume is the dark mass. Shell populations follow the paper's P(N, theta0) (I-011).
- Use: the visual for Phase 3 (light spectrum) and Phase 5 (dark mass); film material for the Lumens Per Watt video.
- Cost: small (a visualization over existing spectrum data; no meter change). Recommended timing: with Phase 3 output.
- Decision: pending.
- Tooling (user's repos): render with laser-beam-demo's deterministic GLSL pipeline, or start from geom_factor's manim scenes (bit_bucket_prime_towers*). Narration line from the user's essay reuse-and-the-wall: "no slope, no warmer, no colder, just no, until suddenly yes". The dark-mass picture is the warmer/colder signal a factoring run otherwise lacks.

### I-013 — Restart schedules for rho (Luby / "lotto"): decided against, with reason
- Date: 2026-10-26. Source: Claude chat, from the user's Cprime (factor_luby.sh, rho_driver.cpp) and rsacrack (lotto_factor.py) repos.
- What exists: rho run as many short restarted runs, on a Luby schedule (Cprime) or as random short "tickets" (rsacrack).
- Why not: rho's chance of success grows with the square of its effort (the birthday bound; the "toll" in NOTES, "Dark-mass scheduler prototype"), so it gets more likely to finish the longer it runs. A restart throws away toll already paid. Restart schedules pay only when run times are heavy-tailed.
- Check (no new run): when Phase 4's hazard monitor measures rho's light curve per theta band, confirm the curve rises. If some band shows a flat or falling curve (e.g. a bad polynomial constant), restarts are worth reopening for that band only.
- Decision: pending (recommended: not adopted; keep as the Phase 4 check).

### I-014 — GMP-ECM as an independent check on the ECM lamp
- Date: 2026-10-26. Source: Claude chat, from the user's ECC-Tools repo (a CLI over libecm / GMP-ECM). Reuse rule: use GMP-ECM itself (an oracle in the harness, never in a charged path).
- Trigger: no scheduler in the dark-mass runs ever chose ECM; that is either true or a sign the ECM lamp is under-lit.
- Idea: on a fixed set of known primes at 16-48 bits, compare the fraction found per curve by our ECM and by GMP-ECM at the same B1 (stage 1 only, then with stage 2). Information only; no card change.
- If ours is lower by more than the run-to-run noise, the ECM lamp curve in Phase 3 is understated and the dark-mass result on ECM is re-run.
- Cost: small. Timing: with Phase 3.
- Update (2026-10-26, the user's stage-2 DP): ECM pays at 96 bits only with a cheap stage 2 (2 multiplies per prime: chosen; 6: not chosen), so the GMP-ECM cross-check should cover stage 2 and our stage-2 cost per prime (ours: <= 3 multiplies per prime with pairing, plus giant steps ~0.25 per candidate and ~4-5 word ops; NOTES, "Stage 2 in the cards today").
- Decision: pending.

### I-015 — Adaptivity belongs inside qs, not between lamps
- Date: 2026-10-26. Source: Claude chat, from the DeepSeek review. Trigger: with found / not-found lamps the optimal schedule is open-loop (NOTES, "DeepSeek's reply (Oct 26) on the dark-mass results").
- Idea: aim Phase 4's hazard monitor at qs's own progress signals (relations per polynomial, large-prime cycle growth, the projected finish time) to decide when to stop sieving, change polynomials, or move to linear algebra.
- Information first: log those signals in the next qs runs.
- Cost: small (logging).
- Decision: pending.

### I-016 — Stage 2 for p-1 (and ECM)
- Date: 2026-10-26. Source: Claude chat, from the user's DP. Trigger: in the model, stage 2 cuts expected cost about 6-7% at every size (up to 12.5% at 96 with ECM), pending the undercharge fix.
- Idea, information step first (from the code): do lampcore's p-1 and ECM have a stage 2? If not, cost a plain prime-by-prime stage 2 (B2 = 100 B1) as a new lamp option, priced by the op meter's existing types.
- Information step answered (Claude Code, from the code): p-1 has no stage 2; its cost model is already written (NOTES, "pm1 stage 2: cost model", Oct 25; MOVES row "pm1 stage 2 (B2 = c x B)"), with predictions pre-registered. ECM has a baby-step giant-step stage 2 (B2 = 50 B1 by default; NOTES, "Stage 2 in the cards today").
- Decision: pending.
