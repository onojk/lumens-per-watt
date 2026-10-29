// gcd cost bench (scratch, untimed, callgrind only): M calls of U256::gcd as lampcore uses it.
// args: bits mode(small|uniform|tdmod and the *0 baselines) M seed; the *0 modes make the same k without the gcd (baseline). small: k = 2, 3, ... (the vl lamp's dots); uniform: k uniform below N.
use ruint::aliases::U256;
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let bits: usize = a[1].parse().unwrap();
    let mode = a[2].as_str();
    let m: u64 = a[3].parse().unwrap();
    let mut s: u64 = a[4].parse().unwrap();
    let mut rnd = || { s ^= s << 13; s ^= s >> 7; s ^= s << 17; s };
    let rand_below_bits = |r: &mut dyn FnMut() -> u64, b: usize| -> U256 {
        let mut v = U256::from_limbs([r(), r(), r(), r()]);
        v = v >> (256 - b);
        v
    };
    let mut n = rand_below_bits(&mut rnd, bits) | (U256::from(1u64) << (bits - 1)) | U256::from(1u64);
    if n.bit_len() != bits { n |= U256::from(1u64) << (bits - 1); }
    let mut acc = U256::ZERO;
    for i in 0..m {
        let k = if mode.starts_with("small") { U256::from(i + 2) } else {
            let mut k = rand_below_bits(&mut rnd, bits);
            while k >= n || k == U256::ZERO { k = rand_below_bits(&mut rnd, bits); }
            k
        };
        if mode == "tdmod" { let nn: u128 = n.to::<u128>(); let d: u128 = (2 * i + 3) as u128; acc ^= U256::from(std::hint::black_box(nn) % std::hint::black_box(d)); continue; }
        if mode == "tdmod0" { let d: u128 = (2 * i + 3) as u128; acc ^= U256::from(std::hint::black_box(d)); continue; }
        if mode.ends_with("0") { acc ^= std::hint::black_box(k); } else { acc ^= std::hint::black_box(k).gcd(std::hint::black_box(n)); }
    }
    println!("{}", acc);
}
