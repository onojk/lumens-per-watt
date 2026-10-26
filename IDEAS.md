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
- Decision: pending.
