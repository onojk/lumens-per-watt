//! Quadratic sieve card ("qs"): a line-by-line port of evolve/qs.py and evolve/ledger.py,
//! with every charge made at the same point and in the same chunk as the Python, so op
//! counts, tests, hits, and the per-phase breakdown agree exactly (checked by parity.py).
//! Cost model: NOTES.md. Split as the Python is (PLAN.md, "Relation economy"): a source
//! (sieve_source: phases 1, 3, 4, 5, 8) feeding a Ledger (phases 2, 6, 7, and 9 when the
//! source turns the relation check on), one per k.
//!
//! Values of size kN live in i128 (N must stay below 2^100); products mod N use U256.

use super::{ks_rank, Budget, Meter, Num, R};
use ruint::aliases::U256;
use serde_json::Value;

pub const MULT: usize = 0;
pub const FB: usize = 1;
pub const SETUP: usize = 2;
pub const SIEVE: usize = 3;
pub const CONFIRM: usize = 4;
pub const LA: usize = 5;
pub const SQRT: usize = 6;
const SF32: [u64; 20] = [1, 2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31]; // squarefree k <= 32
pub const LP: usize = 7; // large primes (Stage 7), only when lc > 1
pub const CHECK: usize = 8; // the ledger's relation check, opt-in ("check": 1)

const DELTA: usize = 10; // surplus relations: rows = F + DELTA

pub(crate) fn gene(g: &Value, key: &str, default: f64) -> f64 {
    g.get(key).and_then(|v| v.as_f64()).unwrap_or(default)
}

pub(crate) fn primes_upto(n: u64) -> Vec<u64> {
    let mut s = vec![true; n as usize + 1];
    s[0] = false;
    if n >= 1 {
        s[1] = false;
    }
    let mut i = 2usize;
    while i * i <= n as usize {
        if s[i] {
            let mut j = i * i;
            while j <= n as usize {
                s[j] = false;
                j += i;
            }
        }
        i += 1;
    }
    (0..=n).filter(|&i| s[i as usize]).collect()
}

/// Square-and-multiply mod a small prime, 1 op per modular multiply, the base reduction
/// counted as the first (bit_length(e) + popcount(e) - 1 in all). `b` is already b mod p.
fn cpow_small(b: u64, e: u64, p: u64, ph: usize, m: &mut Meter) -> Result<(u64, u64), Budget> {
    let mut r = b % p;
    m.charge(ph, 1)?;
    let mut n = 1u64;
    let bl = 64 - e.leading_zeros();
    for i in (0..bl.saturating_sub(1)).rev() {
        r = r * r % p;
        m.charge(ph, 1)?;
        n += 1;
        if (e >> i) & 1 == 1 {
            r = r * b % p;
            m.charge(ph, 1)?;
            n += 1;
        }
    }
    Ok((r, n))
}

/// The same, mod N.
fn cpow_n(b: u64, e: u64, n: U256, ph: usize, m: &mut Meter) -> Result<U256, Budget> {
    let bb = U256::from(b) % n;
    let mut r = bb;
    m.charge(ph, 1)?;
    let bl = 64 - e.leading_zeros();
    for i in (0..bl.saturating_sub(1)).rev() {
        r = r.mul_mod(r, n);
        m.charge(ph, 1)?;
        if (e >> i) & 1 == 1 {
            r = r.mul_mod(bb, n);
            m.charge(ph, 1)?;
        }
    }
    Ok(r)
}

/// Inverse of a mod `md` by extended Euclid, charged 1 op per division step (one chunk).
fn euclid_inv(a: i128, md: i128, ph: usize, m: &mut Meter) -> Result<i128, Budget> {
    let (mut r0, mut r1, mut s0, mut s1, mut steps) = (md, a.rem_euclid(md), 0i128, 1i128, 0u64);
    while r1 != 0 {
        let q = r0.div_euclid(r1);
        let (nr, ns) = (r0 - q * r1, s0 - q * s1);
        r0 = r1;
        r1 = nr;
        s0 = s1;
        s1 = ns;
        steps += 1;
    }
    m.charge(ph, steps)?;
    if ph == SETUP {
        m.ev(crate::EV_SETUP_EUCLID, steps); // per-type counter: Python's at["inv"] append
    }
    Ok(s0.rem_euclid(md))
}

/// euclid_inv in i64 (fix C.1, NOTES.md): the same steps and charges, for moduli and inputs below 2^62.
fn euclid_inv64(a: i64, md: i64, ph: usize, m: &mut Meter) -> Result<i64, Budget> {
    let (mut r0, mut r1, mut s0, mut s1, mut steps) = (md, a.rem_euclid(md), 0i64, 1i64, 0u64);
    while r1 != 0 {
        let q = r0.div_euclid(r1);
        let (nr, ns) = (r0 - q * r1, s0 - q * s1);
        r0 = r1;
        r1 = nr;
        s0 = s1;
        s1 = ns;
        steps += 1;
    }
    m.charge(ph, steps)?;
    if ph == SETUP {
        m.ev(crate::EV_SETUP_EUCLID, steps); // per-type counter: Python's at["inv"] append
    }
    Ok(s0.rem_euclid(md))
}

/// sqrt(n) mod p for a nonzero residue n, charged 1 op per modular multiply.
fn tonelli(n: u64, p: u64, m: &mut Meter) -> Result<u64, Budget> {
    if p % 4 == 3 {
        return Ok(cpow_small(n, (p + 1) / 4, p, FB, m)?.0);
    }
    let (mut q, mut s) = (p - 1, 0u32);
    while q % 2 == 0 {
        q /= 2;
        s += 1;
    }
    let mut z = 2u64;
    loop {
        let (t, _) = cpow_small(z % p, (p - 1) / 2, p, FB, m)?;
        if t == p - 1 {
            break;
        }
        z += 1;
    }
    let (mut cz, _) = cpow_small(z % p, q, p, FB, m)?;
    let (mut t, _) = cpow_small(n, q, p, FB, m)?;
    let (mut r, _) = cpow_small(n, (q + 1) / 2, p, FB, m)?;
    let mut mm = s;
    while t != 1 {
        let (mut i, mut t2) = (0u32, t);
        while t2 != 1 {
            t2 = t2 * t2 % p;
            i += 1;
        }
        let mut b = cz;
        for _ in 0..(mm - i - 1) {
            b = b * b % p;
        }
        r = r * b % p;
        cz = b * b % p;
        t = t * cz % p;
        m.charge(FB, (i + (mm - i - 1) + 3) as u64)?;
        mm = i;
    }
    Ok(r)
}

/// sort_charge (NOTES.md, "The sort_charge option"): n ceil(log2 n) comparisons for n >= 2.
fn sort_cost(n: u64) -> u64 {
    if n >= 2 { n * (64 - (n - 1).leading_zeros()) as u64 } else { 0 }
}

/// All s-element combinations of `pool`, in itertools.combinations order.
fn combinations(pool: &[u64], s: usize) -> Vec<Vec<u64>> {
    let n = pool.len();
    let mut out = Vec::new();
    if s > n {
        return out;
    }
    let mut idx: Vec<usize> = (0..s).collect();
    loop {
        out.push(idx.iter().map(|&i| pool[i]).collect());
        let mut i = s as isize - 1;
        while i >= 0 && idx[i as usize] == i as usize + n - s {
            i -= 1;
        }
        if i < 0 {
            return out;
        }
        idx[i as usize] += 1;
        for j in i as usize + 1..s {
            idx[j] = idx[j - 1] + 1;
        }
    }
}

pub fn lamp_qs(num: &Num, g: &Value, m: &mut Meter) -> R {
    let n = num.n;
    if n % U256::from(2u64) == U256::ZERO {
        return Ok(Some(U256::from(2u64)));
    }
    if n >= U256::from(1u128 << 100) {
        // kN-sized values live in i128: refuse rather than risk a silent wrap
        eprintln!("lampcore: qs supports N < 2^100, got a {}-bit N", n.bit_len());
        std::process::exit(2);
    }
    // 1. multiplier
    // kset "sf32" (NOTES.md, "kc becomes a constant"): the squarefree k <= 32; absent: 1..kc
    let cands: Vec<u64> = if g.get("kset").and_then(|v| v.as_str()) == Some("sf32") {
        SF32.to_vec()
    } else {
        (1..=(gene(g, "kc", 16.0) as u64).max(1)).collect()
    };
    let kc = cands.len() as u64;
    let pt = crate::pt_snap(m);
    // I-021 (NOTES.md, "I-021 adopted"): symbols, charged by the work
    let (sc, (mu, wo, fl)) = ks_rank(num, &cands);
    m.charge(MULT, mu)?;
    m.charge(crate::PH_WORD, wo)?;
    m.charge(crate::PH_FLOG, fl)?;
    let mut ranked: Vec<(u64, f64)> = cands.iter().zip(&sc).map(|(&k, &s)| (k, -s)).collect();
    ranked.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap().then(a.0.cmp(&b.0)));
    if gene(g, "sort_charge", 0.0) != 0.0 {
        m.charge(crate::PH_SORT, sort_cost(kc))?; // sort_charge: the multiplier ranking (audit item 2: sort_cmp)
    }
    crate::pt_end(m, 0, pt);
    let ln_n = num.f.ln();
    let bnd = ((gene(g, "bc", 1.5) * (0.5 * (ln_n * ln_n.ln()).sqrt()).exp()) as u64).max(30);
    // a failed attempt is retried with the next k: a fresh ledger (2. factor base) for each
    for (k, _) in ranked {
        let pt = crate::pt_snap(m);
        let built = Ledger::build(num, k, bnd, m)?;
        crate::pt_end(m, 1, pt);
        let mut led = match built {
            Ok(led) => led,
            Err(p) => return Ok(Some(p)), // p divides N
        };
        if let Some(d) = sieve_source(num, g, k, &mut led, m)? {
            return Ok(Some(d));
        }
        if led.full() {
            let pt = crate::pt_snap(m);
            let solved = led.solve(m)?;
            crate::pt_end(m, 9, pt);
            if let Some(d) = solved {
                return Ok(Some(d));
            }
        }
    }
    Ok(None)
}

/// Relation ledger (evolve/ledger.py): one N, one multiplier k, one factor base. Owns the
/// factor base (phase 2), dedupe (free), linear algebra (6) and the square root (7).
pub(crate) struct Ledger {
    n: U256,
    pub(crate) n_i: i128,
    bnd: u64, // factor-base bound B
    pub(crate) base: Vec<i64>,
    roots_t: Vec<u64>, // parallel to base
    pub(crate) f: usize,
    need: usize,
    // relations (u, vec, y): u^2 = y^2 prod p^e (mod N); y = 1 for a full relation
    rels: Vec<(i128, u32, u32, i128)>, // (u, offset, length, y): the sparse [(j, e)] in `arena` (step 1; fix C.2)
    arena: Vec<(u32, u32)>,
    seen: std::collections::HashSet<i128>,   // full |u|'s
    seen_c: std::collections::HashSet<i128>, // combined u's, up to sign
}

impl Ledger {
    /// Phase 2: -1, 2, primes dividing k, odd primes with (kN | p) = 1. Err(p) if a prime
    /// p dividing N turns up.
    pub(crate) fn build(num: &Num, k: u64, bnd: u64, m: &mut Meter) -> Result<Result<Ledger, U256>, Budget> {
        let n = num.n;
        let kn_u = U256::from(k) * n;
        let mut base: Vec<i64> = vec![-1, 2];
        let mut roots_t: Vec<u64> = vec![0, 0];
        for p in primes_upto(bnd).into_iter().skip(1) {
            let e = (p - 1) / 2;
            let knp = (kn_u % U256::from(p)).to::<u64>();
            let (leg, _) = cpow_small(knp, e, p, FB, m)?;
            if knp == 0 {
                if k % p != 0 {
                    return Ok(Err(U256::from(p)));
                }
                base.push(p as i64);
                roots_t.push(0);
                continue;
            }
            if leg != 1 {
                continue;
            }
            let t = tonelli(knp, p, m)?;
            base.push(p as i64);
            roots_t.push(t);
        }
        let f = base.len();
        Ok(Ok(Ledger {
            n,
            n_i: n.to::<u128>() as i128,
            bnd,
            base,
            roots_t,
            f,
            need: f + DELTA,
            rels: Vec::new(),
            arena: Vec::new(),
            seen: std::collections::HashSet::new(),
            seen_c: std::collections::HashSet::new(),
        }))
    }

    /// Relation i's sparse exponent list.
    fn rv(&self, i: usize) -> &[(u32, u32)] {
        let r = &self.rels[i];
        &self.arena[r.1 as usize..(r.1 + r.2) as usize]
    }

    pub(crate) fn full(&self) -> bool {
        self.rels.len() >= self.need
    }

    /// y^(1 or 2) * prod p^(e_p or e_p/2) mod N over entries p >= 2, charged to CHECK:
    /// square-and-multiply per factor, 1 op per multiply joining it after the first.
    fn product(&self, v: &[(u32, u32)], y: i128, half: bool, m: &mut Meter) -> Result<U256, Budget> {
        let mut factors: Vec<(u64, u64)> = v
            .iter()
            .filter(|&&(j, _)| j >= 1)
            .map(|&(j, e)| (self.base[j as usize] as u64, if half { e as u64 / 2 } else { e as u64 }))
            .collect();
        if y != 1 {
            factors.push((y as u64, if half { 1 } else { 2 }));
        }
        let mut r: Option<U256> = None;
        for (b, e) in factors {
            let x = cpow_n(b, e, self.n, CHECK, m)?;
            r = Some(match r {
                None => x,
                Some(prev) => {
                    let z = prev.mul_mod(x, self.n);
                    m.charge(CHECK, 1)?;
                    z
                }
            });
        }
        Ok(r.unwrap_or(U256::from(1u64)))
    }

    /// Phase 9 (NOTES.md, "Ledger: the charged relation check"): is u^2 = y^2 prod p^e
    /// (mod N), and not a trivial all-even relation?
    fn check(&self, u: i128, v: &[(u32, u32)], y: i128, m: &mut Meter) -> Result<bool, Budget> {
        let n = self.n;
        let ur = U256::from(u.rem_euclid(self.n_i) as u128);
        m.charge(CHECK, 1)?; // u reduced mod N (cpow's first op)
        let lhs = ur.mul_mod(ur, n);
        m.charge(CHECK, 1)?; // the square
        let mut rhs = self.product(v, y, false, m)?;
        if v.iter().any(|&(j, e)| j == 0 && e & 1 == 1) {
            rhs = (n - rhs) % n;
            m.charge(CHECK, 1)?;
        }
        m.charge(CHECK, 1)?; // compare
        if lhs != rhs {
            return Ok(false);
        }
        m.charge(CHECK, ((self.f + 63) / 64) as u64)?; // parity scan
        if v.iter().any(|&(_, e)| e & 1 == 1) {
            return Ok(true);
        }
        let yy = self.product(v, y, true, m)?; // all even: a one-row dependency
        m.charge(CHECK, 2)?; // u = Y, u = N - Y
        Ok(ur != yy && ur != (n - yy) % n)
    }

    /// Keep the relation unless it fails the check (when on) or repeats one already kept.
    /// True once full.
    pub(crate) fn add(&mut self, u: i128, v: &[(u32, u32)], y: i128, chk: bool, m: &mut Meter) -> Result<bool, Budget> {
        if chk && !self.check(u, v, y, m)? {
            return Ok(false);
        }
        // the duplicate check (NOTES.md, "Meter correction"): 2 word ops (full), 3 (combined: also min(cu, N - cu))
        m.charge(crate::PH_HASH, 1)?; // audit item 0: the probe-and-insert is a hash op
        m.charge(crate::PH_WORD, if y == 1 { 1 } else { 2 })?;
        let fresh = if y == 1 { self.seen.insert(u.abs()) } else { self.seen_c.insert(u.min(self.n_i - u)) };
        if !fresh {
            return Ok(false);
        }
        let off = self.arena.len() as u32;
        self.arena.extend_from_slice(v);
        self.rels.push((u, off, v.len() as u32, y));
        Ok(self.full())
    }

    /// Phases 6 and 7 on a full ledger: a factor, or None if no dependency splits N.
    pub(crate) fn solve(&self, m: &mut Meter) -> R {
        let (n, n_i, f, rels, base) = (self.n, self.n_i, self.f, &self.rels, &self.base);
        // 6. linear algebra: dense GF(2) elimination
        let rows = rels.len();
        m.charge(LA, ((rows * f * rows + 63) / 64) as u64)?;
        let cw = (f + 63) / 64;
        let rw = (rows + 63) / 64;
        // GF(2) rows (bit-packed) built from the sparse relations, 1 word per entry (step 1)
        m.charge(crate::PH_WORD, rels.iter().map(|r| r.2 as u64).sum())?;
        let mut mat: Vec<Vec<u64>> = rels
            .iter()
            .enumerate()
            .map(|(i, _)| {
                let mut w = vec![0u64; cw];
                for &(j, e) in self.rv(i) {
                    if e & 1 == 1 {
                        w[j as usize / 64] |= 1 << (j as usize % 64);
                    }
                }
                w
            })
            .collect();
        // item 14: the bit rows' initialization (rows x cw) and the combination matrix's (rows x rw)
        m.charge(crate::PH_WORD, (rows * cw + rows * rw) as u64)?;
        let mut comb: Vec<Vec<u64>> = (0..rows)
            .map(|i| {
                let mut w = vec![0u64; rw];
                w[i / 64] |= 1 << (i % 64);
                w
            })
            .collect();
        let mut used = vec![false; rows];
        let bit = |w: &Vec<u64>, j: usize| (w[j / 64] >> (j % 64)) & 1 == 1;
        let mut pivots = 0u64;
        for col in 0..f {
            let piv = (0..rows).find(|&r| !used[r] && bit(&mat[r], col));
            let Some(piv) = piv else { continue };
            used[piv] = true;
            pivots += 1;
            let (pm, pc) = (mat[piv].clone(), comb[piv].clone());
            for r in 0..rows {
                if r != piv && bit(&mat[r], col) {
                    for w in 0..cw {
                        mat[r][w] ^= pm[w];
                    }
                    for w in 0..rw {
                        comb[r][w] ^= pc[w];
                    }
                }
            }
        }
        m.charge(crate::PH_WORD, pivots * (cw + rw) as u64)?; // item 14: the per-pivot row clones
        let deps: Vec<Vec<u64>> =
            (0..rows).filter(|&r| mat[r].iter().all(|&w| w == 0)).map(|r| comb[r].clone()).collect();
        m.charge(crate::PH_WORD, (rows * cw + deps.len() * rw) as u64)?; // item 14: the zero-row scan, the copies

        // 7. square root, dependency by dependency
        for dep in &deps {
            let members: Vec<usize> = (0..rows).filter(|&i| bit(dep, i)).collect();
            // item 14: the member scan (rows), ex[] (F), the member sums (their entries), the Y scan (F - 1)
            let nnz: usize = members.iter().map(|&i| rels[i].2 as usize).sum();
            m.charge(crate::PH_WORD, (rows + f + nnz + f - 1) as u64)?;
            let mut x = U256::ZERO;
            for (j, &i) in members.iter().enumerate() {
                let ui = U256::from(rels[i].0.rem_euclid(n_i) as u128);
                if j > 0 {
                    x = x.mul_mod(ui, n);
                    m.charge(SQRT, 1)?;
                } else {
                    x = ui;
                }
            }
            let mut ex = vec![0u64; f];
            for &i in &members {
                for &(j, e) in self.rv(i) {
                    ex[j as usize] += e as u64;
                }
            }
            let mut y: Option<U256> = None;
            for j in 1..f {
                if ex[j] != 0 {
                    let yy = cpow_n(base[j] as u64, ex[j] / 2, n, SQRT, m)?;
                    y = Some(match y {
                        None => yy,
                        Some(prev) => {
                            let z = prev.mul_mod(yy, n);
                            m.charge(SQRT, 1)?;
                            z
                        }
                    });
                }
            }
            let mut y = y.unwrap_or(U256::from(1u64));
            for &i in &members {
                // large primes, squared in each combined relation
                if rels[i].3 != 1 {
                    y = y.mul_mod(U256::from(rels[i].3 as u128), n);
                    m.charge(SQRT, 1)?;
                }
            }
            let (mut aa, mut bb) = ((x + n - y % n) % n, n);
            let mut steps = 0u64;
            while bb != U256::ZERO {
                let t = aa % bb;
                aa = bb;
                bb = t;
                steps += 1;
            }
            m.charge(SQRT, steps)?;
            m.ev(crate::EV_SQRT_GCD, steps); // at["deps"] append
            let ok = aa > U256::from(1u64) && aa < n;
            m.test(ok);
            if ok {
                return Ok(Some(aa));
            }
        }
        Ok(None)
    }
}

/// SIQS relation source on kN: phases 3, 4, 5 and 8 until the ledger is full or the
/// polynomials run out. Some(d) if a factor turns up on the way (a large prime dividing N).
/// a_mode = on_demand: candidate A's formed one at a time, each charged when formed (twin of
/// qs.py's a_on_demand; NOTES.md, second amendment). Prefixes: the (s - 1)-combinations of the
/// pool ordered by closeness to q; a prefix within a used A is skipped ((s - 1) small per used A);
/// otherwise A' (s - 2) and t' (1), then last primes in order of closeness to t': per try a scan
/// of the remaining primes (small), 1 multiply and 1 target check (full: 2 events); a failed
/// check ends the prefix; a passing try costs s small per used A and is accepted if it shares at
/// most s - 2 primes with each.
struct OnDemand {
    pool: Vec<u64>,
    prefixes: Vec<Vec<u64>>,
    at: usize,
    target: f64,
    s: usize,
    used: Vec<Vec<u64>>,
    limit: usize,
    sc: bool,
}

impl OnDemand {
    /// `by_q`: the pool in closeness order, as the pool selection produced it (item 12: no re-sort).
    fn new(pool: &[u64], by_q: &[u64], s: usize, target: f64, sc: bool) -> Self {
        OnDemand { pool: pool.to_vec(), prefixes: combinations(by_q, s - 1), at: 0, target, s,
                   used: Vec::new(), limit: s - 2, sc }
    }

    fn next(&mut self, m: &mut Meter) -> Result<Option<Vec<u64>>, Budget> {
        let s = self.s;
        loop {
            if self.at >= self.prefixes.len() {
                if self.limit == s - 2 {
                    self.limit = s - 1; // pass 2 (third amendment): any A not already used
                    self.at = 0;
                } else {
                    return Ok(None);
                }
            }
            let pre = self.prefixes[self.at].clone();
            self.at += 1;
            if self.limit == s - 2 {
                m.charge(crate::PH_WORD, ((s - 1) * self.used.len()) as u64)?; // prefix-overlap check (audit 1)
                if self.used.iter().any(|u| pre.iter().all(|p| u.contains(p))) {
                    continue;
                }
            }
            let ap: u64 = pre.iter().product();
            m.charge(crate::PH_WORD, s as u64 - 2)?; // word multiplies (audit 3)
            let tp = self.target / ap as f64;
            m.charge(crate::PH_FDIV, 1)?; // a double divide (audit 1)
            let mut rest: Vec<u64> = self.pool.iter().copied().filter(|p| !pre.contains(p)).collect();
            m.charge(crate::PH_WORD, self.pool.len() as u64)?; // building rest: one word op per pool prime (item 13)
            while !rest.is_empty() {
                let mut bi = 0usize;
                for i in 1..rest.len() {
                    let (ki, kb) = ((rest[i] as f64 / tp).ln().abs(), (rest[bi] as f64 / tp).ln().abs());
                    if (ki, rest[i]) < (kb, rest[bi]) {
                        bi = i;
                    }
                }
                m.charge(crate::PH_FLOG, rest.len() as u64)?; // a log per scanned prime (audit 1)
                let last = rest.remove(bi);
                m.charge(crate::PH_WORD, 1)?; // the removal (item 13)
                let a = ap * last;
                m.charge(crate::PH_WORD, 1)?; // A = A' last, a word multiply (audit 3)
                m.charge(crate::PH_FLOG, 1)?; // target check: a log (audit 1)
                if (a as f64 / self.target).log2().abs() > 0.25 {
                    break;
                }
                let mut key = pre.clone();
                key.push(last);
                key.sort();
                if self.sc {
                    m.charge(crate::PH_SORT, sort_cost(s as u64))?; // sort_charge: the key's s primes
                }
                m.charge(crate::PH_WORD, (s * self.used.len()) as u64)?; // overlap compare (audit 1)
                if self.used.iter().any(|u| u.iter().filter(|x| key.contains(x)).count() > self.limit) {
                    continue;
                }
                self.used.push(key.clone());
                return Ok(Some(key));
            }
        }
    }
}

fn sieve_source(num: &Num, g: &Value, k: u64, led: &mut Ledger, m: &mut Meter) -> R {
    let pt_pre = crate::pt_snap(m); // timed region "setup": the attempt's setup before the first A
    let n = num.n;
    let n_i = led.n_i;
    let kn_u = U256::from(k) * n;
    let kn = kn_u.to::<u128>() as i128;
    let (bnd, base, roots_t, f) = (led.bnd, led.base.clone(), led.roots_t.clone(), led.f);
    let pos = |p: u64| base.iter().position(|&b| b == p as i64).unwrap();
    let logp: Vec<i32> = base
        .iter()
        .map(|&p| if p > 2 { ((p as f64).log2().round_ties_even() as i32).max(1) } else { 0 })
        .collect();

    // 3. polynomials: A = product of s primes near (sqrt(2kN)/M)^(1/s)
    let mm_ = ((gene(g, "mc", 4.0) * bnd as f64) as i64).max(64);
    let target = (U256::from(2u64) * kn_u).root(2).to::<u128>() as f64 / mm_ as f64;
    let pool_all: Vec<u64> =
        base[2..].iter().map(|&p| p as u64).filter(|&p| k % p != 0 && p > 2).collect();
    if pool_all.is_empty() {
        return Ok(None);
    }
    // M mod p once per attempt (NOTES.md, "Meter correction: the sieve's start offsets"): one small-modulus
    // op per odd factor-base prime; each start is then r + m_p (- p), one word op per root
    let mp: Vec<i128> = base.iter().map(|&p| if p > 0 { (mm_ as i128).rem_euclid(p as i128) } else { 0 }).collect();
    m.charge(SETUP, (base.len() - 2) as u64)?;
    let mut s = 1usize;
    while target.powf(1.0 / s as f64) > *pool_all.last().unwrap() as f64 && s < 8 {
        s += 1;
    }
    while s > 1 && target.powf(1.0 / s as f64) < pool_all[(pool_all.len() - 1).min(2)] as f64 {
        s -= 1;
    }
    let q = target.powf(1.0 / s as f64);
    let pn = pool_all.len().min(if s == 1 { 40 } else { 16 + 4 * s });
    let mut by_q = pool_all.clone();
    by_q.sort_by(|a, b| {
        ((*a as f64 / q).ln().abs(), *a).partial_cmp(&((*b as f64 / q).ln().abs(), *b)).unwrap()
    });
    let mut pool: Vec<u64> = by_q[..pn].to_vec();
    pool.sort();
    let sc = gene(g, "sort_charge", 0.0) != 0.0;
    if sc {
        // sort_charge: pool selection (n keys + comparisons), then ascending
        let na = pool_all.len() as u64;
        m.charge(crate::PH_FLOG, na)?; // the keys: a log each (audit 2)
        m.charge(crate::PH_SORT, sort_cost(na) + sort_cost(pn as u64))?;
    }
    // a_mode (NOTES.md, "On-demand A selection"): "enumerate" (default) forms and charges every
    // candidate up front; "on_demand" forms them one at a time (OnDemand::next), s >= 2 only.
    let on_demand = g.get("a_mode").and_then(|v| v.as_str()) == Some("on_demand") && s >= 2;
    let mut combos: Vec<Vec<u64>> = Vec::new();
    let mut od: Option<OnDemand> = None;
    if on_demand {
        od = Some(OnDemand::new(&pool, &by_q[..pn], s, target, sc));
    } else {
        combos = combinations(&pool, s);
        m.charge(crate::PH_WORD, (s as u64 - 1) * combos.len() as u64)?; // word multiplies forming each A (audit 3)
        let key = |c: &Vec<u64>| ((c.iter().product::<u64>() as f64 / target).ln()).abs();
        combos.sort_by(|a, b| key(a).partial_cmp(&key(b)).unwrap().then_with(|| a.cmp(b)));
        if sc {
            let c = combos.len() as u64;
            m.charge(crate::PH_FLOG, c)?; // sort_charge: the candidate keys, a log each (audit 2)
            m.charge(crate::PH_SORT, sort_cost(c))?;
        }
    }
    let lc = gene(g, "lc", 1.0).max(1.0).min(3.0); // clamp 3.0 (NOTES.md, "(A2)")
    let lp_on = lc > 1.0; // lc = 1.0: no large-prime work at all
    let l_bound = (bnd as f64).powf(lc); // lc <= 2: a cofactor below it is prime; above, filed the same way
    let thr = (mm_ as f64 * (kn_u.to::<u128>() as f64 / 2.0).sqrt()).log2()
        - (gene(g, "tc", 2.0) + (lc - 1.0)) * (bnd as f64).log2();
    let width = (2 * mm_ + 1) as usize;
    // stage H (NOTES.md, "Stage H: sieve 2 and small prime powers"): gene pp, prime powers q = p^j < 2^pp walked
    // like base primes (odd p with two roots, p not dividing k; 2^j, 4 <= j, only when kN = 1 mod 8), and the
    // prime 2's fixed part w2 added on one parity class by a second threshold at the scan; pp absent or 0: off
    let ppb = gene(g, "pp", 0.0) as u32;
    // per power entry: (q, p, the roots of t^2 = kN mod q, log value, M mod q)
    let mut ppe: Vec<(i64, i64, Vec<i64>, i32, i64)> = Vec::new();
    let mut w2 = 0i32;
    if ppb > 0 {
        let lim = 1i64 << ppb;
        for j in 2..f {
            let p = base[j];
            let t = roots_t[j] as i64;
            if k as i64 % p == 0 || p * p >= lim {
                continue;
            }
            let inv = euclid_inv64((2 * t).rem_euclid(p), p, SETUP, m)?; // (2t)^-1 mod p, for the Hensel lifts
            let (mut q, mut tq) = (p, t);
            while q * p < lim {
                let d = ((tq as i128) * (tq as i128) - kn).rem_euclid((q * p) as i128) as i64; // a multiple of q
                tq += q * (-(d / q) * inv).rem_euclid(p);
                q *= p;
                m.charge(SETUP, 3)?; // kN mod q with the square, times the inverse, the update
                ppe.push((q, p, vec![tq, q - tq], logp[j], mm_.rem_euclid(q)));
                m.charge(SETUP, 1)?; // M mod q
            }
        }
        if kn.rem_euclid(8) == 1 {
            let mut s2 = 1i64;
            let mut jj = 4u32;
            while jj < ppb {
                let q = 1i64 << jj;
                if ((s2 as i128) * (s2 as i128) - kn).rem_euclid(q as i128) != 0 {
                    s2 += 1i64 << (jj - 2);
                }
                m.charge(SETUP, 1)?; // the square and compare
                ppe.push((q, 2, vec![s2, q - s2, (s2 + q / 2) % q, (q - s2 + q / 2) % q], 1, mm_.rem_euclid(q)));
                m.charge(SETUP, 1)?;
                jj += 1;
            }
        }
        w2 = match (kn.rem_euclid(4), kn.rem_euclid(8)) {
            (2, _) | (3, _) => 1,
            (_, 5) => 2,
            _ => 3,
        };
        m.charge(crate::PH_WORD, 2)?; // M mod 2, w2 from kN mod 8
    }
    let chk = gene(g, "check", 0.0) != 0.0; // ledger check: qs's acceptance test only
    let rs_on = g.get("confirm").and_then(|v| v.as_str()) == Some("resieve"); // root-matched confirmation
    // I-029 root confirm (NOTES.md, "Root confirm (I-029) as a card option"): per candidate, a branch-free root test
    // over the sieved base primes (the sieve's start offsets), then v divided only by the hits and the direct primes
    let rt_on = g.get("confirm").and_then(|v| v.as_str()) == Some("root");
    // I-032 option 2'a (NOTES.md, "I-032 option 2'a: start offsets kept by the Gray code"): per A the roots are
    // converted once to sieve-coordinate start offsets; the Gray code then updates the offsets, and every reader
    // takes them directly
    let goff = gene(g, "goff", 0.0) != 0.0;
    let p0 = gene(g, "p0", 30.0) as i128;
    // fix C.2: q -> (u, offset, length) into `parena`; `kept` and `cbuf` are per-attempt scratch for a kept
    // candidate's list and a combination's union
    let (mut parena, mut kept, mut cbuf): (Vec<(u32, u32)>, Vec<(u32, u32)>, Vec<(u32, u32)>) = (Vec::new(), Vec::new(), Vec::new());
    let mut partials: std::collections::HashMap<i128, (i128, u32, u32)> =
        std::collections::HashMap::new();
    let mut arr = vec![0i32; width];
    // step 1 (NOTES.md, "Step 1: delete the fills"): one exponent vector per attempt, reused (F word); with
    // re-sieve, the slot array (width) and the generation stamps (F) once per attempt
    let mut ev = vec![0u32; f];
    // step 1b: per-attempt buffers, cleared per use (no per-candidate allocation; counts unchanged)
    let (mut tt, mut plist, mut out): (Vec<u32>, Vec<usize>, Vec<u32>) = (Vec::new(), Vec::new(), Vec::new());
    // fix C.3: per-attempt buffers for the candidates, re-sieve's record lists and the direct list
    let (mut cand, mut rec, mut direct): (Vec<usize>, Vec<Vec<usize>>, Vec<usize>) = (Vec::new(), Vec::new(), Vec::new());
    let mut slot = vec![usize::MAX; if rs_on { width } else { 0 }];
    let mut stamp = vec![0u32; if rs_on { f } else { 0 }];
    let mut gen = 0u32;
    m.charge(crate::PH_WORD, (f + if rs_on { width + f } else { 0 }) as u64)?;
    // root confirm: each odd base prime's reciprocal for fastmod (a 64-bit divide)
    let recip: Vec<u64> = if rt_on { base.iter().map(|&p| if p > 2 { u64::MAX / p as u64 + 1 } else { 0 }).collect() } else { Vec::new() };
    if rt_on {
        m.charge(SETUP, (f - 2) as u64)?;
    }
    // root confirm, per polynomial: per sieved base prime (p, reciprocal, root 1, root 2, base index), and the hit list
    let (mut tp, mut tm, mut ta, mut tb, mut tj): (Vec<u32>, Vec<u64>, Vec<u32>, Vec<u32>, Vec<u32>) =
        (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new());
    let (mut thit, mut dl): (Vec<usize>, Vec<usize>) = (Vec::new(), Vec::new());
    // 2'b (goff with root confirm; NOTES.md, "I-032 option 2'b"): per A, each sieved prime's first-root index in sr;
    // the root test reads the Gray-kept offsets in place (no per-polynomial pass)
    let mut ka: Vec<usize> = Vec::new();

    let mut next_i = 0usize;
    crate::pt_end(m, 2, pt_pre);
    loop {
        let pt_a = crate::pt_snap(m); // "setup": choosing this A and its per-A roots
        let cur: Vec<u64> = match od.as_mut() {
            Some(o) => match o.next(m)? {
                Some(c) => c,
                None => break,
            },
            None => {
                if next_i >= combos.len() {
                    break;
                }
                next_i += 1;
                combos[next_i - 1].clone()
            }
        };
        let qs_ = &cur;
        let mut aj: Vec<usize> = if rt_on { qs_.iter().map(|&q| pos(q)).collect() } else { Vec::new() }; // root confirm: A's primes, direct
        aj.sort();
        let a: i128 = qs_.iter().map(|&x| x as i128).product();
        let mut bl: Vec<i128> = Vec::with_capacity(s);
        for &ql in qs_ {
            let ql_i = ql as i128;
            let aq = a / ql_i;
            m.charge(SETUP, 1)?;
            let inv = euclid_inv(aq.rem_euclid(ql_i), ql_i, SETUP, m)?;
            let mut gam = (roots_t[pos(ql)] as i128 * inv).rem_euclid(ql_i);
            m.charge(SETUP, 1)?;
            if gam > ql_i / 2 {
                gam = ql_i - gam;
            }
            bl.push(aq * gam);
            m.charge(crate::PH_WORD, 1)?; // a word multiply (audit 4); A/q above stays small-modulus
        }
        // per sieved root, structure of arrays (step 4, NOTES.md "Step 4: gray, a flat layout"): the prime, its base
        // index, the root, and per l the root's 2 B_l A^-1 (one contiguous vector per l); roots of one prime adjacent,
        // in the order (r1, r2), so every loop visits them as before
        let (mut sp, mut sj, mut sr): (Vec<i32>, Vec<usize>, Vec<i32>) = (Vec::new(), Vec::new(), Vec::new());
        let mut sbi: Vec<Vec<i32>> = vec![Vec::new(); s]; // primes < 2^31: roots and inverses fit in i32
        let mut n_st = 0usize; // sieved primes
        let mut bv: i128 = bl.iter().sum();
        // fix C.1: the per-prime arithmetic in i64 (A < 2^62, p < 2^30, B_l < A; results identical to i128)
        assert!(a < (1i128 << 62) && bv.abs() < (1i128 << 62), "A or B too large for the i64 setup arithmetic");
        let (a64, bv64) = (a as i64, bv as i64);
        let bl64: Vec<i64> = bl.iter().map(|&b| b as i64).collect();
        for j in 2..f {
            let p = base[j] as i64;
            let ar = a64.rem_euclid(p);
            if ar == 0 || p == 2 {
                continue;
            }
            let ainv = euclid_inv64(ar, p, SETUP, m)?;
            let t = roots_t[j] as i64;
            let r1 = (ainv * (t - bv64).rem_euclid(p)).rem_euclid(p);
            m.charge(SETUP, 1)?;
            let r2 = (ainv * (-t - bv64).rem_euclid(p)).rem_euclid(p);
            m.charge(SETUP, 1)?;
            let mut bainv = Vec::with_capacity(s);
            for &b in &bl64 {
                bainv.push(((2 * b).rem_euclid(p) * ainv).rem_euclid(p));
                m.charge(SETUP, 1)?;
            }
            n_st += 1;
            for r in if t == 0 { vec![r1] } else { vec![r1, r2] } {
                assert!(p < 1 << 30, "factor-base prime too large for the i32 root arrays");
                sp.push(p as i32);
                sj.push(j);
                sr.push(r as i32);
                for l in 0..s {
                    sbi[l].push(bainv[l] as i32);
                }
            }
        }
        // stage H: the power entries, structure of arrays like the base roots (modulus, root, log, M mod q, 2 B_l A^-1)
        let (mut qp, mut qr, mut ql_, mut qm): (Vec<i64>, Vec<i64>, Vec<i32>, Vec<i64>) = (Vec::new(), Vec::new(), Vec::new(), Vec::new());
        let mut qbi: Vec<Vec<i64>> = vec![Vec::new(); s];
        let mut par = usize::MAX;
        if ppb > 0 {
            for (q, p, ts, lv, mq) in &ppe {
                let (q, p) = (*q, *p);
                if a64.rem_euclid(p) == 0 {
                    continue;
                }
                let ar = a64.rem_euclid(q);
                m.charge(SETUP, 1)?;
                let ainv = euclid_inv64(ar, q, SETUP, m)?;
                let rts: Vec<i64> = ts.iter().map(|&t| (ainv * (t - bv64).rem_euclid(q)).rem_euclid(q)).collect();
                m.charge(SETUP, ts.len() as u64)?;
                let mut bainv = Vec::with_capacity(s);
                for &b in &bl64 {
                    bainv.push(((2 * b).rem_euclid(q) * ainv).rem_euclid(q));
                    m.charge(SETUP, 1)?;
                }
                for &r in &rts {
                    qp.push(q);
                    qr.push(r);
                    ql_.push(*lv);
                    qm.push(*mq);
                    for l in 0..s {
                        qbi[l].push(bainv[l]);
                    }
                }
            }
            par = (bv64 + mm_ + kn.rem_euclid(2) as i64).rem_euclid(2) as usize; // the parity class whose threshold is T - w2
            m.charge(crate::PH_WORD, 1)?;
        }
        if goff {
            // 2'a: each root to its start offset s0 = r + M mod p (less p), once per A, one word op per root
            for k in 0..sr.len() {
                let (p, j) = (sp[k], sj[k]);
                let s0 = sr[k] + mp[j] as i32;
                sr[k] = if s0 >= p { s0 - p } else { s0 };
            }
            for t in 0..qr.len() {
                let s0 = qr[t] + qm[t];
                qr[t] = if s0 >= qp[t] { s0 - qp[t] } else { s0 };
            }
            m.charge(crate::PH_WORD, (sr.len() + qr.len()) as u64)?;
            if rt_on {
                // 2'b: per sieved prime its first root's index and its reciprocal, two word ops per prime; its last
                // root is the next prime's first less one (or sr's end), p and the base index are read through sp / sj
                ka.clear();
                tm.clear();
                for k in 0..sr.len() {
                    if k == 0 || sj[k] != sj[k - 1] {
                        ka.push(k);
                        tm.push(recip[sj[k]]);
                    }
                }
                m.charge(crate::PH_WORD, 2 * ka.len() as u64)?;
            }
        }
        crate::pt_end(m, 2, pt_a);
        let mut signs = vec![1i128; s];
        for i in 0..(1usize << (s - 1)) {
            let pt = crate::pt_snap(m); // "gray"
            if i != 0 {
                // Gray code: flip one B_l, update every root
                let v = i.trailing_zeros() as usize + 1;
                let d = signs[v];
                signs[v] = -d;
                bv -= 2 * d * bl[v];
                let n_roots = (sr.len() + qr.len()) as u64;
                let bi = &sbi[v];
                // r, bi in [0, p): one add or subtract and one conditional correction, no reduction
                if d > 0 {
                    for ((r, &b), &p) in sr.iter_mut().zip(bi.iter()).zip(sp.iter()) {
                        let x = *r + b;
                        *r = if x >= p { x - p } else { x };
                    }
                    for ((r, &b), &q) in qr.iter_mut().zip(qbi[v].iter()).zip(qp.iter()) {
                        let x = *r + b;
                        *r = if x >= q { x - q } else { x };
                    }
                } else {
                    for ((r, &b), &q) in qr.iter_mut().zip(qbi[v].iter()).zip(qp.iter()) {
                        let x = *r - b;
                        *r = if x < 0 { x + q } else { x };
                    }
                    for ((r, &b), &p) in sr.iter_mut().zip(bi.iter()).zip(sp.iter()) {
                        let x = *r - b;
                        *r = if x < 0 { x + p } else { x };
                    }
                }
                m.charge(crate::PH_GRAY, n_roots)?; // word-level type setup_gray
            }
            crate::pt_end(m, 3, pt);
            let c = (bv * bv - kn) / a;
            let pt = crate::pt_snap(m); // "sieve"
            // 4. sieve
            let ps = crate::pt_snap_sv(m); // "sv:zero"
            arr.iter_mut().for_each(|x| *x = 0);
            crate::pt_end(m, 14, ps);
            crate::sv_units(0, width as u64); // the width charge
            if par != usize::MAX {
                let ps = crate::pt_snap_sv(m); // "sv:free2"
                // stage H: the free 2 by initialisation (the scan fix); its writes charged below, one sieve_scan per cell
                for x in arr[par..].iter_mut().step_by(2) {
                    *x = w2;
                }
                crate::pt_end(m, 15, ps);
            }
            let ps = crate::pt_snap_sv(m); // "sv:prime"
            let mut upd = 0u64;
            let mut nr = 0u64; // start offsets, one word op per root
            for k in 0..sr.len() {
                let (p, j) = (sp[k] as i128, sj[k]);
                let pu = p as usize;
                let s0 = if goff {
                    sr[k] as i128 // 2'a: the kept offset
                } else {
                    let mut s0 = sr[k] as i128 + mp[j];
                    if s0 >= p {
                        s0 -= p;
                    }
                    nr += 1;
                    s0
                };
                let start = s0 as usize;
                let mut i0 = start;
                while i0 < width {
                    arr[i0] += logp[j];
                    i0 += pu;
                }
                // a prime wider than the interval may start past its end: no steps,
                // as Python's (width - 1 - start) // p + 1 = 0 (usize would wrap)
                if start < width {
                    upd += ((width - 1 - start) / pu + 1) as u64;
                }
            }
            crate::pt_end(m, 16, ps);
            crate::sv_units(2, upd + nr);
            let (upd_p, nr_p) = (upd, nr);
            let ps = crate::pt_snap_sv(m); // "sv:power"
            for t in 0..qr.len() {
                let q = qp[t];
                let s0 = if goff {
                    qr[t]
                } else {
                    let mut s0 = qr[t] + qm[t];
                    if s0 >= q {
                        s0 -= q;
                    }
                    nr += 1;
                    s0
                };
                let (start, qu) = (s0 as usize, q as usize);
                let mut i0 = start;
                while i0 < width {
                    arr[i0] += ql_[t];
                    i0 += qu;
                }
                if start < width {
                    upd += ((width - 1 - start) / qu + 1) as u64;
                }
            }
            crate::pt_end(m, 17, ps);
            crate::sv_units(3, (upd - upd_p) + (nr - nr_p));
            let ps = crate::pt_snap_sv(m); // "sv:tail"
            m.charge(crate::PH_WORD, nr)?;
            m.charge(SIEVE, upd)?;
            m.charge(SIEVE, width as u64)?;
            // meter correction (NOTES.md, "Meter correction (proposed; ...): pp's free-2 initialisation is uncharged"):
            // the free 2's writes, one sieve_scan per cell written, ceil((width - par) / 2)
            let f2 = if par != usize::MAX { ((width - par + 1) / 2) as u64 } else { 0 };
            if f2 > 0 {
                m.charge(SIEVE, f2)?;
                crate::sv_units(1, f2);
            }
            if rt_on && !goff {
                // the sieved roots' start offsets stored, one word per root (roots of one prime adjacent, ascending base order)
                tp.clear();
                tm.clear();
                ta.clear();
                tb.clear();
                tj.clear();
                for k in 0..sr.len() {
                    let (p, j) = (sp[k] as i64, sj[k]);
                    let mut s0 = sr[k] as i64 + mp[j] as i64;
                    if s0 >= p {
                        s0 -= p;
                    }
                    if tj.last() == Some(&(j as u32)) {
                        *tb.last_mut().unwrap() = s0 as u32;
                    } else {
                        tp.push(p as u32);
                        tm.push(recip[j]);
                        ta.push(s0 as u32);
                        tb.push(s0 as u32);
                        tj.push(j as u32);
                    }
                }
                m.charge(crate::PH_WORD, sr.len() as u64)?;
                crate::sv_units(4, sr.len() as u64);
            }
            m.ev(crate::EV_SIEVE_SCAN, width as u64 + f2); // at["polys"] append (the width and the free 2's writes)
            crate::pt_end(m, 18, ps);
            crate::pt_end(m, 4, pt);
            let pt = crate::pt_snap(m); // "scan"
            cand.clear();
            cand.extend((0..width).filter(|&i0| (arr[i0] as f64) >= thr));
            crate::pt_end(m, 5, pt);
            let pt = crate::pt_snap(m); // "resieve"
            // re-sieve (NOTES.md, "Root-matched candidate confirmation"): primes >= p0 matched over a
            // candidate bitmap; v divided only by the matched primes and the direct ones
            if rs_on {
                for (k, &i0) in cand.iter().enumerate() {
                    slot[i0] = k;
                }
                if rec.len() < cand.len() {
                    rec.resize_with(cand.len(), Vec::new);
                }
                for r in rec.iter_mut().take(cand.len()) {
                    r.clear();
                }
                let (mut walk, mut nhit) = (0u64, 0u64);
                gen += 1;
                for k in 0..sr.len() {
                    let (p, j) = (sp[k] as i128, sj[k]);
                    stamp[j] = gen;
                    if p < p0 {
                        continue;
                    }
                    let pu = p as usize;
                    {
                        let r = sr[k] as i128;
                        let s0 = if goff {
                            r // 2'a: the kept offset, no add
                        } else {
                            let mut s0 = r + mp[j];
                            if s0 >= p {
                                s0 -= p;
                            }
                            walk += 1; // the start offset, one word op per root walked
                            s0
                        };
                        let start = s0 as usize;
                        if start >= width {
                            continue;
                        }
                        walk += 2 * ((width - 1 - start) / pu + 1) as u64; // index step + bitmap test
                        let mut i0 = start;
                        while i0 < width {
                            if slot[i0] != usize::MAX {
                                rec[slot[i0]].push(j);
                                nhit += 1;
                            }
                            i0 += pu;
                        }
                    }
                }
                m.charge(crate::PH_WORD, cand.len() as u64 + walk + nhit)?;
                for &i0 in &cand {
                    slot[i0] = usize::MAX; // cleared after the walk, only the set slots
                }
                direct.clear();
                direct.extend((1..f).filter(|&j| (base[j] as i128) < p0 || stamp[j] != gen));
                // per polynomial: the slots cleared (|cand|), the generation stamps written (|st|), the direct
                // list's pass (F - 1), the record lists (|cand|)
                m.charge(crate::PH_WORD, (2 * cand.len() + n_st + f - 1) as u64)?;
            }
            crate::pt_end(m, 6, pt);
            // 5. confirm
            for (ci, &i0) in cand.iter().enumerate() {
                let pt = crate::pt_snap(m); // "confirm"
                let x = i0 as i128 - mm_ as i128;
                let mut v = (a * x + 2 * bv) * x + c;
                m.charge(crate::PH_WORD, 2)?; // two word multiply-adds (audit 5)
                plist.clear();
                if rs_on {
                    // merge two ascending lists, |plist| word ops (NOTES.md, item 11)
                    let (a_, b_) = (&direct, &rec[ci]);
                    let (mut i, mut j) = (0usize, 0usize);
                    while i < a_.len() && j < b_.len() {
                        if a_[i] < b_[j] {
                            plist.push(a_[i]);
                            i += 1;
                        } else {
                            plist.push(b_[j]);
                            j += 1;
                        }
                    }
                    plist.extend_from_slice(&a_[i..]);
                    plist.extend_from_slice(&b_[j..]);
                    m.charge(crate::PH_WORD, plist.len() as u64)?;
                } // else: the full pass iterates 1..f directly (no list is built, as in Python)
                m.charge(crate::PH_WORD, 1)?; // the sign check (audit 8)
                if rt_on {
                    m.charge(crate::PH_ROOT, if goff { ka.len() } else { tp.len() } as u64)?; // the root test, one per sieved base prime
                } else {
                    m.charge(CONFIRM, if rs_on { plist.len() as u64 } else { f as u64 - 1 })?;
                }
                tt.clear(); // entries touched in the reused vector (step 1)
                if v < 0 {
                    ev[0] = 1;
                    tt.push(0);
                    v = -v;
                }
                if v == 0 {
                    m.charge(crate::PH_WORD, 2 * tt.len() as u64)?; // sets + clear
                    for &j in &tt {
                        ev[j as usize] = 0;
                    }
                    m.test(false);
                    continue;
                }
                if rt_on {
                    // branch-free root test (the benchmark's version (c)): i0 mod p by the reciprocal when i0 >= p
                    let n = if goff { ka.len() } else { tp.len() };
                    thit.resize(n + 1, 0);
                    let mut cnt = 0usize;
                    let x0 = i0 as u32;
                    if goff {
                        // 2'b: the offsets read in place from sr through ka
                        for t in 0..n {
                            let k = ka[t];
                            let last = if t + 1 < n { ka[t + 1] - 1 } else { sr.len() - 1 };
                            let p = sp[k] as u32;
                            let fm = (((tm[t].wrapping_mul(x0 as u64)) as u128 * p as u128) >> 64) as u32;
                            let r = if x0 < p { x0 } else { fm };
                            thit[cnt] = sj[k];
                            cnt += ((r == sr[k] as u32) | (r == sr[last] as u32)) as usize;
                        }
                    } else {
                        for t in 0..n {
                            let p = tp[t];
                            let fm = (((tm[t].wrapping_mul(x0 as u64)) as u128 * p as u128) >> 64) as u32;
                            let r = if x0 < p { x0 } else { fm };
                            thit[cnt] = tj[t] as usize;
                            cnt += ((r == ta[t]) | (r == tb[t])) as usize;
                        }
                    }
                    m.charge(crate::PH_WORD, 1)?; // the prime 2's low-bit test
                    let even = v & 1 == 0;
                    dl.clear();
                    if even {
                        dl.push(1);
                    }
                    for &j in &aj {
                        m.charge(CONFIRM, 1)?; // A's primes, v mod p
                        if v % base[j] as i128 == 0 {
                            dl.push(j);
                        }
                    }
                    m.charge(CONFIRM, (cnt + even as usize) as u64)?; // the first division by each hit and an even v
                    plist.clear();
                    let (a_, b_) = (&dl, &thit[..cnt]);
                    let (mut i, mut j) = (0usize, 0usize);
                    while i < a_.len() && j < b_.len() {
                        if a_[i] < b_[j] {
                            plist.push(a_[i]);
                            i += 1;
                        } else {
                            plist.push(b_[j]);
                            j += 1;
                        }
                    }
                    plist.extend_from_slice(&a_[i..]);
                    plist.extend_from_slice(&b_[j..]);
                    m.charge(crate::PH_WORD, plist.len() as u64)?;
                }
                let n_pl = if rs_on || rt_on { plist.len() } else { f - 1 };
                for t in 0..n_pl {
                    let j = if rs_on || rt_on { plist[t] } else { t + 1 };
                    let p = base[j] as i128;
                    if v % p == 0 {
                        v /= p;
                        ev[j] += 1;
                        tt.push(j as u32);
                        while v % p == 0 {
                            v /= p;
                            ev[j] += 1;
                            m.charge(CONFIRM, 1)?;
                        }
                    }
                }
                crate::pt_end(m, 7, pt);
                let pt = crate::pt_snap(m); // "lp_ledger": large primes and the ledger
                let smooth = v == 1;
                let mut partial = false;
                if lp_on && !smooth {
                    // 8. large primes
                    m.charge(crate::PH_WORD, 1)?; // bound check (audit 6)
                    partial = (v as f64) < l_bound; // exact: L < 2^53, and v > 2^53 rounds above it
                }
                m.test(smooth || partial);
                if !(smooth || partial) {
                    m.charge(crate::PH_WORD, 2 * tt.len() as u64)?; // sets + clear
                    for &j in &tt {
                        ev[j as usize] = 0;
                    }
                    crate::pt_end(m, 8, pt);
                    continue;
                }
                let u = a * x + bv;
                let ptl = crate::pt_snap_lp(m); // "lp:copy"
                let nt = tt.len();
                for &ql in qs_ {
                    // the A-primes (uncharged until item 15)
                    let j = pos(ql);
                    if ev[j] == 0 {
                        tt.push(j as u32);
                    }
                    ev[j] += 1;
                }
                kept.clear();
                kept.extend(tt.iter().map(|&j| (j, ev[j as usize]))); // the sparse relation
                let vec_ = &kept;
                m.charge(crate::PH_WORD, (nt + 2 * tt.len() + qs_.len()) as u64)?; // sets, the sparse copy, the clear; item 15: the A-prime adds
                for &j in &tt {
                    ev[j as usize] = 0;
                }
                crate::pt_end(m, 10, ptl);
                if smooth {
                    let ptl = crate::pt_snap_lp(m); // "lp:add"
                    let full = led.add(u, vec_, 1, chk, m)?;
                    crate::pt_end(m, 13, ptl);
                    if full {
                        crate::pt_end(m, 8, pt); // the region closed on the early return too (instrumentation)
                        return Ok(None);
                    }
                    crate::pt_end(m, 8, pt);
                    continue;
                }
                m.charge(LP, 1)?; // N mod q
                if n_i % v == 0 {
                    crate::pt_end(m, 8, pt);
                    return Ok(Some(U256::from(v as u128)));
                }
                let ptl = crate::pt_snap_lp(m); // "lp:hash"
                m.charge(crate::PH_HASH, 1)?; // hash lookup (audit 6)
                let Some(&(u1, o1, l1)) = partials.get(&v) else {
                    m.charge(crate::PH_HASH, 1)?; // insert (audit 6)
                    let off = parena.len() as u32;
                    parena.extend_from_slice(vec_);
                    partials.insert(v, (u, off, vec_.len() as u32));
                    crate::pt_end(m, 11, ptl);
                    crate::pt_end(m, 8, pt);
                    continue;
                };
                crate::pt_end(m, 11, ptl);
                let ptl = crate::pt_snap_lp(m); // "lp:comb"
                let cu = U256::from(u1.rem_euclid(n_i) as u128)
                    .mul_mod(U256::from(u.rem_euclid(n_i) as u128), n)
                    .to::<u128>() as i128;
                m.charge(LP, 1)?;
                // sparse combination through the clean vector (step 1)
                out.clear();
                let v1 = &parena[o1 as usize..(o1 + l1) as usize];
                for &(j, e) in v1.iter().chain(vec_.iter()) {
                    if ev[j as usize] == 0 {
                        out.push(j);
                    }
                    ev[j as usize] += e;
                }
                cbuf.clear();
                cbuf.extend(out.iter().map(|&j| (j, ev[j as usize])));
                for &j in &out {
                    ev[j as usize] = 0;
                }
                m.charge(crate::PH_WORD, (v1.len() + vec_.len() + 2 * out.len()) as u64)?;
                m.ev(crate::EV_LP_FULL, 1); // at["lp"]["combos"] += 1
                crate::pt_end(m, 12, ptl);
                let ptl = crate::pt_snap_lp(m); // "lp:add"
                let full = led.add(cu, &cbuf, v, chk, m)?;
                crate::pt_end(m, 13, ptl);
                if full {
                    crate::pt_end(m, 8, pt);
                    return Ok(None);
                }
                crate::pt_end(m, 8, pt);
            }
        }
    }
    Ok(None)
}
