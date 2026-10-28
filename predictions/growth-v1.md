# growth-v1: growth exponents of each lamp alone on balanced semiprimes, 40–96 bits (the growth harness, v1): sealed predictions, filed before any run

**Run** (not yet): the growth harness (NOTES.md, "Growth-exponent harness: cost note and design", 52c03f4, and its correction 38b3828).
- Each lamp alone (td, rho, p−1, ECM, CFRAC, QS) on 48 fresh balanced semiprimes per size at 40, 48, 56, 64, 72, 80, 88 and 96 bits.
- The output: cost per factorisation (op-class v1, ruint, Montgomery, official), local slopes, L[a, c] fits with intervals, and the doubling period in bits.
- Conditions: cap 2,400 MHz, AC. The runner will be committed before the run.

**Definitions** (as the harness defines them):
- **Doubling period** = 1 ÷ (the local slope of log2 cost per factorisation against bits): the number of bits of N over which the cost doubles.
- **"Cross"** = the size at which the two lamps' fitted cost-per-factorisation curves are equal.

## The reviewer's R-29 / R-30 / R-31 (Oct 28; sealed; verbatim)

      R-29 QS doubling period (cost per number, op-class) between 80 and 96 bits: 9 to 14 bits. 70%.
      R-30 Rho on balanced semiprimes: doubling period 3.5 to 5 bits (theory: cost ~ sqrt(p), so it doubles
           every ~4 bits of N). 75%.
      R-31 The rho and QS cost curves cross between 48 and 64 bits on balanced numbers. 65%.

## DeepSeek's

Pending (the user decides whether to relay).

## Grok's

Pending (the user decides whether to relay).

## Scores (recorded after the run; the forecasts above are unchanged)

Sealed counts run 68250b3 (output committed unchanged in 8e45de1); scored in NOTES "Growth harness v1" (e352362).
- **R-29:** hit (QS doubling period 80–96, op-class: 9.29 bits).
- **R-30:** hit (rho doubling period: 4.05 bits).
- **R-31: MISS, scored under op-class** (the user's ruling, Oct 28): QS is cheaper than rho at every size from 40 bits, so the curves do not cross between 48 and 64. Note: no pricing named; scored under op-class, the pricing of R-29 in the same entry and the one D-31/G-24 named; official would hit; not chosen post hoc.
- DeepSeek's D-29 to D-31 and Grok's G-22 to G-24 are filed and scored in `predictions/growth-spectrum-twilight.md` and NOTES.
