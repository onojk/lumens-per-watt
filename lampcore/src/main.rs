//! lampcore: the lumens-per-watt lamps in Rust, with operation counting identical to
//! evolve/lamps.py, so the same experiments can run on much bigger numbers.
//!
//! Protocol (stdin -> stdout):
//!   line 1: genome as JSON (the same list of stages lamps.py uses)
//!   line 2: op cap (a run that would exceed it is a miss)
//!   then one line per number: "N p q" in decimal (p, q = its prime factors)
//! For each number one line comes back:
//!   "<ops> <factor> <tests> <hits> <stage> <k>"   or   "miss <tests> <hits>"
//! If the genome has a quadratic-sieve stage, both lines end with qs's seven per-phase op
//! counts (mult fb setup sieve confirm la sqrt), for the parity check.
//! stage is the winning stage's index; k is the multiplier a square-search win came from,
//! "-" for any other lamp (read-only instrumentation: it never changes the op count).
//!
//! p and q are used only by the block-flash replay (see lamp_ps). Every other lamp
//! computes on N alone.

use ruint::aliases::U256;
use serde_json::Value;
use std::io::{self, BufRead, BufWriter, Write};

mod qs;

struct Budget;
type R = Result<Option<U256>, Budget>;

struct Meter {
    ops: u64,
    cap: u64,
    tests: u64,
    hits: u64,
    k: Option<u64>, // instrumentation: the k a square-search win came from
    phases: [u64; 7], // qs's ops by phase (see qs.rs)
}

impl Meter {
    #[inline]
    fn tick(&mut self, k: u64) -> Result<(), Budget> {
        self.ops += k;
        if self.ops > self.cap {
            Err(Budget)
        } else {
            Ok(())
        }
    }
    #[inline]
    fn charge(&mut self, phase: usize, k: u64) -> Result<(), Budget> {
        self.phases[phase] += k;
        self.tick(k)
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

fn ks_score(k: u64, num: &Num) -> f64 {
    let kn = U256::from(k) * num.n;
    let r8 = (kn % U256::from(8u64)).to::<u64>();
    let base = if r8 == 1 { 2.0 } else if r8 == 5 { 1.0 } else { 0.5 };
    let mut s = base * 2f64.ln() - 0.5 * (k as f64).ln();
    for &p in KS_PRIMES.iter() {
        if k % p == 0 {
            s += (p as f64).ln() / p as f64;
        } else {
            let r = (kn % U256::from(p)).to::<u64>();
            if powmod_small(r, (p - 1) / 2, p) == 1 {
                s += 2.0 * (p as f64).ln() / (p - 1) as f64;
            }
        }
    }
    s
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
    if g["ksq"].as_bool().unwrap() {
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
                seen.insert(k);
                if let Some(d) = sq_one_k(num, g, k, m)? {
                    return Ok(Some(d));
                }
            }
            for k in 1..=kk {
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
                let mut block: Vec<(u64, f64)> =
                    (i..=hi).map(|j| (mult * j, 0.0)).collect();
                m.tick(block.len() as u64 * KS_PRIMES.len() as u64)?;
                for b in block.iter_mut() {
                    b.1 = -ks_score(b.0, num);
                }
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
    let bnd = (num.f.powf(gf(g, "b")) as u64).max(10);
    // Each prime ticks at least once, so if even a lower bound on pi(B) can't fit in the
    // remaining budget the run would miss anyway; stop before sieving a huge range.
    let lower_pi = bnd as f64 / (bnd as f64).ln();
    if bnd > (1 << 26) && (m.ops as f64 + lower_pi) > m.cap as f64 {
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
    Ok(if d > U256::from(1u64) && d < n { Some(d) } else { None })
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
    if m.ops + (b - 1) + (nblocks - 1) > m.cap {
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

fn run(genome: &[Value], num: &Num, cap: u64) -> (Option<Win>, u64, u64, [u64; 7]) {
    let mut m = Meter { ops: 0, cap, tests: 0, hits: 0, k: None, phases: [0; 7] };
    for (i, s) in genome.iter().enumerate() {
        let r = match s["t"].as_str().unwrap() {
            "td" => lamp_td(num, s, &mut m),
            "sq" => lamp_sq(num, s, &mut m),
            "rho" => lamp_rho(num, s, &mut m),
            "pm1" => lamp_pm1(num, s, &mut m),
            "ps" => lamp_ps(num, s, &mut m),
            "qs" => qs::lamp_qs(num, s, &mut m),
            other => panic!("unknown lamp {other}"),
        };
        match r {
            Ok(Some(d)) => {
                let w = Win { ops: m.ops, d, stage: i, k: m.k };
                return (Some(w), m.tests, m.hits, m.phases);
            }
            Ok(None) => continue,
            Err(Budget) => return (None, m.tests, m.hits, m.phases),
        }
    }
    (None, m.tests, m.hits, m.phases)
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    let genome: Value = serde_json::from_str(&lines.next().unwrap().unwrap()).unwrap();
    let genome = genome.as_array().unwrap().clone();
    let cap: u64 = lines.next().unwrap().unwrap().trim().parse().unwrap();
    let has_qs = genome.iter().any(|s| s["t"] == "qs");
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
        let (res, t, h, ph) = run(&genome, &num, cap);
        let tail = if has_qs {
            ph.iter().map(|x| format!(" {x}")).collect::<String>()
        } else {
            String::new()
        };
        match res {
            Some(w) => {
                let k = w.k.map_or("-".to_string(), |k| k.to_string());
                writeln!(out, "{} {} {t} {h} {} {k}{tail}", w.ops, w.d, w.stage).unwrap()
            }
            None => writeln!(out, "miss {t} {h}{tail}").unwrap(),
        }
    }
}
