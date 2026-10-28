# Op-class v2 for SIMD: how a vector instruction is weighted (DRAFT)

**Status: DRAFT. Not adopted, and nothing is scored with it.** It was written at the user's request (Oct 27 night; IDEAS I-046) and must exist, and be decided, **before any vectorised code is built** (for example a vectorised root test). op-class v1 (`reviews/opclass_procedure.md`, `opclass/opclass_v1.json`) stays frozen for every decision it made. Any v2 is derived prospectively.

## 1. The problem

v1's weight for an op class is instructions retired (callgrind Ir) per charged op, over a committed input set and a committed line map. A vector instruction counts as **one** instruction, whatever its width. Two consequences:
- **A vectorised loop looks 8–32× cheaper per op** in a re-derivation, though it does the same lane work. For example, YAFU's root test runs 8 primes per SSE4.1 instruction, and its scan compares 32 bytes per AVX2 instruction (Experiment 1).
- **Pricing would reward how the work is written, not the work.** Official pricing is implementation-blind; op-class must not be blind in the opposite direction, rewarding implementation at the expense of the work.

What it does **not** affect today: the card runs no 256-bit instructions in its own code, and its 128-bit packed instructions are 1.8–2.0%, mostly compiler-generated moves (Experiment 1). A v2 derived on today's card should match v1 closely (§5, check 1).

## 2. Options for weighting a vector instruction

| option | weight of one executed instruction | for | against |
|---|---|---|---|
| **(L) lanes** | the number of data lanes it operates on: 128-bit with 16-bit elements = 8, 256-bit with 8-bit elements = 32, a scalar = 1 | prices **work**, not implementation: vectorising a charged loop leaves its weight per op unchanged, so the change becomes counts-identical and is judged on wall-clock like the A-prime fix | lane count is ill-defined for shuffles, permutes, packs and horizontal ops; masked or partial lanes; it needs an element-width rule per mnemonic |
| **(B) bytes touched** | register width ÷ 8 (an 8-byte scalar = 1; xmm = 2; ymm = 4) | simple and mechanical from the operand registers | 8-bit-lane work is under-weighted relative to (L), by 4× for ymm bytes; the weight is arbitrary relative to scalar ops |
| **(T) measured throughput** | the instruction class's reciprocal throughput at the cap, from a calibration microbenchmark, relative to a scalar add (as ruint and Montgomery prices are calibrated) | reflects what the machine actually pays | machine-specific; it needs its own calibration and re-calibration per machine; it mixes cost with work, which is ruint's job, not op-class's |

**Recommendation: (L) lanes,** with fixed fallbacks:
- **Packed arithmetic, compare, logic, min/max, blend:** weight = the number of lanes, from the mnemonic's element suffix and the register width (b = 8 bits, w = 16, d / ps = 32, q / pd = 64).
- **Loads, stores and register moves of vector width:** weight = bytes ÷ 8, rounded up. They move data, so they get no lane credit.
- **Shuffles, permutes, packs, unpacks, broadcasts, extracts, inserts, and movemask:** weight 1. They are overhead, not lane work.
- **Scalar FP in xmm (`*ss`, `*sd`, `cvt*`):** weight 1, as in v1.
- **Mnemonics outside a committed table:** weight 1, and the derivation lists them (a guard, like I-045's unattributed instructions).

Under (L), vectorisation is **neutral** in op-class: it shows up only in wall-clock. That matches the meter's purpose, which is to price the work a card does, and keeps official, ruint, Montgomery and op-class all implementation-blind for vectorisation.

## 3. Derivation (as v1, with one added step)

1. The same committed inputs, line map and rules R1–R6 as v1 (`opclass/README.md`), on the binary under test.
2. callgrind with `--dump-instr=yes`; each executed instruction's Ir is multiplied by its **weight** from §2. The weights come from `objdump -d` mnemonics and operands through a committed mnemonic table (`opclass/v2_simd_weights.tsv`, to be written with the derivation).
3. Weighted Ir per op class ÷ the meter's per-type counts gives the v2 weight.
4. **Two independent derivations** (separate agents, as for v1) agree within 2%, then the result is frozen as v2. It is prospective: v1's decisions stand.

## 4. What v2 changes and what it does not

- **No op count changes.** v2 only re-weights instructions. The meter, the charges, the counts and the official, ruint and Montgomery prices are untouched.
- **Robust rule (b) stays:** the worst of op-class, ruint and Montgomery; official reported, with no veto. v2 would replace v1 in that rule only by the user's decision, for comparisons made after the adoption.
- **The unattributed-instruction guard (I-045)** applies to v2 as to v1.

## 5. Checks before any adoption

1. **On today's card** (no 256-bit code), v2's weights equal v1's within 3% per class. If not, the mnemonic table or the classifier is wrong.
2. **A synthetic test:** a scalar loop and its hand-vectorised twin doing the same lane work (a standalone crate, as `bench/copybench`, not the card) get v2 weights within 5% of each other, while v1 gives the vector twin roughly 1 ÷ lanes.
3. **The table's coverage:** every vector mnemonic executed in the input set is in the table. None falls to the fallback weight unlisted.

## 6. Open points for the user

1. Which option: (L), recommended; (B); or (T).
2. Whether loads and stores get bytes ÷ 8 or 1.
3. Masked or partial lanes (AVX-512, not on this CPU): count the active lanes or the full width.
4. Whether the YAFU comparison (information only) should also be reported under v2 instructions, so the card and YAFU compare in lane work.
5. When to derive it: now, on today's card, as check 1; or only when a vectorised change is proposed.
