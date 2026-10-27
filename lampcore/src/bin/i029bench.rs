//! I-029 microbenchmark (NOTES.md, "I-029 microbenchmark: design note"; report only, not in the card).
//! Reads captured 96-bit candidates (evolve/i029_capture.py) on stdin and times three confirm versions per candidate:
//! (a) today's full pass (v mod p by i128 remainder for every base prime), (b) the root test (i0 mod p, by a
//! precomputed reciprocal when i0 >= p, against the prime's roots; divide only the matching primes), (c) (b) with a
//! branch-free first pass. Correctness gate: (b) and (c) give the same (index, exponent) lists and cofactor as (a).
//! Prints one JSON line.
use std::hint::black_box;
use std::io::Read;
use std::time::Instant;

struct Poly {
    base: usize, // index into bases
    r1: Vec<u32>,
    r2: Vec<u32>,
    cands: Vec<(u32, i128)>,
}

struct Base {
    p: Vec<i128>,      // the base, p[0] = -1, p[1] = 2
    po: Vec<u32>,      // the odd primes (p[2..])
    mo: Vec<u64>,      // their reciprocals for fastmod
}

#[inline(always)]
fn fastmod(x: u32, m: u64, p: u32) -> u32 {
    let low = m.wrapping_mul(x as u64);
    ((low as u128 * p as u128) >> 64) as u32
}

#[inline(always)]
fn divide(v: &mut i128, p: i128, j: u32, out: &mut Vec<(u32, u32)>) {
    let mut e = 0u32;
    while *v % p == 0 {
        *v /= p;
        e += 1;
    }
    if e > 0 {
        out.push((j, e));
    }
}

fn full_pass(b: &Base, v0: i128, out: &mut Vec<(u32, u32)>) -> i128 {
    out.clear();
    let mut v = v0.abs();
    for j in 1..b.p.len() {
        let p = b.p[j];
        if v % p == 0 {
            let mut e = 1u32;
            v /= p;
            while v % p == 0 {
                v /= p;
                e += 1;
            }
            out.push((j as u32, e));
        }
    }
    v
}

fn root_test(b: &Base, py: &Poly, i0: u32, v0: i128, out: &mut Vec<(u32, u32)>) -> i128 {
    out.clear();
    let mut v = v0.abs();
    if v & 1 == 0 {
        divide(&mut v, 2, 1, out);
    }
    for k in 0..b.po.len() {
        let p = b.po[k];
        let r = if i0 < p { i0 } else { fastmod(i0, b.mo[k], p) };
        if r == py.r1[k] || r == py.r2[k] {
            divide(&mut v, p as i128, (k + 2) as u32, out);
        }
    }
    v
}

fn root_test_bf(b: &Base, py: &Poly, i0: u32, v0: i128, out: &mut Vec<(u32, u32)>, hits: &mut Vec<u32>) -> i128 {
    out.clear();
    let n = b.po.len();
    hits.resize(n + 1, 0);
    let mut cnt = 0usize;
    for k in 0..n {
        let p = b.po[k];
        let f = fastmod(i0, b.mo[k], p);
        let r = if i0 < p { i0 } else { f };
        let hit = (r == py.r1[k]) as usize | (r == py.r2[k]) as usize;
        hits[cnt] = k as u32;
        cnt += hit;
    }
    let mut v = v0.abs();
    if v & 1 == 0 {
        divide(&mut v, 2, 1, out);
    }
    for &k in &hits[..cnt] {
        divide(&mut v, b.po[k as usize] as i128, k + 2, out);
    }
    v
}

fn main() {
    let mut s = String::new();
    std::io::stdin().read_to_string(&mut s).unwrap();
    let mut bases: Vec<Base> = Vec::new();
    let mut polys: Vec<Poly> = Vec::new();
    let mut lines = s.lines();
    while let Some(l) = lines.next() {
        let f: Vec<&str> = l.split_whitespace().collect();
        if f.is_empty() {
            continue;
        }
        match f[0] {
            "base" => {
                let p: Vec<i128> = f[1..].iter().map(|x| x.parse().unwrap()).collect();
                assert!(p[0] == -1 && p[1] == 2);
                let po: Vec<u32> = p[2..].iter().map(|&x| x as u32).collect();
                let mo = po.iter().map(|&q| u64::MAX / q as u64 + 1).collect();
                bases.push(Base { p, po, mo });
            }
            "poly" => {
                let nc: usize = f[1].parse().unwrap();
                let rs: Vec<u32> = lines.next().unwrap().split_whitespace().map(|x| x.parse().unwrap()).collect();
                let b = bases.len() - 1;
                assert_eq!(rs.len(), 2 * bases[b].po.len());
                let (r1, r2) = (rs.iter().step_by(2).copied().collect(), rs.iter().skip(1).step_by(2).copied().collect());
                let mut cands = Vec::with_capacity(nc);
                for _ in 0..nc {
                    let c: Vec<&str> = lines.next().unwrap().split_whitespace().collect();
                    cands.push((c[0].parse().unwrap(), c[1].parse().unwrap()));
                }
                polys.push(Poly { base: b, r1, r2, cands });
            }
            _ => panic!("bad line {l}"),
        }
    }
    let ncand: usize = polys.iter().map(|p| p.cands.len()).sum();
    let tested: usize = polys.iter().map(|p| p.cands.len() * (bases[p.base].p.len() - 1)).sum();
    // correctness gate
    let (mut oa, mut ob, mut oc, mut hits) = (Vec::new(), Vec::new(), Vec::new(), Vec::new());
    let mut ndiv = 0usize;
    for py in &polys {
        let b = &bases[py.base];
        for &(i0, v) in &py.cands {
            let ca = full_pass(b, v, &mut oa);
            let cb = root_test(b, py, i0, v, &mut ob);
            let cc = root_test_bf(b, py, i0, v, &mut oc, &mut hits);
            assert!(ca == cb && ca == cc && oa == ob && oa == oc, "mismatch at i0 {i0}, v {v}: {oa:?} {ob:?} {oc:?}");
            ndiv += oa.len();
        }
    }
    // timing: passes interleaved a, b, c until each has >= 0.5 s
    let mut t: [Vec<f64>; 3] = [Vec::new(), Vec::new(), Vec::new()];
    let mut tot = [0f64; 3];
    let mut chk = 0i128;
    while tot.iter().any(|&x| x < 0.5) {
        for ver in 0..3 {
            let st = Instant::now();
            for py in &polys {
                let b = &bases[py.base];
                for &(i0, v) in &py.cands {
                    let c = match ver {
                        0 => full_pass(b, black_box(v), &mut oa),
                        1 => root_test(b, py, black_box(i0), black_box(v), &mut ob),
                        _ => root_test_bf(b, py, black_box(i0), black_box(v), &mut oc, &mut hits),
                    };
                    chk = chk.wrapping_add(c);
                }
            }
            let el = st.elapsed().as_secs_f64();
            tot[ver] += el;
            t[ver].push(el * 1e9 / ncand as f64);
        }
    }
    black_box(chk);
    let stat = |v: &Vec<f64>| {
        let mut s = v.clone();
        s.sort_by(|a, b| a.partial_cmp(b).unwrap());
        (s[s.len() / 2], s.iter().sum::<f64>() / s.len() as f64, s.len())
    };
    let per_prime = ncand as f64 / tested as f64;
    let mut parts = Vec::new();
    for (ver, name) in ["full", "root", "root_bf"].iter().enumerate() {
        let (med, mean, n) = stat(&t[ver]);
        parts.push(format!(
            "\"{name}\": {{\"ns_per_cand_median\": {med:.2}, \"ns_per_cand_mean\": {mean:.2}, \"ns_per_prime_median\": {:.3}, \"ns_per_prime_mean\": {:.3}, \"passes\": {n}}}",
            med * per_prime,
            mean * per_prime
        ));
    }
    println!(
        "{{\"candidates\": {ncand}, \"polys\": {}, \"primes_tested_per_cand\": {:.2}, \"dividing_primes_per_cand\": {:.2}, \"gate\": \"passed\", {}}}",
        polys.len(),
        tested as f64 / ncand as f64,
        ndiv as f64 / ncand as f64,
        parts.join(", ")
    );
}
