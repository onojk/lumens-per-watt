//! Elliptic-curve card ("ecm"): a line-by-line port of evolve/ecm.py, every charge made at
//! the same point and in the same chunk as the Python (checked by parity.py). Cost model:
//! NOTES.md, "Stage 8: elliptic-curve card". 1 op per modular multiply or squaring.

use super::qs::{gene, primes_upto};
use super::{Budget, Meter, Num, R};
use ruint::aliases::U256;
use serde_json::Value;

pub const ECM_SETUP: usize = 11;
pub const ECM_S1: usize = 12;
pub const ECM_S2: usize = 13;
pub const ECM_GCD: usize = 14;

const W: u64 = 210;

type Pt = (U256, U256);

struct Ctx {
    n: U256,
    a24: U256,
}

impl Ctx {
    fn mul(&self, a: U256, b: U256) -> U256 {
        a.mul_mod(b, self.n)
    }
    fn add(&self, a: U256, b: U256) -> U256 {
        a.add_mod(b, self.n)
    }
    fn sub(&self, a: U256, b: U256) -> U256 {
        (a + self.n - b) % self.n
    }

    fn xdbl(&self, (x, z): Pt, ph: usize, m: &mut Meter) -> Result<Pt, Budget> {
        m.charge(crate::PH_WORD, 4)?; // X + Z, X - Z, t1 - t2, t2 + e (NOTES.md, "ECM modular additions")
        let s = self.add(x, z);
        let t1 = self.mul(s, s);
        m.charge(ph, 1)?;
        let d = self.sub(x, z);
        let t2 = self.mul(d, d);
        m.charge(ph, 1)?;
        let x2 = self.mul(t1, t2);
        m.charge(ph, 1)?;
        let t3 = self.sub(t1, t2);
        let e = self.mul(self.a24, t3);
        m.charge(ph, 1)?;
        let z2 = self.mul(t3, self.add(t2, e));
        m.charge(ph, 1)?;
        Ok((x2, z2))
    }

    fn xadd(&self, (xp, zp): Pt, (xq, zq): Pt, (xd, zd): Pt, ph: usize, m: &mut Meter) -> Result<Pt, Budget> {
        m.charge(crate::PH_WORD, 6)?; // XP - ZP, XQ + ZQ, XP + ZP, XQ - ZQ, uu + vv, uu - vv
        let uu = self.mul(self.sub(xp, zp), self.add(xq, zq));
        m.charge(ph, 1)?;
        let vv = self.mul(self.add(xp, zp), self.sub(xq, zq));
        m.charge(ph, 1)?;
        let a = self.add(uu, vv);
        let sa = self.mul(a, a);
        m.charge(ph, 1)?;
        let b = self.sub(uu, vv);
        let sb = self.mul(b, b);
        m.charge(ph, 1)?;
        let x3 = self.mul(zd, sa);
        m.charge(ph, 1)?;
        let z3 = self.mul(xd, sb);
        m.charge(ph, 1)?;
        Ok((x3, z3))
    }

    /// (kP, (k+1)P) for k >= 1: R0 = P, R1 = 2P, then xADD + xDBL per bit below the top.
    fn ladder(&self, k: u64, p: Pt, ph: usize, m: &mut Meter) -> Result<(Pt, Pt), Budget> {
        let (mut r0, mut r1) = (p, self.xdbl(p, ph, m)?);
        let bl = 64 - k.leading_zeros();
        for i in (0..bl.saturating_sub(1)).rev() {
            if (k >> i) & 1 == 1 {
                r0 = self.xadd(r0, r1, p, ph, m)?;
                r1 = self.xdbl(r1, ph, m)?;
            } else {
                r1 = self.xadd(r0, r1, p, ph, m)?;
                r0 = self.xdbl(r0, ph, m)?;
            }
        }
        Ok((r0, r1))
    }
}

/// B1 and B2 exactly as ecm.py's bounds().
fn bounds(num: &Num, g: &Value) -> (u64, u64) {
    let s = num.n.root(2).to::<u128>() as f64;
    let ls = s.ln();
    let b1 = ((gene(g, "b1", 1.0) * ((ls * ls.ln()).sqrt() / 2f64.sqrt()).exp()) as u64).max(10);
    (b1, (gene(g, "b2", 50.0) * b1 as f64) as u64)
}

pub fn lamp_ecm(num: &Num, g: &Value, m: &mut Meter) -> R {
    let n = num.n;
    if n % U256::from(2u64) == U256::ZERO {
        return Ok(Some(U256::from(2u64)));
    }
    if n >= U256::from(1u128 << 100) {
        eprintln!("lampcore: ecm supports N < 2^100, got a {}-bit N", n.bit_len());
        std::process::exit(2);
    }
    let n_i = n.to::<u128>() as i128;
    let (b1, b2) = bounds(num, g);
    let primes = primes_upto(b1.max(b2));
    let mut pp: Vec<u64> = Vec::new();
    for &p in &primes {
        if p > b1 {
            break;
        }
        let mut q = p;
        while q * p <= b1 {
            q *= p;
        }
        pp.push(q);
    }
    let stage2 = b2 > b1;
    let mut isprime = vec![false; if stage2 { b2 as usize + 1 } else { 0 }];
    if stage2 {
        for &p in &primes {
            isprime[p as usize] = true;
        }
    }
    let baby: Vec<u64> = (1..W / 2).step_by(2).filter(|b| gcd_u64(*b, W) == 1).collect();
    let curves = (gene(g, "curves", 10000.0) as i64).max(1);
    let s0 = gene(g, "s0", 6.0) as i64;
    let mut ctx = Ctx { n, a24: U256::ZERO };
    let c4 = |x: U256| x % n;

    for i in 0..curves {
        let sigma = U256::from((s0 + i) as u64) % n;
        // setup: Suyama, u = sigma^2 - 5, v = 4 sigma, P = (u^3 : v^3)
        let s_sq = ctx.mul(sigma, sigma);
        m.charge(ECM_SETUP, 1)?;
        let u = ctx.sub(s_sq, c4(U256::from(5u64)));
        m.charge(crate::PH_WORD, 1)?;
        let v = ctx.mul(U256::from(4u64) % n, sigma); // a small constant: word-level, as in ecm.py
        m.charge(crate::PH_WORD, 1)?;
        let u2 = ctx.mul(u, u);
        m.charge(ECM_SETUP, 1)?;
        let u3 = ctx.mul(u2, u);
        m.charge(ECM_SETUP, 1)?;
        let v2 = ctx.mul(v, v);
        m.charge(ECM_SETUP, 1)?;
        let v3 = ctx.mul(v2, v);
        m.charge(ECM_SETUP, 1)?;
        let t = ctx.sub(v, u);
        m.charge(crate::PH_WORD, 1)?;
        let t2 = ctx.mul(t, t);
        m.charge(ECM_SETUP, 1)?;
        let t3 = ctx.mul(t2, t);
        m.charge(ECM_SETUP, 1)?;
        let three_u_v = ctx.add(ctx.add(ctx.add(u, u), u), v);
        m.charge(crate::PH_WORD, 2)?; // 3u, 3u + v
        let num_ = ctx.mul(t3, three_u_v);
        m.charge(ECM_SETUP, 1)?;
        let den = ctx.mul(u3, v);
        m.charge(ECM_SETUP, 1)?;
        let den = ctx.mul(U256::from(16u64) % n, den);
        m.charge(ECM_SETUP, 1)?;
        // extended Euclid for den^-1 mod N, 1 op per division step (one chunk)
        let (mut r0, mut r1, mut sa, mut sb, mut steps) = (n_i, den.to::<u128>() as i128, 0i128, 1i128, 0u64);
        while r1 != 0 {
            let qq = r0 / r1;
            let (nr, ns) = (r0 - qq * r1, sa - qq * sb);
            r0 = r1;
            r1 = nr;
            sa = sb;
            sb = ns;
            steps += 1;
        }
        m.charge(ECM_SETUP, steps)?;
        m.ev(crate::EV_ECM_EUCLID, steps); // per-type: this curve's setup Euclid steps
        if r0 != 1 {
            if r0 < n_i {
                m.test(true);
                return Ok(Some(U256::from(r0 as u128)));
            }
            m.test(false); // degenerate
            continue;
        }
        ctx.a24 = ctx.mul(num_, U256::from(sa.rem_euclid(n_i) as u128));
        m.charge(ECM_SETUP, 1)?;

        // stage 1
        let mut pt: Pt = (u3, v3);
        for &q in &pp {
            pt = ctx.ladder(q, pt, ECM_S1, m)?.0;
        }
        let d = pt.1.gcd(n);
        m.charge(ECM_GCD, 1)?;
        if d > U256::from(1u64) && d < n {
            m.test(true);
            return Ok(Some(d));
        }
        if d == n || !stage2 {
            m.test(false);
            continue;
        }

        // stage 2: baby steps bQ (odd b < w/2), giant steps j W, j0 = max(1, B1 // w)
        let q0 = pt;
        let d2 = ctx.xdbl(q0, ECM_S2, m)?;
        let mut bq: Vec<Pt> = vec![(U256::ZERO, U256::ZERO); (W / 2) as usize];
        bq[1] = q0;
        bq[3] = ctx.xadd(q0, d2, q0, ECM_S2, m)?;
        let mut b = 5usize;
        while b < (W / 2) as usize {
            bq[b] = ctx.xadd(bq[b - 2], d2, bq[b - 4], ECM_S2, m)?;
            b += 2;
        }
        let wp = ctx.ladder(W, q0, ECM_S2, m)?.0;
        let (j0, jmax) = ((b1 / W).max(1), (b2 + W - 1) / W);
        let (mut s, mut s1) = ctx.ladder(j0, wp, ECM_S2, m)?;
        let mut acc = U256::from(1u64) % n;
        for j in j0..=jmax {
            for &bb in &baby {
                let (q1, q2) = (j * W + bb, j * W - bb);
                m.charge(crate::PH_WORD, 2)?; // the two indices
                m.charge(crate::PH_WORD, 2)?; // the two prime-table tests
                let hit = |x: u64| b1 < x && x <= b2 && isprime[x as usize];
                if hit(q1) || hit(q2) {
                    let (xb, zb) = bq[bb as usize];
                    let p1 = ctx.mul(s.0, zb);
                    m.charge(ECM_S2, 1)?;
                    let p2 = ctx.mul(xb, s.1);
                    m.charge(ECM_S2, 1)?;
                    m.charge(crate::PH_WORD, 1)?; // p1 - p2
                    acc = ctx.mul(acc, ctx.sub(p1, p2));
                    m.charge(ECM_S2, 1)?;
                }
            }
            if j < jmax {
                let next = ctx.xadd(s1, wp, s, ECM_S2, m)?;
                s = s1;
                s1 = next;
            }
        }
        let d = acc.gcd(n);
        m.charge(ECM_GCD, 1)?;
        if d > U256::from(1u64) && d < n {
            m.test(true);
            return Ok(Some(d));
        }
        m.test(false);
    }
    Ok(None)
}

fn gcd_u64(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}
