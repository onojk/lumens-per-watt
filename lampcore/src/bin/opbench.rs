//! Op-price microbenchmarks (NOTES.md, "Op-price calibration on this laptop"): wall time per
//! primitive, with lampcore's own types, for a calibrated price table reported beside the
//! official op counts. Measurement only; nothing here feeds a score.
//!
//!   opbench [--probe] [--batches K] N60 N84 N100   (odd moduli of about 60, 84 and 100 bits)
//!
//! Prints one JSON object per line, as each primitive finishes: {"name", "ns_median",
//! "ns_min", "ns_q1", "ns_q3", ...}, or {"name", "timeout": true, ...} past the 30 s limit.
//! --probe: only the sizing probes (ns per op, planned batch), to estimate the wall time.

use ruint::aliases::U256;
use std::hint::black_box;
use std::sync::atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering};
use std::sync::Mutex;
use std::time::Instant;

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }
    fn below_u128(&mut self, n: u128) -> u128 {
        (((self.next() as u128) << 64) | self.next() as u128) % n
    }
}

const BATCH_S: f64 = 0.05; // target seconds per timed batch
const LIMIT_S: f64 = 30.0; // per-primitive limit: past it, a timeout record instead of a price

static BATCHES: AtomicUsize = AtomicUsize::new(31);
static PROBE_ONLY: AtomicBool = AtomicBool::new(false);
/// Start of the current primitive in ms since UNIX_EPOCH (0: none running), for the watchdog.
static STARTED_MS: AtomicU64 = AtomicU64::new(0);
static CURRENT: Mutex<String> = Mutex::new(String::new());

fn now_ms() -> u64 {
    std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis() as u64
}

fn timeout_line(name: &str, extra: &str, stage: &str) {
    println!("{{\"name\": \"{name}\", \"timeout\": true, \"limit_s\": {LIMIT_S}, \"stage\": \"{stage}\"{extra}}}");
}

/// Last resort for a single call that never returns: report it and end the run (the lines
/// already printed stay valid). Calls are sized to ~BATCH_S, so this should never fire.
fn watchdog() {
    std::thread::spawn(|| loop {
        std::thread::sleep(std::time::Duration::from_millis(500));
        let s = STARTED_MS.load(Ordering::SeqCst);
        if s != 0 && now_ms().saturating_sub(s) as f64 > 1000.0 * (LIMIT_S + 5.0) {
            let name = CURRENT.lock().unwrap().clone();
            timeout_line(&name, "", "single call");
            std::process::exit(3);
        }
    });
}

/// Times `f(iters)` (which performs at least `iters` operations and returns the count actually
/// done). A probe (doubling from 2^10 until a call takes >= 2 ms) sizes the batch to ~BATCH_S
/// from the measured ns per op, then ~0.1 s of warm-up and BATCHES timed batches; ns-per-op
/// stats. Past LIMIT_S the primitive records a timeout instead. In probe mode, prints the
/// probe's ns per op and the planned batch size only.
fn bench<F: FnMut(u64) -> u64>(name: &str, extra: &str, mut f: F) {
    let t0 = Instant::now();
    *CURRENT.lock().unwrap() = name.to_string();
    STARTED_MS.store(now_ms(), Ordering::SeqCst);
    let over = |t0: &Instant| t0.elapsed().as_secs_f64() > LIMIT_S;
    let mut it = 1u64 << 10;
    let ns_probe = loop {
        let t = Instant::now();
        let ops = f(it);
        let dt = t.elapsed().as_secs_f64();
        assert!(ops >= it, "{name}: did {ops} ops for {it} requested");
        if dt >= 0.002 {
            break dt * 1e9 / ops as f64;
        }
        if over(&t0) || it >= 1u64 << 40 {
            timeout_line(name, extra, "probe");
            STARTED_MS.store(0, Ordering::SeqCst);
            return;
        }
        it *= 2;
    };
    let iters = ((BATCH_S * 1e9 / ns_probe) as u64).max(1);
    let nb = BATCHES.load(Ordering::SeqCst);
    if PROBE_ONLY.load(Ordering::SeqCst) {
        println!("{{\"name\": \"{name}\", \"ns_probe\": {ns_probe:.4}, \"iters\": {iters}, \"batches\": {nb}{extra}}}");
        STARTED_MS.store(0, Ordering::SeqCst);
        return;
    }
    let tw = Instant::now();
    while tw.elapsed().as_secs_f64() < 0.1 {
        f(iters / 2 + 1); // warm-up
    }
    let mut v = Vec::with_capacity(nb);
    for _ in 0..nb {
        if over(&t0) {
            timeout_line(name, extra, "batches");
            STARTED_MS.store(0, Ordering::SeqCst);
            return;
        }
        let t = Instant::now();
        let ops = f(iters);
        v.push(t.elapsed().as_secs_f64() * 1e9 / ops as f64);
    }
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let q = |x: f64| v[((nb - 1) as f64 * x).round() as usize];
    println!(
        "{{\"name\": \"{name}\", \"ns_median\": {:.4}, \"ns_min\": {:.4}, \"ns_q1\": {:.4}, \"ns_q3\": {:.4}, \"iters\": {iters}, \"batches\": {nb}, \"secs\": {:.2}{extra}}}",
        q(0.5), v[0], q(0.25), q(0.75), t0.elapsed().as_secs_f64()
    );
    STARTED_MS.store(0, Ordering::SeqCst);
}

// ---- two-limb Montgomery multiply (N odd, N < 2^100; R = 2^128) ----------------------------

#[derive(Clone, Copy)]
struct Mont {
    n: [u64; 2],
    nn: u128,
    ninv: u64, // -N^-1 mod 2^64
}

impl Mont {
    fn new(n: u128) -> Mont {
        assert!(n & 1 == 1 && n < (1u128 << 100));
        let n0 = n as u64;
        let mut inv = 1u64;
        for _ in 0..6 {
            inv = inv.wrapping_mul(2u64.wrapping_sub(n0.wrapping_mul(inv)));
        }
        Mont { n: [n0, (n >> 64) as u64], nn: n, ninv: inv.wrapping_neg() }
    }

    /// a * b * R^-1 mod N for a, b < N (CIOS, two limbs).
    #[inline(always)]
    fn mul(&self, a: u128, b: u128) -> u128 {
        let a = [a as u64, (a >> 64) as u64];
        let b = [b as u64, (b >> 64) as u64];
        let mut t = [0u64; 4];
        for i in 0..2 {
            let mut c: u128 = 0;
            for j in 0..2 {
                let s = t[j] as u128 + (a[j] as u128) * (b[i] as u128) + c;
                t[j] = s as u64;
                c = s >> 64;
            }
            let s = t[2] as u128 + c;
            t[2] = s as u64;
            t[3] = (s >> 64) as u64;
            let m = t[0].wrapping_mul(self.ninv);
            let s = t[0] as u128 + (m as u128) * (self.n[0] as u128);
            let mut c = s >> 64;
            let s = t[1] as u128 + (m as u128) * (self.n[1] as u128) + c;
            t[0] = s as u64;
            c = s >> 64;
            let s = t[2] as u128 + c;
            t[1] = s as u64;
            t[2] = t[3] + (s >> 64) as u64;
            t[3] = 0;
        }
        let r = (t[0] as u128) | ((t[1] as u128) << 64);
        if t[2] != 0 || r >= self.nn {
            r.wrapping_sub(self.nn)
        } else {
            r
        }
    }

    fn to(&self, a: u128) -> u128 {
        let r: U256 = (U256::from(a) << 128usize) % U256::from(self.nn);
        r.to::<u128>()
    }
    fn from(&self, a: u128) -> u128 {
        self.mul(a, 1)
    }
}

fn primes_upto(n: usize) -> Vec<usize> {
    let mut s = vec![true; n + 1];
    s[0] = false;
    s[1] = false;
    let mut i = 2;
    while i * i <= n {
        if s[i] {
            let mut j = i * i;
            while j <= n {
                s[j] = false;
                j += i;
            }
        }
        i += 1;
    }
    (0..=n).filter(|&i| s[i]).collect()
}

fn main() {
    let mut args: Vec<u128> = Vec::new();
    let mut argv = std::env::args().skip(1);
    while let Some(a) = argv.next() {
        match a.as_str() {
            "--probe" => PROBE_ONLY.store(true, Ordering::SeqCst),
            "--batches" => BATCHES.store(argv.next().unwrap().parse().unwrap(), Ordering::SeqCst),
            _ => args.push(a.parse().unwrap()),
        }
    }
    assert_eq!(args.len(), 3, "usage: opbench [--probe] [--batches K] N60 N84 N100");
    watchdog();
    let mut rng = Rng(0x9e3779b97f4a7c15);
    const K: usize = 1024; // operand pool, L1-resident

    // ---- verify the Montgomery multiply against U256::mul_mod ---------------------------------
    for &n in &args {
        let mo = Mont::new(n);
        let nu = U256::from(n);
        for _ in 0..1_000_000 {
            let (a, b) = (rng.below_u128(n), rng.below_u128(n));
            let got = mo.from(mo.mul(mo.to(a), mo.to(b)));
            let want = U256::from(a).mul_mod(U256::from(b), nu).to::<u128>();
            assert_eq!(got, want, "Montgomery mismatch for N = {n}: a = {a}, b = {b}");
        }
        println!("{{\"name\": \"montgomery verified\", \"bits\": {}, \"inputs\": 1000000}}", 128 - n.leading_zeros());
    }

    // ---- baseline loop overhead -----------------------------------------------------------
    bench("loop overhead", "", |it| {
        let mut x = 0u64;
        for i in 0..it {
            x = black_box(x.wrapping_add(i));
        }
        black_box(x);
        it
    });

    // ---- 1. modular multiply: ruint and Montgomery, chain and throughput -------------------
    for &n in &args {
        let bits = 128 - n.leading_zeros();
        let nu = U256::from(n);
        let ys: Vec<U256> = (0..K).map(|_| U256::from(rng.below_u128(n))).collect();
        let xs: Vec<U256> = (0..K).map(|_| U256::from(rng.below_u128(n))).collect();
        let ex = format!(", \"bits\": {bits}");
        bench("mulmod ruint chain", &ex, |it| {
            let mut x = xs[0];
            for i in 0..it as usize {
                x = x.mul_mod(black_box(ys[i & (K - 1)]), nu);
            }
            black_box(x);
            it
        });
        bench("mulmod ruint throughput", &ex, |it| {
            let mut acc = U256::ZERO;
            for i in 0..it as usize {
                acc ^= xs[i & (K - 1)].mul_mod(ys[(i * 7 + 3) & (K - 1)], nu);
            }
            black_box(acc);
            it
        });
        let mo = Mont::new(n);
        let ym: Vec<u128> = ys.iter().map(|y| mo.to(y.to::<u128>())).collect();
        let xm: Vec<u128> = xs.iter().map(|x| mo.to(x.to::<u128>())).collect();
        bench("mulmod montgomery chain", &ex, |it| {
            let mut x = xm[0];
            for i in 0..it as usize {
                x = mo.mul(x, black_box(ym[i & (K - 1)]));
            }
            black_box(x);
            it
        });
        bench("mulmod montgomery throughput", &ex, |it| {
            let mut acc = 0u128;
            for i in 0..it as usize {
                acc ^= mo.mul(xm[i & (K - 1)], ym[(i * 7 + 3) & (K - 1)]);
            }
            black_box(acc);
            it
        });
        // ---- gcd mod N: U256::gcd (rho, ECM) and the Euclid steps it would take -------------
        let mut steps_total = 0u64;
        for x in &xs {
            let (mut a, mut b) = (*x, nu);
            while b != U256::ZERO {
                let t = a % b;
                a = b;
                b = t;
                steps_total += 1;
            }
        }
        let ex2 = format!(", \"bits\": {bits}, \"euclid_steps_mean\": {:.2}", steps_total as f64 / K as f64);
        bench("gcd U256::gcd per call", &ex2, |it| {
            let mut acc = U256::ZERO;
            for i in 0..it as usize {
                acc ^= black_box(xs[i & (K - 1)]).gcd(nu);
            }
            black_box(acc);
            it
        });
        bench("gcd U256 Euclid per step", &ex2, |it| {
            let mut steps = 0u64;
            let mut i = 0usize;
            while steps < it {
                let (mut a, mut b) = (black_box(xs[i & (K - 1)]), nu);
                while b != U256::ZERO {
                    let t = a % b;
                    a = b;
                    b = t;
                    steps += 1;
                }
                black_box(a);
                i += 1;
            }
            steps
        });
        // ---- 6b. extended Euclid on i128 at this size (ECM's setup inverse) ------------------
        let ni = n as i128;
        bench("ext euclid i128 per step", &ex, |it| {
            let mut steps = 0u64;
            let mut i = 0usize;
            while steps < it {
                let (mut r0, mut r1, mut s0, mut s1) = (ni, black_box(xs[i & (K - 1)].to::<u128>() as i128), 0i128, 1i128);
                while r1 != 0 {
                    let q = r0 / r1;
                    let (nr, ns) = (r0 - q * r1, s0 - q * s1);
                    r0 = r1;
                    r1 = nr;
                    s0 = s1;
                    s1 = ns;
                    steps += 1;
                }
                black_box((r0, s0));
                i += 1;
            }
            steps
        });
    }

    // ---- factor base and sieve geometry of tuned qs at 84 bits ------------------------------
    let n84 = args[1];
    let ln_n = (n84 as f64).ln();
    let bnd = ((1.1 * (0.5 * (ln_n * ln_n.ln()).sqrt()).exp()) as usize).max(30);
    let mm = ((0.25 * bnd as f64) as usize).max(64);
    let width = 2 * mm + 1;
    let base: Vec<usize> = primes_upto(bnd)
        .into_iter()
        .skip(1)
        .filter(|&p| {
            let (mut r, mut b, mut e) = (1u128, n84 % p as u128, (p as u128 - 1) / 2);
            while e > 0 {
                if e & 1 == 1 {
                    r = r * b % p as u128;
                }
                b = b * b % p as u128;
                e >>= 1;
            }
            r == 1
        })
        .collect();
    let logp: Vec<i32> = base.iter().map(|&p| ((p as f64).log2().round() as i32).max(1)).collect();
    // roots: pseudo-random in [0, p), two per prime (start positions are uniform either way)
    let roots: Vec<[usize; 2]> = base.iter().map(|&p| [(rng.next() % p as u64) as usize, (rng.next() % p as u64) as usize]).collect();
    let geo = format!(", \"B\": {bnd}, \"M\": {mm}, \"width\": {width}, \"F\": {}", base.len() + 2);

    // ---- 2. sieve byte-add (lampcore's loop, i32 array, wrapping adds, no zeroing) -----------
    let mut arr = vec![0i32; width];
    bench("sieve update", &geo, |it| {
        let mut upd = 0u64;
        while upd < it {
            for (j, &p) in base.iter().enumerate() {
                for &r in &roots[j] {
                    let start = (r + mm) % p;
                    let mut i0 = start;
                    while i0 < width {
                        arr[i0] = arr[i0].wrapping_add(logp[j]);
                        i0 += p;
                    }
                    if start < width {
                        // primes above the width can miss the interval entirely
                        upd += ((width - 1 - start) / p + 1) as u64;
                    }
                }
            }
            black_box(&arr);
        }
        upd
    });
    for x in arr.iter_mut() {
        *x = (rng.next() % 40) as i32;
    }
    let thr = 30.0f64;

    // ---- 3. cell scan ---------------------------------------------------------------------
    bench("cell scan", &geo, |it| {
        let mut cells = 0u64;
        let mut hits = 0u64;
        while cells < it {
            for i0 in 0..width {
                if (black_box(arr[i0]) as f64) >= thr {
                    hits += 1;
                }
            }
            cells += width as u64;
        }
        black_box(hits);
        cells
    });

    // ---- 4. trial division of a ~50-bit i128 by a small prime --------------------------------
    let vs: Vec<i128> = (0..K).map(|_| (rng.next() >> 14) as i128).collect();
    let ps: Vec<i128> = (0..K).map(|i| base[i % base.len()] as i128).collect();
    bench("trial division i128 ~2^50 by p", &geo, |it| {
        let mut acc = 0i128;
        for i in 0..it as usize {
            acc ^= black_box(vs[i & (K - 1)]) % ps[(i * 13) & (K - 1)];
        }
        black_box(acc);
        it
    });
    // td's step: an 84-bit N mod a small d
    let n84i = n84 as i128;
    bench("N84 mod small d (i128)", &geo, |it| {
        let mut acc = 0i128;
        for i in 0..it as usize {
            acc ^= black_box(n84i) % ps[i & (K - 1)];
        }
        black_box(acc);
        it
    });

    // ---- 5. 64-bit XOR, the GF(2) elimination's row update ----------------------------------
    let fcols = base.len() + 2;
    let rows = fcols + 10;
    let cw = (fcols + 63) / 64;
    let mut mat: Vec<u64> = (0..rows * cw).map(|_| rng.next()).collect();
    let piv: Vec<u64> = (0..cw).map(|_| rng.next()).collect();
    bench("xor word", &geo, |it| {
        let mut words = 0u64;
        while words < it {
            for r in 0..rows {
                for w in 0..cw {
                    mat[r * cw + w] ^= black_box(piv[w]);
                }
            }
            words += (rows * cw) as u64;
        }
        black_box(&mat);
        words
    });

    // ---- 6a. extended Euclid step on small values (setup's inverses mod p) --------------------
    let small: Vec<(i128, i128)> = (0..K).map(|i| {
        let p = base[i % base.len()] as i128;
        (p, 1 + (rng.next() % (p as u64 - 1)) as i128)
    }).collect();
    bench("ext euclid small per step", &geo, |it| {
        let mut steps = 0u64;
        let mut i = 0usize;
        while steps < it {
            let (p, a) = black_box(small[i & (K - 1)]);
            let (mut r0, mut r1, mut s0, mut s1) = (p, a, 0i128, 1i128);
            while r1 != 0 {
                let q = r0.div_euclid(r1);
                let (nr, ns) = (r0 - q * r1, s0 - q * s1);
                r0 = r1;
                r1 = nr;
                s0 = s1;
                s1 = ns;
                steps += 1;
            }
            black_box((r0, s0));
            i += 1;
        }
        steps
    });

    // ---- 7. small modular multiply (u64, mod p <= B), chain ---------------------------------
    bench("small mulmod u64 chain", &geo, |it| {
        let mut x = 3u64;
        for i in 0..it as usize {
            let p = ps[i & (K - 1)] as u64;
            x = (x % p) * black_box(7 + (i as u64 & 63)) % p + 1;
        }
        black_box(x);
        it
    });
}
