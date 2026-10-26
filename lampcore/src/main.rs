//! lampcore: the lumens-per-watt lamps in Rust, with operation counting identical to
//! evolve/lamps.py, so the same experiments can run on much bigger numbers.
//!
//! Protocol (stdin -> stdout):
//!   line 1: genome as JSON (the same list of stages lamps.py uses)
//!   line 2: op cap (a run that would exceed it is a miss)
//!   then one line per number: "N p q" in decimal (p, q = its prime factors)
//! For each number one line comes back:
//!   "<ops> <factor> <tests> <hits> <stage> <k>"   or   "miss <tests> <hits>"
//! If the genome has a quadratic-sieve, continued-fraction or elliptic-curve stage, both lines
//! end with fifteen per-phase op counts (mult fb setup sieve confirm la sqrt lp check cf_step
//! cf_td ecm_setup ecm_s1 ecm_s2 ecm_gcd), for the parity check.
//! If the genome has a race stage (Stage 9, race.rs), the line then ends with
//! " R <side A ops> <side B ops> <switches>" for the last race that ran (and the phase columns
//! are printed when either side is a qs, cfrac or ecm stage).
//! With --types, each line then ends with " T" and the run's per-type op counts, in
//! TYPE_NAMES order (the types evolve/optypes.py splits; read-only instrumentation).
//! stage is the winning stage's index; k is the multiplier a square-search win came from,
//! "-" for any other lamp (read-only instrumentation: it never changes the op count).
//!
//! p and q are used only by the block-flash replay (see lamp_ps). Every other lamp
//! computes on N alone.

use ruint::aliases::U256;
use serde_json::Value;
use std::io::{self, BufRead, BufWriter, Write};

mod cfrac;
mod ecm;
mod qs;
mod race;

struct Budget;

/// Per-type op counts (NOTES.md, "lampcore per-type op counters"): the types optypes.py
/// splits, in its TYPE_ORDER.
pub const TYPE_NAMES: [&str; 29] = [
    "mult", "fb", "setup_full", "setup_euclid", "setup_small", "sieve_update", "sieve_scan",
    "confirm_full", "confirm_td", "la", "sqrt_mul", "sqrt_gcd", "lp_full", "lp_small", "check",
    "setup_mul", "setup_euclid_N", "mul", "gcd", "td_mod", "sq_ops", "ps_ops", "cfrac_ops", "word", "setup_gray",
    "hash", "sort_cmp", "f64_log", "f64_div",
];
/// The word-level phase (NOTES.md, "ECM modular additions"): one machine-word op, priced like sieve_update.
pub const PH_WORD: usize = 15;
/// The Gray-code root-update phase (NOTES.md, "Gray-code root update re-typed"): word-level, its own type for both-way pricing.
pub const PH_GRAY: usize = 16;
/// The audit re-typing's own types (NOTES.md, "Audit re-typing, items 0-8"): one hash-set probe-and-insert,
/// one comparison inside a sort, one floating log of a ratio, one floating divide.
pub const PH_HASH: usize = 17;
pub const PH_SORT: usize = 18;
pub const PH_FLOG: usize = 19;
pub const PH_FDIV: usize = 20;
/// Event counters for the full-price parts, at the program points of Python's trace updates.
pub const EV_SETUP_FULL: usize = 0;
pub const EV_SETUP_EUCLID: usize = 1;
pub const EV_SIEVE_SCAN: usize = 2;
pub const EV_CONFIRM_FULL: usize = 3;
pub const EV_SQRT_GCD: usize = 4;
pub const EV_LP_FULL: usize = 5;
pub const EV_ECM_EUCLID: usize = 6;
pub type Types = [i64; 29];

/// One stage's per-type counts from its own deltas (ops, tests, phases, event counters).
fn stage_types(t: &str, d_ops: u64, d_tests: u64, ph: &[u64; 21], ev: &[u64; 7]) -> Types {
    let mut o = [0i64; 29];
    let (p, e) = (|i: usize| ph[i] as i64, |i: usize| ev[i] as i64);
    match t {
        "qs" => {
            o[0] = p(qs::MULT);
            o[1] = p(qs::FB);
            o[2] = e(EV_SETUP_FULL);
            o[3] = e(EV_SETUP_EUCLID);
            o[4] = p(qs::SETUP) - e(EV_SETUP_FULL) - e(EV_SETUP_EUCLID);
            o[5] = p(qs::SIEVE) - e(EV_SIEVE_SCAN);
            o[6] = e(EV_SIEVE_SCAN);
            o[7] = e(EV_CONFIRM_FULL);
            o[8] = p(qs::CONFIRM) - e(EV_CONFIRM_FULL);
            o[9] = p(qs::LA);
            o[10] = p(qs::SQRT) - e(EV_SQRT_GCD);
            o[11] = e(EV_SQRT_GCD);
            o[12] = e(EV_LP_FULL);
            o[13] = p(qs::LP) - e(EV_LP_FULL);
            o[14] = p(qs::CHECK);
            o[23] = p(PH_WORD); // re-sieve word ops (zero unless confirm = resieve)
            o[24] = p(PH_GRAY);
            o[25] = p(PH_HASH);
            o[26] = p(PH_SORT);
            o[27] = p(PH_FLOG);
            o[28] = p(PH_FDIV);
        }
        "ecm" => {
            o[15] = p(ecm::ECM_SETUP) - e(EV_ECM_EUCLID);
            o[16] = e(EV_ECM_EUCLID);
            o[17] = p(ecm::ECM_S1) + p(ecm::ECM_S2);
            o[18] = p(ecm::ECM_GCD);
            o[23] = p(PH_WORD);
        }
        "rho" => {
            o[17] = d_ops as i64 - d_tests as i64;
            o[18] = d_tests as i64;
        }
        "pm1" => {
            // stage 2's word ops (NOTES.md, "p-1 stage 2 by prime-gap stepping"); zero without stage 2
            o[17] = d_ops as i64 - d_tests as i64 - p(PH_WORD);
            o[18] = d_tests as i64;
            o[23] = p(PH_WORD);
        }
        "td" => o[19] = d_ops as i64,
        "sq" => o[20] = d_ops as i64,
        "ps" => o[21] = d_ops as i64,
        "cfrac" => o[22] = d_ops as i64,
        other => panic!("no per-type split for {other}"),
    }
    o
}
type R = Result<Option<U256>, Budget>;

// ---- phase-level wall-clock timing (NOTES.md, "Phase-level wall-clock check"; --phasetime, off by default;
// read-only instrumentation: no charge or count depends on it) ------------------------------------------
pub static PT_ON: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);
pub const PT_N: usize = 10;
pub const PT_NAMES: [&str; PT_N] = ["mult", "fb", "setup", "gray", "sieve", "scan", "resieve", "confirm", "lp_ledger", "solve"];
type PtAcc = ([u64; PT_N], [u64; PT_N], [[i64; 29]; PT_N]);
thread_local! {
    static PT: std::cell::RefCell<PtAcc> = std::cell::RefCell::new(([0; PT_N], [0; PT_N], [[0; 29]; PT_N]));
}
pub type Snap = Option<(std::time::Instant, [u64; 21], [u64; 7], u64, u64)>;
#[inline]
fn pt_snap(m: &Meter) -> Snap {
    if PT_ON.load(std::sync::atomic::Ordering::Relaxed) {
        Some((std::time::Instant::now(), m.phases, m.ev, m.ops, m.tests))
    } else {
        None
    }
}
/// Ends a timed region: its wall time, and its own per-type op counts (stage_types on the deltas).
#[inline]
fn pt_end(m: &Meter, r: usize, s: Snap) {
    if let Some((t0, ph0, ev0, o0, te0)) = s {
        let dt = t0.elapsed().as_nanos() as u64;
        let ph: [u64; 21] = std::array::from_fn(|i| m.phases[i] - ph0[i]);
        let ev: [u64; 7] = std::array::from_fn(|i| m.ev[i] - ev0[i]);
        let ty = stage_types("qs", m.ops - o0, m.tests - te0, &ph, &ev);
        PT.with(|p| {
            let mut p = p.borrow_mut();
            p.0[r] += dt;
            p.1[r] += 1;
            for k in 0..29 {
                p.2[r][k] += ty[k];
            }
        });
    }
}
fn pt_take() -> PtAcc {
    PT.with(|p| std::mem::replace(&mut *p.borrow_mut(), ([0; PT_N], [0; PT_N], [[0; 29]; PT_N])))
}

struct Meter {
    ops: u64,
    cap: u64,
    tests: u64,
    hits: u64,
    k: Option<u64>, // instrumentation: the k a square-search win came from
    phases: [u64; 21], // per-phase ops of qs, cfrac and ecm (see qs.rs, cfrac.rs, ecm.rs)
    hook: Option<Box<race::Hook>>, // set only on a race side's meter (race.rs)
    race: Option<(u64, u64, u64)>, // the last race's side A ops, side B ops, switches
    ob: Option<u64>, // the running stage's op budget ("ob"; NOTES.md, "Per-stage op budget")
    ob_spent: u64,   // that stage's own spending
    ob_hit: bool,    // set when the budget, not the cap, ended the stage
    ev: [u64; 7],    // per-type event counters (read-only instrumentation)
    types: Types,    // the run's per-type op counts, added per stage
}

impl Meter {
    #[inline]
    fn tick(&mut self, k: u64) -> Result<(), Budget> {
        self.ops += k;
        if let Some(h) = self.hook.as_mut() {
            h.side_ops += k; // counted before the cap check, as race.py does
        }
        if self.ops > self.cap {
            return Err(Budget);
        }
        if let Some(lim) = self.ob {
            self.ob_spent += k;
            if self.ob_spent > lim {
                self.ob_hit = true; // ended after the charge that took it past ob
                return Err(Budget);
            }
        }
        if let Some(h) = self.hook.as_mut() {
            h.after_charge(k, &mut self.ops)?;
        }
        Ok(())
    }
    #[inline]
    fn charge(&mut self, phase: usize, k: u64) -> Result<(), Budget> {
        self.phases[phase] += k;
        self.tick(k)
    }
    #[inline]
    fn ev(&mut self, i: usize, k: u64) {
        self.ev[i] += k;
    }
    /// What the ps / pm1 prechecks compare against: the cap, or the meter total at which the
    /// running stage's op budget runs out, whichever is lower.
    fn precheck_cap(&self) -> u64 {
        match self.ob {
            Some(lim) => self.cap.min(self.ops - self.ob_spent + lim),
            None => self.cap,
        }
    }
    #[inline]
    fn test(&mut self, hit: bool) {
        self.tests += 1;
        if hit {
            self.hits += 1;
        }
    }
}

struct Num {
    n: U256,
    f: f64, // float(N), correctly rounded, as Python's int -> float
    p: U256,
    q: U256,
}

fn gf(g: &Value, key: &str) -> f64 {
    g[key].as_f64().expect(key)
}
fn gi(g: &Value, key: &str, default: u64) -> u64 {
    g.get(key).and_then(|v| v.as_u64()).unwrap_or(default)
}
fn bit_length(x: u64) -> u64 {
    64 - x.leading_zeros() as u64
}
fn isqrt(x: U256) -> U256 {
    x.root(2)
}
fn absdiff(a: U256, b: U256) -> U256 {
    if a >= b {
        a - b
    } else {
        b - a
    }
}

// ---- trial division -------------------------------------------------------------

fn lamp_td(num: &Num, g: &Value, m: &mut Meter) -> R {
    let lim = num.f.powf(gf(g, "a")) as u128 + 1;
    let n: u128 = num.n.to::<u128>();
    if n % 2 == 0 {
        return Ok(Some(U256::from(2u64)));
    }
    let mut d: u128 = 3;
    while d <= lim {
        m.tick(1)?;
        let hit = n % d == 0;
        m.test(hit);
        if hit {
            return Ok(Some(U256::from(d)));
        }
        d += 2;
    }
    Ok(None)
}

// ---- square search ---------------------------------------------------------------

const SMOOTH_K: [u64; 46] = [
    1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 18, 20, 24, 30, 36, 40, 45, 48, 60, 72, 80, 90, 120,
    144, 180, 210, 240, 360, 420, 480, 720, 840, 1260, 1680, 2520, 5040, 7560, 10080, 15120,
    20160, 25200, 27720, 45360, 50400, 55440,
];
const KS_PRIMES: [u64; 14] = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47];

// I-021 (NOTES.md, "I-021 adopted"): Knuth-Schroeppel scores by multiplicativity of the Legendre symbol.
// (kN / p) = (k / p)(N / p): the 14 symbols of N once per number (N mod p, then the Legendre power), (k / p)
// from a constant table (k <= KS_TMAX; above it, k mod p and the residue table of p). The ln p terms are a
// constant table computed with the old expressions, so the scores are bit-identical to the old ks_score.
pub(crate) const KS_TMAX: u64 = 64;
struct KsTab {
    w1: [f64; 14],
    w2: [f64; 14],
    sym: Vec<Vec<i8>>,
    t: Vec<[i8; 14]>,
    prep_mult: u64,
}
fn ks_tab() -> &'static KsTab {
    static TAB: std::sync::OnceLock<KsTab> = std::sync::OnceLock::new();
    TAB.get_or_init(|| {
        let w1 = std::array::from_fn(|i| (KS_PRIMES[i] as f64).ln() / KS_PRIMES[i] as f64);
        let w2 = std::array::from_fn(|i| 2.0 * (KS_PRIMES[i] as f64).ln() / (KS_PRIMES[i] - 1) as f64);
        let sym: Vec<Vec<i8>> = KS_PRIMES
            .iter()
            .map(|&p| (0..p).map(|r| if r == 0 { 0 } else if powmod_small(r, (p - 1) / 2, p) == 1 { 1 } else { -1 }).collect())
            .collect();
        let t = (0..=KS_TMAX).map(|k| std::array::from_fn(|i| sym[i][(k % KS_PRIMES[i]) as usize])).collect();
        // per number: 14 reductions N mod p + the Legendre powers' bit_length(e) + popcount(e) small multiplies
        let prep_mult = KS_PRIMES.iter().map(|&p| 1 + bit_length((p - 1) / 2) + ((p - 1) / 2).count_ones() as u64).sum();
        KsTab { w1, w2, sym, t, prep_mult }
    })
}

/// (N / p) for the 14 primes: 0, 1 or -1.
fn ks_prep(num: &Num) -> [i8; 14] {
    std::array::from_fn(|i| {
        let p = KS_PRIMES[i];
        let r = powmod_small((num.n % U256::from(p)).to::<u64>(), (p - 1) / 2, p);
        if r == 0 { 0 } else if r == 1 { 1 } else { -1 }
    })
}

/// The score of k, and its charges (mult, word, flog): k*N 1 mult (plus k mod p per prime when k > KS_TMAX),
/// ln k 1 flog, 2 word + 1 per table lookup + 1 per term added.
fn ks_eval(k: u64, num: &Num, legn: &[i8; 14]) -> (f64, (u64, u64, u64)) {
    let tab = ks_tab();
    let kn = U256::from(k) * num.n;
    let r8 = (kn % U256::from(8u64)).to::<u64>();
    let base = if r8 == 1 { 2.0 } else if r8 == 5 { 1.0 } else { 0.5 };
    let mut s = base * 2f64.ln() - 0.5 * (k as f64).ln();
    let row: [i8; 14] = if k <= KS_TMAX {
        tab.t[k as usize]
    } else {
        std::array::from_fn(|i| tab.sym[i][(k % KS_PRIMES[i]) as usize])
    };
    let mut adds = 0u64;
    for i in 0..14 {
        if row[i] == 0 {
            s += tab.w1[i];
            adds += 1;
        } else if row[i] * legn[i] == 1 {
            s += tab.w2[i];
            adds += 1;
        }
    }
    (s, (1 + if k > KS_TMAX { 14 } else { 0 }, 2 + 14 + adds, 1))
}

/// Scores for cands, and the summed charges (mult incl. the per-number symbols, word, flog).
pub(crate) fn ks_rank(num: &Num, cands: &[u64]) -> (Vec<f64>, (u64, u64, u64)) {
    let legn = ks_prep(num);
    let (mut mu, mut wo, mut fl) = (ks_tab().prep_mult, 0u64, 0u64);
    let sc = cands
        .iter()
        .map(|&k| {
            let (s, (a, b, c)) = ks_eval(k, num, &legn);
            mu += a;
            wo += b;
            fl += c;
            s
        })
        .collect();
    (sc, (mu, wo, fl))
}

/// The per-number part of ks_rank's mult charge (the 14 symbols of N).
pub(crate) fn ks_prep_mult() -> u64 {
    ks_tab().prep_mult
}

fn powmod_small(mut b: u64, mut e: u64, m: u64) -> u64 {
    let mut r = 1 % m;
    b %= m;
    while e > 0 {
        if e & 1 == 1 {
            r = r * b % m;
        }
        b = b * b % m;
        e >>= 1;
    }
    r
}

fn sq_one_k(num: &Num, g: &Value, k: u64, m: &mut Meter) -> R {
    let mut kn = U256::from(k) * num.n;
    // truthiness as in lamps.py (bool, or a number != 0; NOTES.md, "sq ksq parsing")
    let ksq = g["ksq"].as_bool().or_else(|| g["ksq"].as_f64().map(|v| v != 0.0)).unwrap_or(false);
    if ksq {
        kn *= U256::from(4u64);
    }
    // Same window as lamps.py: x0 ..= s + floor(f + width), with sqrt(kN) ~ s + f.
    let s = isqrt(kn);
    let exact = s * s == kn;
    let x0 = if exact { s } else { s + U256::from(1u64) };
    let f = (kn - s * s).to::<u128>() as f64 / (s * U256::from(2u64)).to::<u128>() as f64;
    let width = gf(g, "c") * num.f.powf(gf(g, "w")) / (k as f64).sqrt();
    let steps = (f + width).floor() as u64;
    let w = (if exact { steps + 1 } else { steps }).max(1);
    for i in 0..w {
        m.tick(1)?;
        let x = x0 + U256::from(i);
        let t = x * x - kn;
        let y = isqrt(t);
        let ok = y * y == t;
        m.test(ok);
        if ok {
            let d = (x - y).gcd(num.n);
            if d > U256::from(1u64) && d < num.n {
                m.k = Some(k);
                return Ok(Some(d));
            }
        }
    }
    Ok(None)
}

fn lamp_sq(num: &Num, g: &Value, m: &mut Meter) -> R {
    let kk = (num.f.powf(gf(g, "k")) as u64).max(1);
    let mult = gi(g, "mult", 1);
    match g["mode"].as_str().unwrap() {
        "one" => sq_one_k(num, g, 1, m),
        "seq" => {
            for k in 1..=kk {
                if let Some(d) = sq_one_k(num, g, k, m)? {
                    return Ok(Some(d));
                }
            }
            Ok(None)
        }
        "seqm" => {
            for i in 1..=kk {
                if let Some(d) = sq_one_k(num, g, mult * i, m)? {
                    return Ok(Some(d));
                }
            }
            Ok(None)
        }
        "smooth" => {
            let mut seen = std::collections::HashSet::new();
            for &k in SMOOTH_K.iter() {
                if k > kk {
                    break;
                }
                m.tick(1)?; // charged insert (NOTES.md, "Meter correction")
                seen.insert(k);
                if let Some(d) = sq_one_k(num, g, k, m)? {
                    return Ok(Some(d));
                }
            }
            for k in 1..=kk {
                m.tick(1)?; // charged membership test
                if !seen.contains(&k) {
                    if let Some(d) = sq_one_k(num, g, k, m)? {
                        return Ok(Some(d));
                    }
                }
            }
            Ok(None)
        }
        "ks" => {
            let chunk = gi(g, "r", 16);
            let mut i = 1u64;
            while i <= kk {
                let hi = kk.min(i + chunk - 1);
                let ks: Vec<u64> = (i..=hi).map(|j| mult * j).collect();
                // I-021: scored by symbols, charged by its work; the per-number symbols with the first block
                let (sc, (mu, wo, fl)) = ks_rank(num, &ks);
                m.tick(if i == 1 { mu } else { mu - ks_prep_mult() } + wo + fl)?;
                let mut block: Vec<(u64, f64)> = ks.iter().zip(&sc).map(|(&k, &s)| (k, -s)).collect();
                block.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap()); // stable, like Python
                for (k, _) in block {
                    if let Some(d) = sq_one_k(num, g, k, m)? {
                        return Ok(Some(d));
                    }
                }
                i += chunk;
            }
            Ok(None)
        }
        other => panic!("unknown square-search mode {other}"),
    }
}

// ---- rho ------------------------------------------------------------------------

fn lamp_rho(num: &Num, g: &Value, m: &mut Meter) -> R {
    let n = num.n;
    let c = U256::from(gi(g, "c", 1));
    let b = gi(g, "b", 1).max(1);
    let d = gi(g, "d", 2);
    let step_cost = (bit_length(d) - 1 + d.count_ones() as u64 - 1).max(1);
    let dd = U256::from(d);
    let f = |v: U256| -> U256 {
        let s = if d == 2 { v.mul_mod(v, n) } else { v.pow_mod(dd, n) };
        s.add_mod(c, n)
    };
    let one = U256::from(1u64);
    let mut y = U256::from(gi(g, "x0", 2));
    let (mut r, mut q, mut gg) = (1u64, one, one);
    let mut x;
    let mut ys = y;
    loop {
        x = y;
        for _ in 0..r {
            y = f(y);
            m.tick(step_cost)?;
        }
        let mut k = 0u64;
        while k < r && gg == one {
            ys = y;
            for _ in 0..b.min(r - k) {
                y = f(y);
                q = q.mul_mod(absdiff(x, y), n);
                m.tick(step_cost + 1)?;
            }
            gg = q.gcd(n);
            m.tick(1)?;
            m.test(gg != one);
            k += b;
        }
        r *= 2;
        if gg != one {
            break;
        }
    }
    if gg == n {
        loop {
            ys = f(ys);
            m.tick(step_cost)?;
            gg = absdiff(x, ys).gcd(n);
            m.tick(1)?;
            m.test(gg != one);
            if gg > one {
                break;
            }
        }
    }
    Ok(if gg > one && gg < n { Some(gg) } else { None })
}

// ---- p - 1 ------------------------------------------------------------------------

fn lamp_pm1(num: &Num, g: &Value, m: &mut Meter) -> R {
    // the absolute bound "B" if given (NOTES.md, "(A1)"), else N^b
    let bnd = match g.get("B").and_then(|v| v.as_u64()) {
        Some(b) => b,
        None => (num.f.powf(gf(g, "b")) as u64).max(10),
    };
    // Each prime ticks at least once, so if even a lower bound on pi(B) can't fit in the
    // remaining budget the run would miss anyway; stop before sieving a huge range.
    let lower_pi = bnd as f64 / (bnd as f64).ln();
    if bnd > (1 << 26) && (m.ops as f64 + lower_pi) > m.precheck_cap() as f64 {
        return Err(Budget);
    }
    // Bit-packed sieve (one bit per number): a bound near 2^31 takes 256 MB, not 2 GB.
    let words = bnd as usize / 64 + 1;
    let mut composite = vec![0u64; words];
    composite[0] |= 0b11; // 0 and 1
    let is_comp = |c: &Vec<u64>, i: usize| (c[i / 64] >> (i % 64)) & 1 == 1;
    let mut i = 2usize;
    while i * i <= bnd as usize {
        if !is_comp(&composite, i) {
            let mut j = i * i;
            while j <= bnd as usize {
                composite[j / 64] |= 1 << (j % 64);
                j += i;
            }
        }
        i += 1;
    }
    let n = num.n;
    let mut a = U256::from(2u64);
    for p in 2..=bnd {
        if is_comp(&composite, p as usize) {
            continue;
        }
        let mut pk = p;
        while (pk as u128) * (p as u128) <= bnd as u128 {
            // u128: for a bound past 2^32, p * p overflows u64 (Python's ints don't)
            pk *= p;
        }
        a = a.pow_mod(U256::from(pk), n);
        m.tick(bit_length(pk).max(1))?;
    }
    let d = if a == U256::ZERO { U256::from(1u64) } else { (a - U256::from(1u64)).gcd(n) };
    m.tick(1)?;
    m.test(d != U256::from(1u64));
    let c = g.get("c").and_then(|v| v.as_f64()).unwrap_or(0.0) as u64;
    if d != U256::from(1u64) || c == 0 {
        return Ok(if d > U256::from(1u64) && d < n { Some(d) } else { None });
    }
    pm1_stage2(n, a, bnd, c * bnd, m)
}

/// Stage 2 by prime-gap stepping over the primes in (B, B2] (NOTES.md, "p-1 stage 2 by prime-gap stepping: cost
/// model, completed for the code"): a gap table D[2j] = a^(2j), X = a^q1 by square-and-multiply, then per prime
/// 2 mul + 3 word (1 mul + 1 word for q1); a gcd of the running product every 64 primes and after the last; a gcd
/// of N backtracks through that batch prime by prime.
fn pm1_stage2(n: U256, a: U256, bnd: u64, b2: u64, m: &mut Meter) -> R {
    let qs: Vec<u64> = qs::primes_upto(b2).into_iter().filter(|&q| q > bnd).collect();
    if qs.is_empty() {
        return Ok(None);
    }
    let gmax = qs.windows(2).map(|w| w[1] - w[0]).max().unwrap_or(2) as usize;
    let mut tab = vec![U256::ZERO; gmax + 1];
    tab[2] = a.mul_mod(a, n);
    m.tick(1)?;
    let mut j = 4;
    while j <= gmax {
        tab[j] = tab[j - 2].mul_mod(tab[2], n);
        m.tick(1)?;
        j += 2;
    }
    let q1 = qs[0];
    let mut x = a;
    for bit in (0..bit_length(q1) - 1).rev() {
        // left to right: bit_length - 1 squarings, popcount - 1 multiplies
        x = x.mul_mod(x, n);
        m.tick(1)?;
        if (q1 >> bit) & 1 == 1 {
            x = x.mul_mod(a, n);
            m.tick(1)?;
        }
    }
    let one = U256::from(1u64);
    let mut acc = one;
    let (mut x_batch, mut i_batch) = (x, 0usize);
    for i in 0..qs.len() {
        if i > 0 {
            m.charge(PH_WORD, 2)?; // the gap and the table index
            x = x.mul_mod(tab[(qs[i] - qs[i - 1]) as usize], n);
            m.tick(1)?;
        }
        m.charge(PH_WORD, 1)?; // X - 1
        acc = acc.mul_mod(x.wrapping_sub(one).wrapping_add(n) % n, n);
        m.tick(1)?;
        if (i + 1) % 64 == 0 || i == qs.len() - 1 {
            let gg = acc.gcd(n);
            m.tick(1)?;
            m.test(gg != one);
            if gg > one && gg < n {
                return Ok(Some(gg));
            }
            if gg == n {
                return pm1_backtrack(n, &qs, &tab, x_batch, i_batch, i, m);
            }
            x_batch = x;
            i_batch = i + 1;
        }
    }
    Ok(None)
}

/// Prime by prime through one batch from X (before its first step): the step, X - 1 and a gcd each.
fn pm1_backtrack(n: U256, qs: &[u64], tab: &[U256], mut x: U256, i0: usize, i1: usize, m: &mut Meter) -> R {
    let one = U256::from(1u64);
    for i in i0..=i1 {
        if i > 0 {
            m.charge(PH_WORD, 2)?;
            x = x.mul_mod(tab[(qs[i] - qs[i - 1]) as usize], n);
            m.tick(1)?;
        }
        m.charge(PH_WORD, 1)?;
        let gg = (x.wrapping_sub(one).wrapping_add(n) % n).gcd(n);
        m.tick(1)?;
        m.test(gg != one);
        if gg != one {
            return Ok(if gg < n { Some(gg) } else { None });
        }
    }
    Ok(None)
}

// ---- block flash (replay) ------------------------------------------------------------
//
// lamps.py's block flash builds f(x) = (x+1)...(x+B) with a product tree and evaluates it at
// every block start with a remainder tree. Every polynomial product is charged by length
// alone (FFT cost model), so the whole charge depends only on B and the number of blocks.
// Which block's gcd first exceeds 1 is fixed by where p and q sit: block i holds stations
// iB+1..iB+B, and its product is divisible by p exactly when that range holds a multiple of p.
// So the replay charges the same products in the same order and finds the same block,
// without redoing the arithmetic. The parity test against lamps.py checks this.

fn fft_cost(n_out: u64) -> u64 {
    let mut n = 1u64;
    while n < n_out {
        n *= 2;
    }
    3 * (n / 2) * (bit_length(n) - 1).max(1) + n
}

fn pmul_len(la: usize, lb: usize, m: &mut Meter) -> Result<usize, Budget> {
    if la == 0 || lb == 0 {
        return Ok(0);
    }
    m.tick(fft_cost((la + lb - 1) as u64))?;
    Ok(la + lb - 1)
}

fn product_tree_len(leaves: usize, m: &mut Meter) -> Result<Vec<Vec<usize>>, Budget> {
    let mut tree = vec![vec![2usize; leaves]];
    while tree.last().unwrap().len() > 1 {
        let lvl = tree.last().unwrap().clone();
        let mut nxt = Vec::with_capacity(lvl.len() / 2 + 1);
        let mut i = 0;
        while i < lvl.len() {
            if i + 1 < lvl.len() {
                nxt.push(pmul_len(lvl[i], lvl[i + 1], m)?);
            } else {
                nxt.push(lvl[i]);
            }
            i += 2;
        }
        tree.push(nxt);
    }
    Ok(tree)
}

fn inv_series_len(lg: usize, k: usize, m: &mut Meter) -> Result<usize, Budget> {
    let mut lh = 1usize;
    let mut prec = 1usize;
    while prec < k {
        prec = (2 * prec).min(k);
        let gh = pmul_len(lg.min(prec), lh, m)?.min(prec);
        lh = pmul_len(lh, gh, m)?.min(prec);
    }
    Ok(lh)
}

fn pmod_len(la: usize, lb: usize, m: &mut Meter) -> Result<usize, Budget> {
    let (da, db) = (la as i64 - 1, lb as i64 - 1);
    if da < db {
        return Ok(la);
    }
    let k = (da - db + 1) as usize;
    let linv = inv_series_len(lb, k, m)?;
    let lq = pmul_len(la.min(k), linv, m)?.min(k);
    pmul_len(lb, lq, m)?;
    Ok(db as usize)
}

fn lamp_ps(num: &Num, g: &Value, m: &mut Meter) -> R {
    let l = (num.f.powf(gf(g, "a")) as u64) + 1;
    let b = ((gf(g, "c") * num.f.powf(gf(g, "s"))) as u64).max(2);
    let nblocks = (l + b - 1) / b;
    // Same guard as lamps.py: the two product trees charge at least one op per merge, so if
    // that can't fit, the run misses before any test; stop before allocating b leaves.
    if m.ops + (b - 1) + (nblocks - 1) > m.precheck_cap() {
        return Err(Budget);
    }
    let f_len = product_tree_len(b as usize, m)?.last().unwrap()[0];
    let tree = product_tree_len(nblocks as usize, m)?;
    let mut rems = vec![pmod_len(f_len, tree.last().unwrap()[0], m)?];
    for lvl in (0..tree.len().saturating_sub(1)).rev() {
        let mut nxt = Vec::with_capacity(tree[lvl].len());
        for (i, &node) in tree[lvl].iter().enumerate() {
            nxt.push(pmod_len(rems[i / 2], node, m)?);
        }
        rems = nxt;
    }
    let (p, q, n) = (num.p, num.q, num.n);
    let bb = U256::from(b);
    let has_multiple = |prime: U256, i: u64| -> bool {
        let lo = U256::from(i) * bb; // block covers lo+1 ..= lo+B
        (lo + bb) / prime > lo / prime
    };
    for i in 0..nblocks {
        m.tick(1)?;
        let (hp, hq) = (has_multiple(p, i), has_multiple(q, i));
        if !hp && !hq {
            continue;
        }
        if hp != hq {
            return Ok(Some(if hp { p } else { q }));
        }
        let lo = U256::from(i) * bb;
        for j in 1..=b {
            m.tick(1)?;
            let st = lo + U256::from(j);
            if st > U256::from(1u64) && n % st == U256::ZERO {
                return Ok(Some(st));
            }
        }
    }
    Ok(None)
}

// ---- driver ---------------------------------------------------------------------------

struct Win {
    ops: u64,
    d: U256,
    stage: usize,
    k: Option<u64>,
}

fn run_stage(num: &Num, s: &Value, m: &mut Meter) -> R {
    match s["t"].as_str().unwrap() {
        "td" => lamp_td(num, s, m),
        "sq" => lamp_sq(num, s, m),
        "rho" => lamp_rho(num, s, m),
        "pm1" => lamp_pm1(num, s, m),
        "ps" => lamp_ps(num, s, m),
        "qs" => qs::lamp_qs(num, s, m),
        "cfrac" => cfrac::lamp_cfrac(num, s, m),
        "ecm" => ecm::lamp_ecm(num, s, m),
        "race" => race::lamp_race(num, s, m),
        other => panic!("unknown lamp {other}"),
    }
}

type RunOut = (Option<Win>, u64, u64, [u64; 21], Option<(u64, u64, u64)>, Types);

fn run(genome: &[Value], num: &Num, cap: u64) -> RunOut {
    for s in genome {
        // rejected before any number runs, as lamps.validate_genome
        if let Some(v) = s.get("ob") {
            assert!(v.is_u64(), "ob must be a non-negative integer");
        }
        if s["t"] == "race" {
            assert!(s.get("ob").is_none() && s["a"].get("ob").is_none() && s["b"].get("ob").is_none(),
                    "ob is not allowed on a race or its sides");
            race::validate(s);
        }
    }
    let mut m = Meter { ops: 0, cap, tests: 0, hits: 0, k: None, phases: [0; 21], hook: None, race: None,
                        ob: None, ob_spent: 0, ob_hit: false, ev: [0; 7], types: [0; 29] };
    for (i, s) in genome.iter().enumerate() {
        let ob = s.get("ob").and_then(|v| v.as_u64());
        if ob == Some(0) {
            continue; // skipped: no lamp code runs
        }
        m.ob = ob;
        m.ob_spent = 0;
        let start = m.ops;
        let (t0, ph0, ev0) = (m.tests, m.phases, m.ev);
        let r = run_stage(num, s, &mut m);
        if s["t"] != "race" {
            // a race adds its sides' split itself (race.rs)
            let ph: [u64; 21] = std::array::from_fn(|i| m.phases[i] - ph0[i]);
            let ev: [u64; 7] = std::array::from_fn(|i| m.ev[i] - ev0[i]);
            let st = stage_types(s["t"].as_str().unwrap(), m.ops - start, m.tests - t0, &ph, &ev);
            for (a, b) in m.types.iter_mut().zip(st.iter()) {
                *a += b;
            }
        }
        // a precheck (no charge crossed the cap) that the stage's budget made binding ends
        // the stage, not the run
        let precheck_ob = matches!(r, Err(Budget)) && !m.ob_hit && m.ops <= cap
            && ob.map_or(false, |lim| start + lim < cap);
        let ended_by_ob = m.ob_hit || precheck_ob;
        m.ob = None;
        m.ob_hit = false;
        match r {
            Ok(Some(d)) => {
                let w = Win { ops: m.ops, d, stage: i, k: m.k };
                return (Some(w), m.tests, m.hits, m.phases, m.race, m.types);
            }
            Ok(None) => continue,
            Err(Budget) if ended_by_ob => continue, // the stage's budget: next stage
            Err(Budget) => return (None, m.tests, m.hits, m.phases, m.race, m.types),
        }
    }
    (None, m.tests, m.hits, m.phases, m.race, m.types)
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    let genome: Value = serde_json::from_str(&lines.next().unwrap().unwrap()).unwrap();
    let genome = genome.as_array().unwrap().clone();
    let cap: u64 = lines.next().unwrap().unwrap().trim().parse().unwrap();
    let phased = |s: &Value| s["t"] == "qs" || s["t"] == "cfrac" || s["t"] == "ecm";
    let has_qs = genome.iter().any(|s| phased(s) || (s["t"] == "race" && (phased(&s["a"]) || phased(&s["b"]))));
    let has_race = genome.iter().any(|s| s["t"] == "race");
    let types_out = std::env::args().any(|a| a == "--types");
    if std::env::args().any(|a| a == "--phasetime") {
        PT_ON.store(true, std::sync::atomic::Ordering::Relaxed);
        // the per-region overhead: an empty snap / end pair on a dummy meter, timed in a loop
        let dm = Meter { ops: 0, cap: u64::MAX, tests: 0, hits: 0, k: None, phases: [0; 21], hook: None, race: None,
                         ob: None, ob_spent: 0, ob_hit: false, ev: [0; 7], types: [0; 29] };
        let reps = 200_000u64;
        let t0 = std::time::Instant::now();
        for _ in 0..reps {
            pt_end(&dm, 0, pt_snap(&dm));
        }
        let per = t0.elapsed().as_nanos() as f64 / reps as f64;
        pt_take();
        eprintln!("{{\"overhead_ns_per_region\": {per:.2}}}");
    }
    // test hook for the per-type mutation check: "<type>:drop" or "<type>:double", applied
    // to the output only
    let mutate: Option<(usize, bool)> = std::env::var("LAMPCORE_TYPES_MUTATE").ok().map(|v| {
        let (name, how) = v.split_once(':').unwrap();
        (TYPE_NAMES.iter().position(|t| *t == name).unwrap(), how == "double")
    });
    let out = io::stdout();
    let mut out = BufWriter::new(out.lock());
    for line in lines {
        let line = line.unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.is_empty() {
            continue;
        }
        let n: U256 = parts[0].parse().unwrap();
        let p: U256 = parts[1].parse().unwrap();
        let q: U256 = parts[2].parse().unwrap();
        let num = Num { n, f: n.to::<u128>() as f64, p, q };
        let (res, t, h, ph, rc, mut ty) = run(&genome, &num, cap);
        if PT_ON.load(std::sync::atomic::Ordering::Relaxed) {
            let (ns, calls, tys) = pt_take();
            let tyj: Vec<String> = tys.iter().map(|r| format!("[{}]", r.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(","))).collect();
            eprintln!("{{\"N\": \"{n}\", \"regions\": {:?}, \"ns\": {:?}, \"calls\": {:?}, \"types\": [{}]}}", PT_NAMES, ns, calls, tyj.join(","));
        }
        let mut tail = if has_qs {
            ph.iter().map(|x| format!(" {x}")).collect::<String>()
        } else {
            String::new()
        };
        if has_race {
            let (a, b, sw) = rc.unwrap_or((0, 0, 0));
            tail += &format!(" R {a} {b} {sw}");
        }
        if types_out {
            if let Some((i, double)) = mutate {
                ty[i] = if double { 2 * ty[i] } else { 0 };
            }
            tail += " T";
            for x in ty.iter() {
                tail += &format!(" {x}");
            }
        }
        match res {
            Some(w) => {
                let k = w.k.map_or("-".to_string(), |k| k.to_string());
                writeln!(out, "{} {} {t} {h} {} {k}{tail}", w.ops, w.d, w.stage).unwrap()
            }
            None => writeln!(out, "miss {t} {h}{tail}").unwrap(),
        }
    }
}
