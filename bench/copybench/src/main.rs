//! Kept-relation copy microbenchmark (NOTES.md, "Stage 3: kept-relation copies"; cost note only, lampcore untouched).
//! Mirrors lampcore's path for one kept relation (qs.rs 1235-1250 and Ledger::add 387-389): the sparse list built
//! from the touched entries into a reused buffer (`kept`), then appended to a growing arena with its record pushed.
//! Usage: copybench <list_len> <relations> <width> <reps> [<F> <a_index> <s>]
//!   list_len   entries (u32, u32) per kept relation
//!   relations  kept relations per "number" (the arena grows from empty to relations x list_len, then is dropped)
//!   width      sieve width: a sieve-sized i32 array swept (read-modify-write) between copies, as the card's sieve
//!              works between kept relations (cache pressure)
//!   reps       numbers simulated
//!   F a_index s  optional: also, per kept relation, the s A-primes' base indices found as lampcore finds them
//!              (qs.rs 607 `pos`: a linear `position` scan of the F-entry factor base), the primes at index ~a_index
//! Whole-loop timings (no timer inside the loop): copies alone, sweeps alone, both interleaved; with F: the lookups alone.
//! Prints ns per copy alone, and under pressure = (both - sweeps alone) / copies.
use std::hint::black_box;
use std::time::Instant;

fn pass(len: usize, rels: usize, width: usize, reps: usize, copy: bool, sweep: bool) -> (f64, u64) {
    let ev: Vec<u32> = (0..4096u32).map(|i| (i % 7) + 1).collect();
    let tt: Vec<u32> = (0..len as u32).map(|i| (i * 37) % 4096).collect();
    let mut arr = vec![0i32; width.max(1)];
    let mut sink = 0u64;
    let t0 = Instant::now();
    for r in 0..reps {
        let mut kept: Vec<(u32, u32)> = Vec::new();
        let mut arena: Vec<(u32, u32)> = Vec::new();
        let mut recs: Vec<(i128, u32, u32, i128)> = Vec::new();
        for k in 0..rels {
            if sweep {
                for x in arr.iter_mut() {
                    *x = x.wrapping_add((k as i32) ^ (r as i32));
                }
                black_box(&mut arr);
            }
            if copy {
                kept.clear();
                kept.extend(tt.iter().map(|&j| (j, ev[j as usize])));
                let off = arena.len() as u32;
                arena.extend_from_slice(&kept);
                recs.push((k as i128, off, kept.len() as u32, 1));
            }
        }
        sink = sink.wrapping_add(arena.len() as u64 + recs.len() as u64);
        black_box((&arena, &recs));
    }
    (t0.elapsed().as_nanos() as f64, sink)
}

fn lookups(f: usize, idx: usize, s: usize, rels: usize, reps: usize) -> f64 {
    let base: Vec<i64> = (0..f as i64).map(|i| 2 * i + 3).collect();
    let qs_: Vec<u64> = (0..s).map(|l| base[(idx + l).min(f - 1)] as u64).collect();
    let pos = |p: u64| base.iter().position(|&b| b == p as i64).unwrap();
    let mut sink = 0usize;
    let t0 = Instant::now();
    for _ in 0..reps {
        for _ in 0..rels {
            for &ql in black_box(&qs_) {
                sink = sink.wrapping_add(pos(ql));
            }
        }
    }
    black_box(sink);
    t0.elapsed().as_nanos() as f64
}

fn main() {
    let a: Vec<usize> = std::env::args().skip(1).map(|x| x.parse().unwrap()).collect();
    let (len, rels, width, reps) = (a[0], a[1], a[2], a[3]);
    let copies = (rels * reps) as f64;
    if a.len() >= 7 {
        let l = lookups(a[4], a[5], a[6], rels, reps);
        println!("{{\"F\": {}, \"a_index\": {}, \"s\": {}, \"ns_per_relation_lookups\": {:.2}}}", a[4], a[5], a[6], l / copies);
    }
    let (c, s1) = pass(len, rels, width, reps, true, false);
    let (s, _) = pass(len, rels, width, reps, false, true);
    let (b, s2) = pass(len, rels, width, reps, true, true);
    println!("{{\"list_len\": {len}, \"relations\": {rels}, \"width\": {width}, \"reps\": {reps}, \"ns_per_copy_alone\": {:.2}, \
              \"ns_per_copy_under_pressure\": {:.2}, \"sweep_ns_per_copy\": {:.2}, \"sink\": {}}}",
             c / copies, (b - s) / copies, s / copies, s1.wrapping_add(s2));
}
