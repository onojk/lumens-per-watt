# Stage H2 predictions: the re-time after the scan fix (the user's; sealed before the run)

Recorded from the user's message of Oct 27, before any H2 run. 96 bits, all 640 map numbers, against the reference (re-sieve off, pp absent, tc 1.0353), card after the scan fix. Threshold shifts are through tc only (tc = 1.0353 − d / log2 1,752), with L unchanged.

- **H2-1** (iii) pp 10, +5 bits (tc 0.5713): wall-clock −4% to +2% against the reference.
- **H2-2** (iv) pp 3, +3 bits (tc 0.7569): wall-clock −5% to +1%.
- **H2-3** "2 free" (pp 3) at +1 bit (tc 0.9425): polynomials −6% to +4%; wall-clock −6% to +2%.
- **H2-4** "2 free" (pp 3) at +2 bits (tc 0.8497): polynomials −2% to +8%; wall-clock −6% to +2%.

Run: `tools/sealed_run.sh stage-h2 -- bash -c "cd evolve && python3 stageh2.py"`. All four cells plus the reference in one run; two wall-clock replicates; region breakdown; priced (ruint / Montgomery / official); polynomials; candidates; capture on stage B's subset.
