//! Independent oracle (NOTES.md, "Library references and oracles"): num-prime, a test-only
//! dev-dependency, checks study populations and lampcore's answers. It is never reachable
//! from charged code (`cargo tree -e normal` lists only ruint and serde_json).

use num_prime::nt_funcs::{factorize128, is_prime};
use std::collections::BTreeMap;
use std::io::Write;
use std::process::{Command, Stdio};

fn numbers() -> Vec<(u128, u128, u128)> {
    include_str!("data/oracle_numbers.txt")
        .lines()
        .filter(|l| !l.starts_with('#') && !l.trim().is_empty())
        .map(|l| {
            let v: Vec<u128> = l.split_whitespace().map(|x| x.parse().unwrap()).collect();
            (v[0], v[1], v[2])
        })
        .collect()
}

#[test]
fn populations_are_semiprimes() {
    for (n, p, q) in numbers() {
        assert_eq!(p * q, n, "p q != N for {n}");
        assert!(is_prime(&p, None).probably() && is_prime(&q, None).probably(), "a factor of {n} is not prime");
        let want: BTreeMap<u128, usize> = [(p, 1), (q, 1)].into_iter().collect();
        assert_eq!(factorize128(n), want, "num-prime factors {n} differently");
    }
}

#[test]
fn lampcore_answers_divide() {
    let nums = numbers();
    let input: String = nums.iter().map(|(n, p, q)| format!("{n} {p} {q}\n")).collect();
    for genome in [
        r#"[{"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4}]"#,
        r#"[{"t": "ecm", "b1": 1.0, "b2": 50}]"#,
        r#"[{"t": "rho", "c": 1, "b": 64}]"#,
    ] {
        let mut child = Command::new(env!("CARGO_BIN_EXE_lampcore"))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()
            .unwrap();
        child.stdin.take().unwrap().write_all(format!("{genome}\n{}\n{input}", 1u64 << 28).as_bytes()).unwrap();
        let out = String::from_utf8(child.wait_with_output().unwrap().stdout).unwrap();
        let lines: Vec<&str> = out.lines().collect();
        assert_eq!(lines.len(), nums.len());
        for ((n, p, q), line) in nums.iter().zip(lines) {
            let f: Vec<&str> = line.split_whitespace().collect();
            assert_ne!(f[0], "miss", "{genome} missed {n}");
            let d: u128 = f[1].parse().unwrap();
            assert!(d == *p || d == *q, "{genome} returned {d} for {n}, not a factor");
        }
    }
}
