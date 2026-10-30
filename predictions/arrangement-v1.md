# arrangement-v1: the arrangement lamp family ("arrangement + detection rule"), predictions

**Status: SEALED. All three forecasters recorded (the reviewer's R-38..R-43, Grok's G-31..G-36, DeepSeek's D-38..D-43), before any build or run.** The design is `docs/planning/arrangement_lamps.md` as of 70d374a: approved in principle by the user (Oct 29), with the reviewer's amendments. The fitness is G_rho (`reviews/growth_fitness_rho.md`, frozen 77ff2ee), with G (`reviews/growth_fitness.md`, frozen c86ef35) beside it.

Novelty Plan: phase 4 (program search, the building-block family). Q1 is phase 4's test drive on a family with a known answer.

## The questions (design §7)

1. **Q1:** Is the best genome rho-shaped? That means the map layout with cycle detection (Floyd or Brent, batched or not), with a log2-steps slope of 0.20–0.30 per bit over 48–80 bits. Yes or no. A yes is reported as "rediscovered known lamp"; it validates the search, meter and guard.
2. **Q2:** The best genome's G_rho (48–80, op-class, plus its worst-of value including the scaled gcd price), or "not defined". Its G (80–96), or "not defined".
3. **Q3:** The best genome ÷ rho alone at 64 and 80 bits, op-class v1, with a range; and the same under the size-scaled gcd price.
4. **Q4:** Does any non-map layout (stride, fold, bins) beat a slope of 0.45 per bit? Yes or no.
5. **Q5:** Does the search select the exponent layout (rediscovered p−1) on θ < 0.3 numbers? It is scored on the θ 0.20–0.30 sub-map only (design §8).
6. **Q6:** The best genome's map degree d: d = 2, or higher?

**Number distributions** (design §8):
- **Balanced main map:**
  - training: 48 per size at 48–80 bits, seeds 9920000 + bits;
  - validation: 48 per size at 48, 64, 80 and 96 bits, seeds 9930000 + bits, with rho alone on the same numbers.
- **θ sub-map:** θ uniform 0.20–0.30; training 48 per size at 64 and 80 bits (seeds 9925000 + bits); validation 96 per size (seeds 9935000 + bits).

## The reviewer's R-38 to R-43 (Oct 29; sealed; verbatim; filed before any run)

<!-- verbatim begin -->
  R-38 (Q1) Best genome rho-shaped (map + cycle detection, slope 0.20-0.30 per
       bit, 48-80): yes, 80%.
  R-39 (Q2) Best genome G_rho (48-80, op-class): 1.00, range 0.88-1.12, 65%;
       holds under the worst-of set incl. scaled gcd price. G (80-96) defined:
       0.43, range 0.36-0.52, 60%.
  R-40 (Q3) Best genome / rho alone at 64 and 80 bits, op-class: 0.95, range
       0.82-1.08, 60%; under the scaled gcd price within +/-0.03 of op-class.
  R-41 (Q4) A non-map layout beats 0.45 per bit: no, 85%.
  R-42 (Q5, if kept) Search selects the exponent layout on theta < 0.3: no, 60%.
  R-43 (Q6) Best map degree d = 2: yes, 70%.
  Calibration note: ranges widened and confidences lowered from R-38 on, per the
  scorecard (stated 61-65%, hit 47-50%).
<!-- verbatim end -->

**Scope note** (the prediction is unchanged): Q5 is kept, with its own sub-map (design §8), so R-42 is scored.

## DeepSeek's D-38 to D-43 (Oct 29; sealed; verbatim, as relayed by the user; filed before any build or run)

<!-- verbatim begin -->
Sealed predictions for the arrangement-v1 round. Facts below are predictions,
not measurements; I will not revise them after scoring.

D-38 | Yes. Best genome is rho-shaped: map layout + Floyd or Brent cycle
detection, batched or not, slope 0.20–0.30 per bit over 48–80. | 0.85 | Best
genome is not map+cycle detection, or its measured slope falls outside 0.20–0.30.

D-39 | G_rho ≈ 1.00, range [0.97, 1.04] op-class over 48–80. Under worst-of incl.
scaled gcd: ≈0.99 [0.96, 1.03], so I predict no strict win under worst-of (near
parity). G(80–96): ≈1.00, or effectively "not defined" if the genome is rho
rediscovered. | 0.65 | G_rho outside [0.97,1.04] op-class, or a strict G_rho > 1
win holds under worst-of.

D-40 | Best genome / rho alone, op-class: 64 bits ≈ 0.99 [0.95, 1.04]; 80 bits ≈
1.00 [0.96, 1.05]. Under scaled gcd: 64 ≈ 1.00 [0.96, 1.05]; 80 ≈ 1.01 [0.97,
1.06]. | 0.60 | Any ratio outside those ranges, or scaled-gcd shifts the ratio by
more than about 5%.

D-41 | No. No non-map layout — stride, fold, or bins — beats 0.45 per bit. Best
non-map likely sits near 0.50. | 0.85 | Any stride/fold/bins layout measures a
slope below 0.45 per bit.

D-42 | No. On the theta 0.20–0.30 sub-map, the search does not select the
exponent layout; it selects a map/rho-shaped genome. | 0.60 | The exponent layout
is selected on the theta 0.20–0.30 sub-map.

D-43 | d = 2. Best genome's map degree is 2, not higher. | 0.75 | Best genome
selects degree d > 2.

Short rationale: the measured shapes put rho and p-1 near slope 0.25, while
walk/value-line sit near 0.50; non-map layouts in this family are unlikely to
cross 0.45. Since rho is the frozen baseline for G_rho, a rediscovered
rho-shaped best genome should sit near parity rather than a large win,
especially once scaled gcd is in the worst-of set.
<!-- verbatim end -->

**The reviewer's notes on D-38..D-43** (Oct 29; annotations only; no prediction changes):

<!-- verbatim begin -->
- D-39's G (80-96) "~1.00, or effectively not defined if the genome is rho
  rediscovered" appears to treat G as G_rho. G compares against QS's 9.29-bit
  doubling period; a rho-shaped genome (~4-bit doubling) has G ~ 4/9.29 ~ 0.43
  (the relay's design states rho's G is about 0.44). The "rediscovered known
  lamp" label does not make G undefined. Recorded and scored as written.
- D-39 / D-40 ranges are narrow (about +/-3-5%) with confidence 0.60-0.65;
  G_rho's own resolution note says 0.96-1.04 is not separable from 1 at 48 per
  size. Interval score as usual.
- D-40's falsifier has two conditions (range; scaled-gcd shift > 5%); recorded
  as written.
<!-- verbatim end -->

**Recording note:** the relay text printed for the forecasters did not contain the figure "rho's G is about 0.44" that the first note cites (flagged to the user earlier). The note is recorded as given.

## Grok's G-31 to G-36 (Oct 29; sealed; verbatim, as relayed by the user; filed before any build or run)

<!-- verbatim begin -->
G-31 (best genome is rho-shaped: map + Floyd/Brent, slope 0.20–0.30 / bit over
48–80). Prediction: yes. Range: categorical {yes, no}. Arithmetic: measured
unmetered slopes (20–40 bits) are 0.254 for rho (x²+1, Floyd) and 0.253 for p-1
versus 0.503 for walk/value-line; map + cycle detection is explicitly in the gene
pool while non-map layouts are linear (stride/fold/bins). Base: best genome under
G_rho fitness on the main balanced map (training 48 per size at 48/56/64/72/80).
"Rho-shaped" defined exactly as map layout + Floyd or Brent detection (batched or
not) with fitted slope in [0.20, 0.30]. Confidence: 70%. Falsifier (single
condition): the selected genome uses a non-map layout or a fitted slope outside
[0.20, 0.30].

G-32 (best genome's G_rho 48–80 op-class; holds under worst-of incl. scaled gcd?;
its G 80–96). Prediction: G_rho = 1.05; holds under worst-of; G = not defined.
Range: G_rho 0.70–1.40 (±33% around 1.05). Arithmetic: rho alone measured at
3.936 bits [3.790, 4.098]; a rediscovered or mildly tuned map+cycle genome is
expected near 1.0 relative to that baseline, centre lifted to 1.05 for possible
Brent/batched or degree effects, then widened for search variance and the
1.1–1.3% gcd share. Scaled-gcd price changes gcd by a size-dependent factor but
gcd is only ~1% of cost, so worst-of is not expected to reverse a near-1 result.
G (vs QS 9.29 bits) is undefined if the genome is rho-shaped (cannot run the
80–96 QS comparison on a pure rho). Base: op-class v1, G_rho = (candidate
doubling period) / 3.936 over 48–80, worst-of = {op-class v1, ruint, Montgomery,
scaled gcd}. Confidence: 50%. Falsifier (single condition): measured G_rho
(op-class) ≥ 1.50 or the genome is reported as non-rho-shaped.

G-33 (best genome / rho alone at 64 and 80 bits, op-class; same under scaled
gcd). Prediction: 0.95 at both sizes (op-class and scaled-gcd). Range: 0.65–1.25
at each size (±32%). Arithmetic: if the genome is a close rho variant, cost ratio
near 1; centre 0.95 allows a small implementation edge (batched detection or
degree), width covers the possibility of a modestly worse constant or of a
non-rho genome that is still competitive at these sizes. Scaled-gcd adjustment is
small (gcd 1.1–1.3% of rho cost) so the two pricings stay close. Base: mean cost
per factorisation, op-class v1 and size-scaled gcd price, versus rho alone on the
same 48 held-out numbers per size. Confidence: 55%. Falsifier (single condition):
measured op-class ratio at 80 bits ≥ 1.40.

G-34 (any non-map layout beats 0.45 per bit). Prediction: no. Range: categorical
{yes, no}. Arithmetic: measured walk/value-line slopes are 0.503; non-map layouts
(stride, fold, bins) are linear arrangements whose collision time is expected to
track that slope; "beat 0.45" would require a sub-linear improvement not observed
in the unmetered shapes. Base: fitted slope of log2(median steps) per bit, 48–80,
any stride/fold/squares-bins genome. Confidence: 65%. Falsifier (single
condition): a non-map genome is selected with fitted slope ≤ 0.45.

G-35 (search selects exponent layout on the θ 0.20–0.30 sub-map). Prediction:
yes. Range: categorical {yes, no}. Arithmetic: exponent layout is exactly p-1's
arrangement; on the low-θ band (smaller factors) the earlier twilight results
showed p-1 delivering useful successes at low op-class cost, and the gene pool
includes it. Base: selected genome on the θ-uniform 0.20–0.30 sub-map (training
48 at 64 and 80). Confidence: 55%. Falsifier (single condition): the selected
genome on that sub-map is not the exponent layout.

G-36 (best genome's map degree: d = 2 or higher). Prediction: d = 2. Range:
categorical {d=2, d>2}. Arithmetic: measured rho baseline uses x²+1; higher even
d (4,6,8) costs (log2 d + popcount(d) − 1) muls per step (charge 554.9 each)
while the Brent/Pollard (1981) cycle-shortening benefit is conditional on
p ≡ 1 mod 2k and is not guaranteed to offset the extra multiplies under the
frozen op-class weights. Base: map-layout degree of the best G_rho genome on the
main balanced map. Confidence: 60%. Falsifier (single condition): the selected
genome has map degree d ≥ 4.
<!-- verbatim end -->

**The reviewer's notes on G-31..G-36** (Oct 29; annotations only; no prediction changes):

<!-- verbatim begin -->
- G-32's "G undefined for a pure rho (cannot run the 80-96 QS comparison)" shares
  D-39's reading: G compares the candidate's own 80-96 doubling period with QS's
  9.29 bits; the design states a p^(1/2) arrangement is feasible at 80-96 and
  validation includes 96, so G should be defined (~0.43) unless the stage budget
  censors rho at 96. If the budget censors it, state so in the results.
- G-32's falsifier has two conditions (the second duplicates G-31); recorded as
  written.
- G-35's support cites twilight evidence where p-1 was compared with QS at 96
  bits; on the 0.20-0.30 sub-map at 64/80 bits p-1 competes with rho at
  p ~ 2^13-2^24. Recorded as given.
<!-- verbatim end -->

## Grok's G-37 (sealed Oct 30, after judge pin 3 and before any validation run; verbatim, as clarified by Grok and pasted by the user)

<!-- verbatim begin -->
G-37 (fraction of top genomes whose 48-bit advantage is concentrated on the Fermat-easy subset)
Prediction: 0.02.
Range: 0.00-0.08.
Exact comparison: among the top 10 genomes ranked by training G_rho (op-class v1) on the balanced map, the fraction for which (48-bit cost vs rho on the Fermat-easy subset) <= 0.5 x (48-bit cost vs rho on the complementary subset), where the Fermat-easy subset is defined as Fermat steps <= sqrt(p) and is taken from the held-out 48-bit validation numbers.
Confidence: 60%.
Falsifier (single condition): the measured fraction exceeds 0.08.
<!-- verbatim end -->

**Pre-run notes (the user's, marked as such; verbatim):**

<!-- verbatim begin -->
- With a denominator of 10, only 0/10 is within range; 1/10 = 0.10 falsifies.
- "Cost vs rho" on a subset = the genome's aggregate op-class v1 cost on that subset / rho's aggregate on the same numbers, using the split report's aggregate (state which: median or mean) and nothing else.
- Top 10 = the 10 highest training G_rho among valid genomes; genomes invalidated by the early-exit audit are excluded before ranking.
- The report prints the Fermat-easy subset size at 48 bits (validation) beside the result.
- The search never sees validation numbers; G-37 is computed after the search, by the report script.
<!-- verbatim end -->

**The recorder's notes (Claude's; not part of the forecast):**
- The aggregate is the **mean** op-class v1 cost per number on the subset (total spent, censored runs included, divided by the subset's numbers), against rho's mean on the same numbers (`evolve/arr_report.py` g37, 39375a9).
- "Valid genomes" with a training G_rho are the search record's evaluated genomes whose training G_rho (op-class v1) is defined. A genome the search dropped (by the cost guard or for too few successes) has none and is not ranked.
- Disclosure: before this seal, a code check of g37 ran once on the held-out 48-bit numbers with the 20–32-bit selftest genomes (rho-like). It showed a Fermat-easy subset of 6 of 48, and 0 / 5 for those genomes. Grok did not see it. NOTES, "Incident: held-out 48-bit numbers seen before G-37 was sealed"; the user decides whether this stands.


## Judge pins, pin 1

Appended after sealing; no prediction changed (design §6). The judge's sha256s at 3d3f42d (the arr lamp, parity clean, c94e986; the guard, 743fde7 and 3d3f42d). `@predictions` is the sealed text above this heading. The scoring harness `evolve/arr_validate.py` is not written yet: it stays `pending`, so tools/sealed_run.sh refuses every scored run until a later pin (appended, in its own commit) names its hash. Check: `python3 tools/judge.py check arrangement-v1`.

<!-- judge-pins begin -->
db88aaec5e9ee750e6f62724f626b4abbc02a0595ba1c1367f9d4a07a1d9d373  lampcore/target/release/lampcore
2f606e441a8bb4f84281d0b279570b4ea4d12db0e27af0ad4f2b97465caf5bfd  lampcore/Cargo.toml
3fe5a57d381e98ac6cd19fb5857f9e327d3327818ccb8c7609513b3d267da596  lampcore/Cargo.lock
43b0e4beb9d153a63e7f204e90c2163beb413bd805d4346f66a2636ed23c2ae3  lampcore/src/arr.rs
1c65c2ae2932f4a66e5171c911d847cf230a2c6fd1153167a18434df7ddec7d6  lampcore/src/cfrac.rs
f97cdd67b7b139b917566c0b793e16d4fc24b1cea7ca4e36f7cbd426f2ec95d5  lampcore/src/ecm.rs
dd6e1fdd513995bbf31b8f21ac9fb78b780eb755ca35f580c672a3c90e113c17  lampcore/src/main.rs
1b5790834fc1d7decf19f4ec775f4c003477466f58616dabf3e04e7f37af819e  lampcore/src/qs.rs
c574752b6d5669c1d2f187c09266e583529288d4ec5f03b3addef35f4bb7db46  lampcore/src/race.rs
60725704a573d1eadbf0904a2729501568c69044b682fab5da670b2340f5ba05  evolve/lamps.py
cf926d3383660d474585200206ab623003db97464ee12e681433adac0a19e88b  evolve/arr.py
33bc565f4e60e3cef1ba3b91202b2434de85b43247810a2c623a3fb772a2b971  evolve/fastlamps.py
a03d5a259ac45e24404988b60b535570b025cb5b751cef0f682fda54f47b9b48  evolve/optypes.py
32c4102a0cf7a5dd2124cbcd706c5ad5560b614ff99dc79e602c39be5266a4fe  evolve/qs.py
d84a2559a4e43256a57186b02a351a2e8ea6f914f069dfc1108c0c8fa2a00e9b  evolve/cfrac.py
32c36aa229413299f88120570e82ed1b6f4302670159528529aa31bca7d8dc61  evolve/ecm.py
57569989f14bb4e341837dfe787d3aa34f2664b886b4b1a3c6ccceab8aa442d6  evolve/race.py
8f7027c29a4c6a1eb901955dbe7f74c40d7694bcd5e8f4eb8cd08da5354a8729  evolve/ledger.py
8301947ba7d51e6222b4e3d19f8a9ad2504b37e14a26014480a78d77834e47f6  evolve/blockflash.py
449b87a000739d360490d87472f671e7eab2dfd727a136450ce5853c73816982  evolve/calibrate.json
60e5333bfe2a9288163dd5631e4b67a787e135b3ccaee48a333eb056ce197746  opclass/opclass_v1.json
23907d75ab800182d18280abeeb3890349c7f245c28736c5827b5dd4223a2463  reviews/growth_fitness_rho.md
7a168f8c2bbc446405b86c024dfe667094796b174712a971b7517f8820ff962f  reviews/growth_fitness.md
3ddb6ded114c00d8f5d8c58e2eab8d400468ac483e4627e0a64c4dafaf41d2af  tools/sealed_run.sh
9527edab23dfb931fccc2d0665a7ebfee83d01bac586ed5d0ac0ae82d89b156b  tools/judge.py
5eff0bfa34b38423808e78f3096ff48f95f9cb2ed42003bda5246bf0740e4318  tools/search_sandbox.sh
pending                                                           evolve/arr_validate.py
d57e3189d78ca5210c90d61a62cf2bf9cc116afe45e5bc83fb89dc175090fb73  @predictions
<!-- judge-pins end -->

## Judge pins, pin 2

Appended in its own commit; no prediction changed. Supersedes pin 1. The judge at 7299376: the scoring harness `evolve/arr_validate.py` (pending in pin 1) and everything it loads (12 more modules and 4 data files, found with an audit hook on a short run of each code path), the binary rebuilt for gcd_small < 2^32 (G_rho v2, 6a20d42), and `reviews/growth_fitness_rho.md` with its v2 addendum. Nothing is pending.

<!-- judge-pins begin -->
96a5c218872f13e3fb377a8ed12b5ae002c8c32106d7218fb957dfcda91651a4  lampcore/target/release/lampcore
2f606e441a8bb4f84281d0b279570b4ea4d12db0e27af0ad4f2b97465caf5bfd  lampcore/Cargo.toml
3fe5a57d381e98ac6cd19fb5857f9e327d3327818ccb8c7609513b3d267da596  lampcore/Cargo.lock
16e8bfcf50c383c0b6bb289916e43905879108e25c880a8505bb39a0c007a1a6  lampcore/src/arr.rs
1c65c2ae2932f4a66e5171c911d847cf230a2c6fd1153167a18434df7ddec7d6  lampcore/src/cfrac.rs
f97cdd67b7b139b917566c0b793e16d4fc24b1cea7ca4e36f7cbd426f2ec95d5  lampcore/src/ecm.rs
6053ccd04f2e61f6808a0b1233a5f3da5c4e23069b650953cbad89a0c05362d0  lampcore/src/main.rs
1b5790834fc1d7decf19f4ec775f4c003477466f58616dabf3e04e7f37af819e  lampcore/src/qs.rs
c574752b6d5669c1d2f187c09266e583529288d4ec5f03b3addef35f4bb7db46  lampcore/src/race.rs
82407c607dc7c73e4b6b57384b43f836bb9d8558a863d4141057a3190c571bda  evolve/lamps.py
05cb35eea66751d021e471344e2efbb58d72b650de6f498d63c385f487fe6bba  evolve/arr.py
33bc565f4e60e3cef1ba3b91202b2434de85b43247810a2c623a3fb772a2b971  evolve/fastlamps.py
a03d5a259ac45e24404988b60b535570b025cb5b751cef0f682fda54f47b9b48  evolve/optypes.py
32c4102a0cf7a5dd2124cbcd706c5ad5560b614ff99dc79e602c39be5266a4fe  evolve/qs.py
d84a2559a4e43256a57186b02a351a2e8ea6f914f069dfc1108c0c8fa2a00e9b  evolve/cfrac.py
32c36aa229413299f88120570e82ed1b6f4302670159528529aa31bca7d8dc61  evolve/ecm.py
57569989f14bb4e341837dfe787d3aa34f2664b886b4b1a3c6ccceab8aa442d6  evolve/race.py
8f7027c29a4c6a1eb901955dbe7f74c40d7694bcd5e8f4eb8cd08da5354a8729  evolve/ledger.py
8301947ba7d51e6222b4e3d19f8a9ad2504b37e14a26014480a78d77834e47f6  evolve/blockflash.py
449b87a000739d360490d87472f671e7eab2dfd727a136450ce5853c73816982  evolve/calibrate.json
60e5333bfe2a9288163dd5631e4b67a787e135b3ccaee48a333eb056ce197746  opclass/opclass_v1.json
2ea182efdcd2ab0c346ec48a22067fd80a55e05bca2f56e1b7ec1672874198a3  reviews/growth_fitness_rho.md
7a168f8c2bbc446405b86c024dfe667094796b174712a971b7517f8820ff962f  reviews/growth_fitness.md
3ddb6ded114c00d8f5d8c58e2eab8d400468ac483e4627e0a64c4dafaf41d2af  tools/sealed_run.sh
959e2e2837e083af52719fa5bee8dc114e259d3ebb64ddf9029478bf63f11268  tools/judge.py
5eff0bfa34b38423808e78f3096ff48f95f9cb2ed42003bda5246bf0740e4318  tools/search_sandbox.sh
ea603abd21497801331c91a09d8926e7514e550224e93d2de7e5dea75ac92690  evolve/arr_validate.py
4a84655cfb61bede2e2964600cbc11a121679dbc4b143928cc622a29b7b8f69d  evolve/baseline_msieve.py
94da3a7026941497bd0d675863de505535a7da380371a9527c80ef322aafd727  evolve/gcdscale.py
4f4998ab3cc59a56d550ea5e317c3e921a7260987eef67b6ee329932a0357a84  evolve/growth_harness.py
04235deb9d4fa0dcaf54bac00fb5e3f2a529e081c434f5786fe663e313b03fcb  evolve/lctest.py
dd93e08e105099a369f86e58e267d960da3f8e10f046c9314f61aa97c4b03f6c  evolve/oracle.py
13a436bad141f020e006b58653357791271f67cd98978b491feaba5cc16796e7  evolve/partition.py
2afe02b29592aaaf868129742baa59aa2a821067295a3773998e2608c78d7cf0  evolve/run8_space.py
f90951cc8a828163bd13b74bcf06e7e3475c888928e69ca175714f489d8e165f  evolve/size_budgets.py
8128465f668b955650c90cf910d30cd31b5439724b0c361a51a8ae0624cc0b39  evolve/sizescale.py
168c62ad4954d979be2ca924548d8ecc1a85a2319761dbae14fd6ed72f7296b2  evolve/sizescale2.py
b0d3b87be175a9ca63e882cc2b4b26c97ca69a0c6a23259b59fee46b29be6de2  evolve/stopping.py
d738dc9b2a339d56938b98616bdad983a589a004f8e51682b307a0a079b0b0bb  evolve/timing.py
73abc2f9a7a62edf2c09a0d893fb57e926cddfbf5cbfd3187e92080b5e72621e  bench/gcdbench/gcd_ir.json
52a7277a535826a03aeacae6668223cde60d749d3a9eeb011241840e44d94351  evolve/run6/accept.json
3e115287ce39db2f95a0acad4fe9fad6422295cde7995b491e3d917dc4acfceb  evolve/size_curve.json
0527f7f5dfbbb45f1852f6277009ee60792d042f1aa5b83b1621bc7f6f6dd57a  evolve/sizescale_k_sealed.json
d57e3189d78ca5210c90d61a62cf2bf9cc116afe45e5bc83fb89dc175090fb73  @predictions
<!-- judge-pins end -->

## Judge pins, pin 3

Appended in its own commit; no prediction changed. Supersedes pin 2. The judge at 39375a9, after the guard hardening (DeepSeek items 2, b1–b3; Grok b1–b2; 4e86af5, 3356dc3): the seed-free pricing module `evolve/arr_price.py`, the harness with its total reader, search_out allow-list and early-exit audit, `tools/score_sandbox.sh` (new), the training-only `tools/search_sandbox.sh`, and `tools/sealed_run.sh` (pinned experiments run only through the two sandboxes). Selftests re-run: the harness selftest passes inside the scoring sandbox. Nothing is pending.

<!-- judge-pins begin -->
96a5c218872f13e3fb377a8ed12b5ae002c8c32106d7218fb957dfcda91651a4  lampcore/target/release/lampcore
2f606e441a8bb4f84281d0b279570b4ea4d12db0e27af0ad4f2b97465caf5bfd  lampcore/Cargo.toml
3fe5a57d381e98ac6cd19fb5857f9e327d3327818ccb8c7609513b3d267da596  lampcore/Cargo.lock
16e8bfcf50c383c0b6bb289916e43905879108e25c880a8505bb39a0c007a1a6  lampcore/src/arr.rs
1c65c2ae2932f4a66e5171c911d847cf230a2c6fd1153167a18434df7ddec7d6  lampcore/src/cfrac.rs
f97cdd67b7b139b917566c0b793e16d4fc24b1cea7ca4e36f7cbd426f2ec95d5  lampcore/src/ecm.rs
6053ccd04f2e61f6808a0b1233a5f3da5c4e23069b650953cbad89a0c05362d0  lampcore/src/main.rs
1b5790834fc1d7decf19f4ec775f4c003477466f58616dabf3e04e7f37af819e  lampcore/src/qs.rs
c574752b6d5669c1d2f187c09266e583529288d4ec5f03b3addef35f4bb7db46  lampcore/src/race.rs
82407c607dc7c73e4b6b57384b43f836bb9d8558a863d4141057a3190c571bda  evolve/lamps.py
05cb35eea66751d021e471344e2efbb58d72b650de6f498d63c385f487fe6bba  evolve/arr.py
33bc565f4e60e3cef1ba3b91202b2434de85b43247810a2c623a3fb772a2b971  evolve/fastlamps.py
a03d5a259ac45e24404988b60b535570b025cb5b751cef0f682fda54f47b9b48  evolve/optypes.py
32c4102a0cf7a5dd2124cbcd706c5ad5560b614ff99dc79e602c39be5266a4fe  evolve/qs.py
d84a2559a4e43256a57186b02a351a2e8ea6f914f069dfc1108c0c8fa2a00e9b  evolve/cfrac.py
32c36aa229413299f88120570e82ed1b6f4302670159528529aa31bca7d8dc61  evolve/ecm.py
57569989f14bb4e341837dfe787d3aa34f2664b886b4b1a3c6ccceab8aa442d6  evolve/race.py
8f7027c29a4c6a1eb901955dbe7f74c40d7694bcd5e8f4eb8cd08da5354a8729  evolve/ledger.py
8301947ba7d51e6222b4e3d19f8a9ad2504b37e14a26014480a78d77834e47f6  evolve/blockflash.py
449b87a000739d360490d87472f671e7eab2dfd727a136450ce5853c73816982  evolve/calibrate.json
60e5333bfe2a9288163dd5631e4b67a787e135b3ccaee48a333eb056ce197746  opclass/opclass_v1.json
2ea182efdcd2ab0c346ec48a22067fd80a55e05bca2f56e1b7ec1672874198a3  reviews/growth_fitness_rho.md
7a168f8c2bbc446405b86c024dfe667094796b174712a971b7517f8820ff962f  reviews/growth_fitness.md
3c9bcfd55b6d6a3a5429c828010af1b563e2745272e3f06d111109ad7ecd42cb  tools/sealed_run.sh
74a20fe2e99c155eda3ef5aaab2c8ef39db984989a38aa730c2df36f324b29ce  tools/judge.py
f2eaddbb9cb40ac384f6bb6ba175154aa3f08dae0eaa98d7b671e03bd278ad3a  tools/search_sandbox.sh
a782f5c8ef19984be07aacd895ba516d8a0b5ed9c530f38af8fe4db00d4ce94e  tools/score_sandbox.sh
a16b491732676a8b2895bbd126435f56ac696301a5af07a1ae21c2fd99642ab5  evolve/arr_validate.py
e5ccd4ac8ab29d0659bba487b111865657e2ed8023a29aeaee03482140044dac  evolve/arr_price.py
4a84655cfb61bede2e2964600cbc11a121679dbc4b143928cc622a29b7b8f69d  evolve/baseline_msieve.py
94da3a7026941497bd0d675863de505535a7da380371a9527c80ef322aafd727  evolve/gcdscale.py
4f4998ab3cc59a56d550ea5e317c3e921a7260987eef67b6ee329932a0357a84  evolve/growth_harness.py
04235deb9d4fa0dcaf54bac00fb5e3f2a529e081c434f5786fe663e313b03fcb  evolve/lctest.py
dd93e08e105099a369f86e58e267d960da3f8e10f046c9314f61aa97c4b03f6c  evolve/oracle.py
13a436bad141f020e006b58653357791271f67cd98978b491feaba5cc16796e7  evolve/partition.py
2afe02b29592aaaf868129742baa59aa2a821067295a3773998e2608c78d7cf0  evolve/run8_space.py
f90951cc8a828163bd13b74bcf06e7e3475c888928e69ca175714f489d8e165f  evolve/size_budgets.py
8128465f668b955650c90cf910d30cd31b5439724b0c361a51a8ae0624cc0b39  evolve/sizescale.py
168c62ad4954d979be2ca924548d8ecc1a85a2319761dbae14fd6ed72f7296b2  evolve/sizescale2.py
b0d3b87be175a9ca63e882cc2b4b26c97ca69a0c6a23259b59fee46b29be6de2  evolve/stopping.py
d738dc9b2a339d56938b98616bdad983a589a004f8e51682b307a0a079b0b0bb  evolve/timing.py
73abc2f9a7a62edf2c09a0d893fb57e926cddfbf5cbfd3187e92080b5e72621e  bench/gcdbench/gcd_ir.json
52a7277a535826a03aeacae6668223cde60d749d3a9eeb011241840e44d94351  evolve/run6/accept.json
3e115287ce39db2f95a0acad4fe9fad6422295cde7995b491e3d917dc4acfceb  evolve/size_curve.json
0527f7f5dfbbb45f1852f6277009ee60792d042f1aa5b83b1621bc7f6f6dd57a  evolve/sizescale_k_sealed.json
d57e3189d78ca5210c90d61a62cf2bf9cc116afe45e5bc83fb89dc175090fb73  @predictions
<!-- judge-pins end -->
