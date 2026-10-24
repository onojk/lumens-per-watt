//! Continued-fraction card ("cfrac"): a line-by-line port of evolve/cfrac.py, a second
//! relation source into qs.rs's Ledger (one k, one factor base), with every charge made at
//! the same point and in the same chunk as the Python (checked by parity.py). Cost model:
//! NOTES.md, "CFRAC as a second relation source".

use super::qs::{gene, Ledger, MULT};
use super::{ks_score, Budget, Meter, Num, KS_PRIMES, R};
use ruint::aliases::U256;
use serde_json::Value;

pub const CF_STEP: usize = 9; // isqrt, then 4 ops per step
pub const CF_TD: usize = 10; // trial division of every residue

pub fn lamp_cfrac(num: &Num, g: &Value, m: &mut Meter) -> R {
    let n = num.n;
    if n % U256::from(2u64) == U256::ZERO {
        return Ok(Some(U256::from(2u64)));
    }
    if n >= U256::from(1u128 << 100) {
        eprintln!("lampcore: cfrac supports N < 2^100, got a {}-bit N", n.bit_len());
        std::process::exit(2);
    }
    // 1. multiplier
    let kc = (gene(g, "kc", 16.0) as u64).max(1);
    m.charge(MULT, kc * KS_PRIMES.len() as u64)?;
    let mut ranked: Vec<(u64, f64)> = (1..=kc).map(|k| (k, -ks_score(k, num))).collect();
    ranked.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap().then(a.0.cmp(&b.0)));
    let ln_n = num.f.ln();
    let bnd = ((gene(g, "bc", 1.5) * (0.5 * (ln_n * ln_n.ln()).sqrt()).exp()) as u64).max(30);
    for (k, _) in ranked {
        let mut led = match Ledger::build(num, k, bnd, m)? {
            Ok(led) => led,
            Err(p) => return Ok(Some(p)), // p divides N
        };
        cf_source(num, g, k, &mut led, m)?;
        if led.full() {
            if let Some(d) = led.solve(m)? {
                return Ok(Some(d));
            }
        }
    }
    Ok(None)
}

/// CFRAC relation source on kN until the ledger is full or the period ends (Q = 1).
fn cf_source(num: &Num, g: &Value, k: u64, led: &mut Ledger, m: &mut Meter) -> Result<(), Budget> {
    let n = num.n;
    let kn_u = U256::from(k) * n;
    let chk = gene(g, "check", 0.0) != 0.0;
    m.charge(CF_STEP, kn_u.bit_len() as u64)?; // g = isqrt(kN)
    let g0 = kn_u.root(2);
    if g0 * g0 == kn_u {
        return Ok(()); // Q_1 = 0: no expansion
    }
    let kn = kn_u.to::<u128>() as i128;
    let g0i = g0.to::<u128>() as i128;
    let (base, f) = (led.base.clone(), led.f);
    let (mut p, mut q, mut qp, mut a) = (0i128, 1i128, kn, g0i);
    let (mut aa, mut ap) = (g0 % n, U256::from(1u64));
    let mut i = 0u64;
    loop {
        m.charge(CF_STEP, 4)?;
        let p1 = a * q - p;
        let q1 = qp + a * (p - p1);
        let a1 = (g0i + p1) / q1;
        let an = (U256::from(a1 as u128).mul_mod(aa, n) + ap) % n;
        if q1 == 1 {
            return Ok(()); // end of the period: the relations repeat
        }
        // residue: A^2 = (-1)^(i+1) Q1 (mod N)
        m.charge(CF_TD, f as u64)?;
        let mut vec_ = vec![0u32; f];
        vec_[0] = ((i + 1) & 1) as u32;
        let mut v = q1;
        for j in 1..f {
            let pj = base[j] as i128;
            if v % pj == 0 {
                v /= pj;
                vec_[j] += 1;
                while v % pj == 0 {
                    v /= pj;
                    vec_[j] += 1;
                    m.charge(CF_TD, 1)?;
                }
            }
        }
        m.test(v == 1);
        if v == 1 && led.add(aa.to::<u128>() as i128, vec_, 1, chk, m)? {
            return Ok(());
        }
        p = p1;
        qp = q;
        q = q1;
        a = a1;
        ap = aa;
        aa = an;
        i += 1;
    }
}
