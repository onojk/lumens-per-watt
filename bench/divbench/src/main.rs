// Word-division bench (the user's ruling, Oct 30, family (2) SQUFOF-like): the timed D = time of a 64-bit DIV / time of
// a timed word add, each in the same dependent chain (the division in SQUFOF's step is on the critical path: b depends
// on the previous Q). Operands of SQUFOF's size at N of `bits` bits: dividend ~ 2^(bits/2) (P0 + P_i), divisor uniform
// in [2^(bits/4), 2^(bits/2)) (Q_i). Never charged; timing only.
// args: bits mode(div|add|loop) M seed reps -> one line per rep: ns per iteration
use std::hint::black_box;
use std::time::Instant;
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let bits: u32 = a[1].parse().unwrap();
    let mode = a[2].clone();
    let m: usize = a[3].parse().unwrap();
    let mut s: u64 = a[4].parse().unwrap();
    let reps: usize = a[5].parse().unwrap();
    let mut rnd = || { s ^= s << 13; s ^= s >> 7; s ^= s << 17; s };
    let half = bits / 2;
    let quarter = bits / 4;
    let n = 1usize << 16;
    let num: Vec<u64> = (0..n).map(|_| (rnd() >> (64 - half)) | (1u64 << (half - 1))).collect();
    let den: Vec<u64> = (0..n).map(|_| {
        let lo = 1u64 << quarter;
        let span = (1u64 << half) - lo;
        lo + rnd() % span
    }).collect();
    for _ in 0..reps {
        let mut acc: u64 = 0;
        let t = Instant::now();
        match mode.as_str() {
            "div" => for i in 0..m { let j = i & (n - 1); acc = acc.wrapping_add(black_box(num[j] ^ (acc & 1)) / black_box(den[j])); },
            "add" => for i in 0..m { let j = i & (n - 1); acc = acc.wrapping_add(black_box(num[j] ^ (acc & 1)).wrapping_add(black_box(den[j]))); },
            _     => for i in 0..m { let j = i & (n - 1); acc = acc.wrapping_add(black_box(num[j] ^ (acc & 1)) ^ black_box(den[j])); },
        }
        let dt = t.elapsed().as_secs_f64();
        black_box(acc);
        println!("{:.4}", dt * 1e9 / m as f64);
    }
}
