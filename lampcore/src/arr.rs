//! The arrangement lamp "arr" (arrangement-v1; NOTES.md, "Cost model: the arrangement lamp", 6062320, and the stride
//! ruling 77e898e, written before this code). The twin of evolve/arr.py: the same charges, in the same order, and the
//! same tests. In no deck.
//!
//! word, hash and sort_cmp charges go to their phases (PH_WORD, PH_HASH, PH_SORT); gcd = tests; mul is the rest
//! (main.rs, stage_types). SMALL counts the gcds whose non-N argument was < 2^32 at the call (information only).

use super::{Budget, Meter, Num, R, PH_HASH, PH_SORT, PH_WORD};
use ruint::aliases::U256;
use serde_json::Value;
use std::cell::Cell;
use std::collections::HashMap;

thread_local! {
    static SMALL: Cell<u64> = Cell::new(0);
}
pub fn small_reset() {
    SMALL.with(|s| s.set(0));
}
pub fn small_take() -> u64 {
    SMALL.with(|s| s.get())
}

fn gene(g: &Value, k: &str, lo: u64, hi: u64, default: Option<u64>) -> u64 {
    let v = match g.get(k) {
        Some(v) => v.as_u64().unwrap_or_else(|| panic!("arr: gene {k} out of range")),
        None => default.unwrap_or_else(|| panic!("arr: gene {k} out of range")),
    };
    assert!(v >= lo && v <= hi, "arr: gene {k} out of range");
    v
}

/// Refuses (panics) on a stage that may not be built, as arr.validate raises.
pub fn validate(s: &Value) {
    let (l, d) = (&s["layout"], &s["detect"]);
    let k = l["kind"].as_str().expect("arr: layout and detect must name a known kind");
    let r = d["kind"].as_str().expect("arr: layout and detect must name a known kind");
    match k {
        "stride" => {
            gene(l, "a", 0, u64::MAX, None);
            gene(l, "s", 1, u64::MAX, None);
        }
        "fold" => {
            gene(l, "w", 2, 4096, None);
            gene(l, "a", 0, u64::MAX, None);
            gene(l, "s", 1, u64::MAX, None);
        }
        "map" => {
            gene(l, "c", 0, u64::MAX, Some(1));
            gene(l, "x0", 0, u64::MAX, Some(2));
            let dd = gene(l, "d", 2, 8, Some(2));
            assert!(dd % 2 == 0, "arr: map degree d must be 2, 4, 6 or 8");
        }
        "bins" => {
            gene(l, "m", 1, u64::MAX, None);
            let b = gene(l, "B", 1, 1 << 16, None);
            assert!(b.is_power_of_two(), "arr: B must be a power of 2");
        }
        "exponent" => {
            gene(l, "a", 0, u64::MAX, None);
            gene(l, "K", 1, u64::MAX, None);
        }
        _ => panic!("arr: layout and detect must name a known kind"),
    }
    match r {
        "dot" => {
            gene(d, "t", 0, u64::MAX, Some(0));
        }
        "batch" => {
            gene(d, "t", 0, u64::MAX, Some(0));
            gene(d, "b", 1, 4096, None);
        }
        "floyd" | "brent" => {
            gene(d, "b", 1, 4096, None);
            assert!(k == "map" || k == "stride", "arr: floyd and brent need a map or stride layout");
        }
        "bins" => assert!(k == "bins", "arr: bin compare needs the bins layout"),
        _ => panic!("arr: layout and detect must name a known kind"),
    }
}

fn bit_length(x: u64) -> u64 {
    64 - x.leading_zeros() as u64
}

#[derive(Clone)]
struct Layout {
    kind: u8, // 0 stride, 1 fold, 2 map, 3 bins, 4 exponent
    n: U256,
    x: U256,
    s: U256,
    c: U256,
    d: u64,
    step: u64,
    w: u64,
    kk: u64,
    kmax: u64,
    started: bool,
}

impl Layout {
    fn new(g: &Value, n: U256) -> Layout {
        let u = |k: &str, def: u64| U256::from(g.get(k).and_then(|v| v.as_u64()).unwrap_or(def)).reduce_mod(n);
        let gi = |k: &str, def: u64| g.get(k).and_then(|v| v.as_u64()).unwrap_or(def);
        let zero = U256::ZERO;
        let mut l = Layout { kind: 0, n, x: zero, s: zero, c: zero, d: 2, step: 1, w: 0, kk: 0, kmax: 0, started: false };
        match g["kind"].as_str().unwrap() {
            "stride" => {
                l.x = u("a", 0);
                l.s = u("s", 1);
            }
            "fold" => {
                l.kind = 1;
                l.w = gi("w", 2);
                l.x = u("a", 0); // the next stride value
                l.s = u("s", 1);
            }
            "map" => {
                l.kind = 2;
                l.c = u("c", 1);
                l.d = gi("d", 2);
                l.x = u("x0", 2);
                l.step = (bit_length(l.d) - 1 + l.d.count_ones() as u64 - 1).max(1);
            }
            "bins" => {
                l.kind = 3;
                l.s = u("m", 1); // the multiplier m
            }
            _ => {
                l.kind = 4;
                l.x = u("a", 0);
                l.kmax = gi("K", 1);
            }
        }
        l
    }

    /// The step of a map or stride layout as a function, charged with `extra` more mul in the same charge.
    fn f(&self, v: U256, extra: u64, m: &mut Meter) -> Result<U256, Budget> {
        let n = self.n;
        if self.kind == 0 {
            m.phases[PH_WORD] += 1;
            m.tick(1 + extra)?;
            return Ok(v.add_mod(self.s, n));
        }
        m.tick(self.step + extra)?;
        let s = if self.d == 2 { v.mul_mod(v, n) } else { v.pow_mod(U256::from(self.d), n) };
        Ok(s.add_mod(self.c, n))
    }

    /// The next dot, or None when the layout is finished (exponent past K).
    fn dot(&mut self, m: &mut Meter) -> Result<Option<U256>, Budget> {
        let n = self.n;
        match self.kind {
            0 | 2 => {
                if self.started {
                    self.x = self.f(self.x, 0, m)?;
                }
                self.started = true;
                Ok(Some(self.x))
            }
            1 => {
                let mut p = U256::from(1u64);
                for _ in 0..self.w {
                    m.charge(PH_WORD, 1)?;
                    let v = self.x;
                    self.x = self.x.add_mod(self.s, n);
                    m.tick(1)?;
                    p = p.mul_mod(v, n);
                }
                Ok(Some(p))
            }
            3 => {
                m.charge(PH_WORD, 1)?;
                self.c = self.c.add_mod(self.s, n); // y = m * i
                m.tick(1)?;
                let x = self.c.mul_mod(self.c, n);
                m.charge(PH_HASH, 1)?;
                Ok(Some(x))
            }
            _ => {
                self.kk += 1;
                if self.kk > self.kmax {
                    return Ok(None);
                }
                m.tick(bit_length(self.kk).max(1))?;
                self.x = self.x.pow_mod(U256::from(self.kk), n);
                Ok(Some(self.x))
            }
        }
    }
}

/// One charged gcd of v with N and one luck-meter test (hit: the gcd is not 1).
fn gt(v: U256, n: U256, m: &mut Meter) -> Result<U256, Budget> {
    m.tick(1)?;
    if v.bit_len() <= 32 {  // small-k: argument < 2^32 (G_rho v2, 9e89a4e)
        SMALL.with(|s| s.set(s.get() + 1));
    }
    let g = v.gcd(n);
    m.test(g != U256::from(1u64));
    Ok(g)
}

/// (x - t) mod N for x, t < N.
fn sub_mod(x: U256, t: U256, n: U256) -> U256 {
    if x >= t {
        x - t
    } else {
        x + (n - t)
    }
}

fn absdiff(a: U256, b: U256) -> U256 {
    if a >= b {
        a - b
    } else {
        b - a
    }
}

pub fn lamp_arr(num: &Num, s: &Value, m: &mut Meter) -> R {
    validate(s);
    let n = num.n;
    let one = U256::from(1u64);
    let mut l = Layout::new(&s["layout"], n);
    let d = &s["detect"];
    let b = d.get("b").and_then(|v| v.as_u64()).unwrap_or(1);
    let t = U256::from(d.get("t").and_then(|v| v.as_u64()).unwrap_or(0)).reduce_mod(n);
    match d["kind"].as_str().unwrap() {
        "dot" => {
            while let Some(x) = l.dot(m)? {
                let g = gt(sub_mod(x, t, n), n, m)?;
                if g > one && g < n {
                    return Ok(Some(g));
                }
            }
            Ok(None)
        }
        "batch" => {
            let (mut st, mut q, mut cnt) = (l.clone(), one, 0u64);
            loop {
                let x = l.dot(m)?;
                if let Some(x) = x {
                    m.tick(1)?;
                    q = q.mul_mod(sub_mod(x, t, n), n);
                    cnt += 1;
                }
                if cnt > 0 && (cnt == b || x.is_none()) {
                    let g = gt(q, n, m)?;
                    if g == n {
                        for _ in 0..cnt {
                            let y = st.dot(m)?.unwrap();
                            let g = gt(sub_mod(y, t, n), n, m)?;
                            if g != one {
                                return Ok(if g < n { Some(g) } else { None });
                            }
                        }
                        return Ok(None);
                    }
                    if g != one {
                        return Ok(Some(g));
                    }
                    st = l.clone();
                    cnt = 0;
                }
                if x.is_none() {
                    return Ok(None);
                }
            }
        }
        "floyd" => {
            let mut x = l.dot(m)?.unwrap();
            let mut y = x;
            let (mut q, mut cnt, mut sx, mut sy) = (one, 0u64, x, y);
            loop {
                x = l.f(x, 0, m)?;
                y = l.f(y, 0, m)?;
                y = l.f(y, 0, m)?;
                m.tick(1)?;
                q = q.mul_mod(absdiff(x, y), n);
                cnt += 1;
                if cnt == b {
                    let g = gt(q, n, m)?;
                    if g == n {
                        let (mut x, mut y) = (sx, sy);
                        for _ in 0..cnt {
                            x = l.f(x, 0, m)?;
                            y = l.f(y, 0, m)?;
                            y = l.f(y, 0, m)?;
                            let g = gt(absdiff(x, y), n, m)?;
                            if g != one {
                                return Ok(if g < n { Some(g) } else { None });
                            }
                        }
                        return Ok(None);
                    }
                    if g != one {
                        return Ok(Some(g));
                    }
                    cnt = 0;
                    sx = x;
                    sy = y;
                }
            }
        }
        "brent" => {
            // lamp_rho's loop, with the layout's step
            let mut y = l.dot(m)?.unwrap();
            let (mut r, mut q, mut gg) = (1u64, one, one);
            let mut x;
            let mut ys = y;
            loop {
                x = y;
                for _ in 0..r {
                    y = l.f(y, 0, m)?;
                }
                let mut k = 0u64;
                while k < r && gg == one {
                    ys = y;
                    for _ in 0..b.min(r - k) {
                        y = l.f(y, 1, m)?;
                        q = q.mul_mod(absdiff(x, y), n);
                    }
                    gg = gt(q, n, m)?;
                    k += b;
                }
                r *= 2;
                if gg != one {
                    break;
                }
            }
            if gg == n {
                loop {
                    ys = l.f(ys, 0, m)?;
                    gg = gt(absdiff(x, ys), n, m)?;
                    if gg > one {
                        break;
                    }
                }
            }
            Ok(if gg > one && gg < n { Some(gg) } else { None })
        }
        _ => {
            // bin compare (bins layout only)
            let bmask = s["layout"]["B"].as_u64().unwrap() - 1;
            let mut bins: HashMap<u64, Vec<U256>> = HashMap::new();
            loop {
                let x = l.dot(m)?.unwrap();
                let lst = bins.entry(x.as_limbs()[0] & bmask).or_default();
                for &y in lst.iter() {
                    m.charge(PH_SORT, 1)?;
                    let g = gt(absdiff(x, y), n, m)?;
                    if g > one && g < n {
                        return Ok(Some(g));
                    }
                }
                lst.push(x);
            }
        }
    }
}
