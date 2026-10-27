# Op-class fraction: derivation procedure (DRAFT, a proposal)

**Status: DRAFT. Not adopted.** The user has not chosen option (2) of the open robust-rule decision (NOTES, "Open decision (the user's): the robust rule's veto by official pricing"). This file is step (i) of that option's order:
1. commit the derivation procedure;
2. compute the fraction mechanically and commit it;
3. only then compute and publish the break-even fraction for 2′b and 2′b's ratio.

**Nothing here computes a fraction, a break-even or a priced figure, and nothing may be priced with it until the user adopts the procedure.**

Written by Claude Code, Oct 27 (overnight stage 6), from the reviewer's notes and DeepSeek's and Grok's second views (NOTES).

## 1. What the fraction is for

- **Official prices every counted op at 1.** Option (2) adds a **fourth pricing** ("op-class") that keeps official's hardware-neutral spirit but weights each op class by the number of ISA-level instructions in one fixed compiled sequence that performs it.
- Official itself is unchanged. ruint and Montgomery are unchanged.
- The robust ratio would become the worst of four: a proposal for the rule, decided separately by the user.
- **The weight must come from instruction definitions, never from timing on any machine.** A weight fitted to this laptop's wall-clock would be a second ruint (the reviewer's note) and would remove the hardware-neutral member of the robust track.

## 2. The op classes

Every type in `evolve/optypes.TYPE_ORDER` that the qs card charges gets a weight. Each class is represented by **the card's own code that performs one charged op of that class**, at the commit where the procedure is adopted:

| class | what one charged op is (as charged today) | representative sequence (lampcore) |
|---|---|---|
| sieve_update | one `arr[i] += logp` at a prime stride | the inner `while i0 < width` loop of the base-prime walk (`qs.rs`, sieve) |
| sieve_scan | one cell of the per-polynomial width charge (clear and scan), and one free-2 write | the array clear, the scan's compare, the free-2 store, per cell |
| word | one word-level add, compare or store (start offsets, Gray steps, ka / tm builds, confirm's per-candidate words) | each charged site's statement |
| setup_gray | one root update in the Gray switch | the per-root update loop |
| root_test | one root test of a candidate against a prime | the branch-free test in the root-confirm loop |
| confirm_td | one trial division (i128 v mod p) | the confirm loop body |
| setup_small, fb, mult | one small-modulus reduction (i64 or i128) | the setup and factor-base loops |
| setup_euclid | one Euclid division step | `euclid_inv64`'s loop body |
| la | one 64-bit XOR of the dense elimination | the elimination's row XOR |
| hash | one large-prime table lookup or insert | the HashMap call site in lp_ledger |
| lp_small, lp_full | the ledger's small-modulus and full ops | their sites |
| sort_cmp, f64_log, f64_div | one comparison, one log, one division | their sites |
| sqrt_mul, sqrt_gcd | one full multiply, one gcd step | the square-root stage |

- **Where one charged op covers a variable amount of work** (a Euclid step, an i128 division whose instruction count depends on operand size, a HashMap call): the representative is the steady-state path that the charge describes. Its instruction count is taken as written below, without guessing branches.

## 3. ISA, compiler, settings (fixed)

- **ISA:** x86-64, baseline target (`x86-64`, no `target-cpu=native`, no `-C target-feature`). The baseline target is chosen so the sequences are the same on any x86-64 machine. ARM64 counts may be added later as a second, separate derivation, never mixed.
- **Compiler:** rustc 1.95.0 (59807616e 2026-04-14), cargo 1.95.0, the toolchain pinned in this file. A toolchain change means re-deriving and recommitting the fraction under the same procedure.
- **Settings:** the card's `[profile.release]`: `opt-level = 3`, no LTO, default codegen units. The release binary is built from the adopted commit with no environment flags.
- **The binary's hash** (sha256) is recorded with the counts, so anyone can check that the counted code is the card's.

## 4. How instructions are counted

- **Static count, ISA level, from the fixed binary:** disassemble with `objdump -d --no-show-raw-insn` and identify each class's representative loop or block by its source location (`-l` line info from a build with `debug = 1`, which does not change codegen at opt-level 3; this is checked by comparing the `.text` of both builds).
- **Per op:** the instructions in the steady-state body that perform one charged op, divided by the ops that body performs per iteration (for an unrolled or vectorised loop, the body's instructions ÷ its ops).
- **Counted:** every ISA instruction in that body, including loads, stores, address arithmetic, compares and the loop's own branch. A memory-operand instruction counts as one instruction.
- **Not counted:** instructions outside the body (call setup, loop entry and exit), amortised over many ops.
- **Calls into the standard library** (HashMap, Vec growth, i128 division helpers): counted through the callee's steady-state path in the same binary, by the same rule.
- **Cross-check, still ISA level:** a dynamic instruction count of a single-class microloop with an instruction-counting tool that counts retired ISA instructions deterministically (e.g. valgrind's `--tool=callgrind` Ir counts, or `perf stat -e instructions:u` used only as a count, never as time). If static and dynamic per-op counts differ by more than 10% for a class, the static body choice is reviewed and the reason recorded before any fraction is computed.
- **The fraction for each class** = its instructions per op ÷ the reference class's instructions per op. The reference class is proposed as **root_test** (the op official's veto turned on: sieve update against root test). Equivalently, all weights could be expressed per instruction; the ratios are the same.
- **Mechanical computation:** a committed script reads the disassembly and the committed list of source locations and prints the weights. No hand-edited numbers.

## 5. What is excluded, and why

- **Memory cost** (cache misses, bandwidth, latency) is excluded. Instruction counts are the hardware-neutral quantity; memory behaviour depends on the cache hierarchy, the working-set size and the machine. A sieve update is mostly memory, so this pricing will under-weight it against time on any real machine. **That must be stated beside every op-class figure.** Memory is what energy (RAPL, option 3) or ruint would see.
- **Instruction latency and throughput** (micro-ops, ports, divider latency) are excluded for the same reason. A 64-bit division counts as one instruction here even though it is far slower than an add. The pricing measures how much the code does, not how long it takes.
- **Retired micro-operations** (Grok's suggestion) are excluded: they vary by microarchitecture (the reviewer's note).
- **Wall-clock and any timed data** are excluded from the derivation entirely.

## 6. Safeguards (order and freezing)

1. This procedure is committed, reviewed and adopted by the user **before** any count is taken.
2. The fraction is computed by the committed script from the fixed binary, committed, and **frozen**: the same weights for every cell, every size and every later test, never re-tuned after results.
3. Only after (2): the break-even fraction for 2′b (the weight at which 2′b's op-class ratio against 2′a equals 1) and 2′b's op-class ratio are computed and published, side by side.
4. Any later change (toolchain, ISA, a new op class) re-derives under this same procedure, with a new commit and the old weights kept on record. Earlier figures keep their weights.
5. **Sealed tests do not test a pricing.** Priced outcomes are deterministic from counts already measured, so the safeguard is on the derivation, not on a run (the reviewer's note). The wall-clock of 2′b at 72 and 84 was measured separately (2b-sizes, 5d8e1c9).

## 7. Open points for the user

- **Reference class:** root_test, or per instruction (the same ratios)?
- **Static body selection:** this is where judgement enters, so the list of source locations is part of the procedure's commit.
- **Whether official stays in the robust track beside the op-class pricing** (worst of four), or the op-class pricing replaces official in it: the rule decision itself, not part of this procedure.
