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
- Update (2026-10-26, the corrected DP): with stage 2, td to 2^12 is in the optimum at 72 under every prior and at 84 and 96 under several. Strengthens the td re-solve.
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
- Also measure the effective ECM size divisor (the DP uses 12; DeepSeek's estimate is about 24.5). If it is about 24, the 96-bit ECM gain is understated.
- Dickman overstates smoothness at small bounds (B 2^8: about 15-25% for random integers); ECM at B1 = 2^8 inherits this, so the 96-bit ECM gain may be overstated; this offsets DeepSeek's torsion-24.5 argument. The GMP-ECM measurement decides.
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
- Update (2026-10-26, the corrected DP): it keeps a 3.9-5.5% saving from p-1 stage 2 at every size. Shape: a short stage 1 (B 2^7-2^9), one stage 2 to about 100 B. Our p-1 has none today (3a7320f; cost model written). Recommended: adopt after the current meter queue, as a lamp change with a sealed prediction and the usual per-band gate.
- Update (2026-10-26, the real-prime measurement run): not sealed. The measured comparison at 2 multiplies per prime loses at 72 and 84 (+8.4% / +2.9%) and saves 1.8% at 96. Next: (1) from the code, the plain stage-2 cost per prime we would actually get, and whether prime pairing is cheap to add (answered in NOTES: gap stepping 2 mul + 3 word per prime; paired BSGS ~1.1-1.4 multiply-equivalents); (2) a DP rerun at that cost with c = 1.4 / 1.8, rho at K/1.4 and B2/B1 in {20, 30, 50, 100}; seal a prediction only from that.
- Candidate shape to price in the rerun: the stage-1 optimum with a short stage 2 appended (B2/B1 20-50), 96 bits first; at 72-84 the arithmetic says no.
- Information step answered (Claude Code, from the code): p-1 has no stage 2; its cost model is already written (NOTES, "pm1 stage 2: cost model", Oct 25; MOVES row "pm1 stage 2 (B2 = c x B)"), with predictions pre-registered. ECM has a baby-step giant-step stage 2 (B2 = 50 B1 by default; NOTES, "Stage 2 in the cards today").
- Decision: pending.

### I-017 — 1-2 small ECM curves at 96 bits
- Date: 2026-10-26. Source: Claude chat, from the user's DP. Trigger: ECM at B1 2^8 with stage 2 is chosen at 96 under all three priors (gain 4.75-7.35%). Our ECM already has a BSGS stage 2 (B2 = 50 B1).
- Information step from the code and results: does the current 96-bit card run any ECM, and at what measured cost per curve (stage 1 + stage 2) under ruint pricing? If none, an ECM-at-small-B1 option belongs in the 96-bit re-solve.
- Answered (Claude Code, NOTES "I-017 information step"): Track R's 96-bit pipeline runs no ECM; Track M's runs ~1 curve at the default B1 = 2,059 (59,257 ruint per curve). At b1 = 0.125 (B1 = 257 ~ 2^8, B2 = 12,850) a curve costs 8,187 ruint (~12% of qs at 96), close to the model's ~8,900.
- Decision: pending.

### I-018 — Illuminate the helix, not the number line (two-coordinate light map)
- Date: 2026-10-26. Source: the user's question ("what if we were illuminating the helix instead of the number line?"), developed in Claude chat.
- Idea: each point of the theta tower is a whole semiprime (height log N, radius proportional to 1/2 - theta). A lamp lights the numbers it would crack; "lumens per watt" = population lit per unit cost. This is the quantity the dark-mass DP already computes.
- Second coordinate: angle = smoothness of p-1 (log of the largest prime factor of p-1 / log p). Then:
  - td lights a solid outer skin; rho the same with a soft inner edge;
  - p-1 lights a wedge of angle; stage 2 widens it (p-1 with one large prime <= B2);
  - ECM is a re-rollable speckle (no fixed region);
  - qs floods the whole cross-section.
  The dark mass is a visible region: the spine plus the non-smooth-p-1 wedge at mid theta.
- Use: (a) Phase 3's light spectrum measured as this 2D map with the real lamps (a batch of random semiprimes per band, recording which lamp cracked each); (b) a direct check of the p-1 model: measured p-1 light against the predicted wedge, calibrating the p-1 smoothness constant c (model input 3.4); (c) the visual for I-012 and the film.
- Caveat: both coordinates are computed after factoring; it is a map of where lamps work, never an aiming method (the primehelix separation result).
- Convention: no external standard was found (DeepSeek); the first coordinate follows primehelix's theta plots.
- Update (2026-10-26, the real-prime measurement run): confirmed visually: p-1's light is a wedge (stage 1 inside the B1 ray, stage 2 out to the 100 B1 ray), the rim is lit by td and rho, and the centre is dark under every pipeline. Calibration: p-1's Dickman size divisor fits c = 1.41 (stage 1) / 1.83 (with stage 2), not 3.4; the DP's coverage (c = 1) matches the measured dark fraction within 0.02.
- Cost: small (one measurement pass plus a plot). Timing: with Phase 3, or earlier as the p-1 calibration step for I-016.
- Both views together (user, Oct 26): one number's line, in theta, is one ray of the tower (outer skin to spine at height log N). The number line is the live view of one search (the unlit part of the ray is its dark mass); the tower is the accumulated record of many searches (each find lights its point). Both come from the same per-run log (levels reached, cost at find), aggregated for the tower.
- Explains p-1's look: on a single ray its light is scattered (it keys on p-1 smoothness, the angle coordinate); on the tower it is a wedge. Rho is the reverse: clean along the ray, fuzzy on the tower.
- Film: split screen, one ray lighting up live on the left; its find landing on a filling tower on the right.
- Decision: pending.
