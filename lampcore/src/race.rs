//! Stage 9 race combinator, identical to evolve/race.py (NOTES.md, "Stage 9: race
//! combinator"). Each side runs in its own scoped thread with strict hand-over over channels,
//! so no lamp changes: the side's Meter carries a hook that counts its slice and, right after
//! the charge that fills it, hands control back to the race. Exactly one thread runs at a
//! time. The side's Meter mirrors the shared op total (synced at every hand-over), so the cap
//! check and the ps / pm1 prechecks read the shared meter, as in Python.

use crate::{Budget, Meter, Num, R};
use serde_json::Value;
use std::sync::mpsc::{channel, Receiver, Sender};

pub(crate) enum Cmd {
    Resume { ops: u64, solo: bool },
    Abort,
}

enum Ev {
    Paused { ops: u64 },
    Done(SideEnd),
}

struct SideEnd {
    res: R,
    ops: u64,      // the shared total when the side stopped
    side_ops: u64, // this side's own official ops
    tests: u64,
    hits: u64,
    k: Option<u64>,
    phases: [u64; 16],
    types: crate::Types,
}

/// The per-side part of a Meter inside a race.
pub(crate) struct Hook {
    size: u64,
    counter: u64,
    pub(crate) side_ops: u64,
    solo: bool, // the other side cannot run (ended, or slice 0): never hand over
    tx: Sender<Ev>,
    rx: Receiver<Cmd>,
}

impl Hook {
    /// Called by Meter::tick after the charge is applied and under the cap. Returns Err to
    /// unwind a side whose race has ended (teardown).
    pub(crate) fn after_charge(&mut self, k: u64, ops: &mut u64) -> Result<(), Budget> {
        self.counter += k;
        if self.counter >= self.size && !self.solo {
            self.counter = 0;
            self.tx.send(Ev::Paused { ops: *ops }).unwrap();
            match self.rx.recv().unwrap() {
                Cmd::Resume { ops: o, solo } => {
                    *ops = o;
                    self.solo = solo;
                }
                Cmd::Abort => return Err(Budget),
            }
        }
        Ok(())
    }
}

pub(crate) fn validate(g: &Value) {
    for side in ["a", "b"] {
        assert!(g[side].is_object() && g[side]["t"].is_string(), "race: side {side} must be a stage");
        assert!(g[side]["t"] != "race", "race: nested races are out of scope");
    }
    for key in ["sa", "sb"] {
        assert!(g[key].is_u64(), "race: {key} must be a non-negative integer");
    }
    assert!(!(g["sa"] == 0 && g["sb"] == 0), "race: sa = sb = 0 is invalid");
}

#[derive(PartialEq, Clone, Copy)]
enum St {
    New,
    Paused,
    Done,
}

pub fn lamp_race(num: &Num, g: &Value, m: &mut Meter) -> R {
    validate(g);
    let stages = [&g["a"], &g["b"]];
    let sizes = [g["sa"].as_u64().unwrap(), g["sb"].as_u64().unwrap()];
    let cap = m.cap;
    let mut shared = m.ops;
    let mut state = [St::New, St::New];
    let mut side_ops = [0u64; 2];
    let mut switches = 0u64;
    let (ev_tx, ev_rx): (Vec<Sender<Ev>>, Vec<Receiver<Ev>>) = (0..2).map(|_| channel()).unzip();
    let mut cmd_tx: Vec<Option<Sender<Cmd>>> = vec![None, None];

    let out: R = std::thread::scope(|sc| {
        let mut cur = if sizes[0] > 0 { 0 } else { 1 };
        let absorb = |e: &SideEnd, m: &mut Meter, side_ops: &mut [u64; 2], i: usize| {
            m.tests += e.tests;
            m.hits += e.hits;
            for (a, b) in m.phases.iter_mut().zip(e.phases.iter()) {
                *a += b;
            }
            for (a, b) in m.types.iter_mut().zip(e.types.iter()) {
                *a += b;
            }
            side_ops[i] = e.side_ops;
        };
        let result = loop {
            let other = 1 - cur;
            let solo = sizes[other] == 0 || state[other] == St::Done;
            if state[cur] == St::New {
                let (ctx, crx) = channel();
                cmd_tx[cur] = Some(ctx);
                let tx = ev_tx[cur].clone();
                let (stage, size, ops) = (stages[cur], sizes[cur], shared);
                sc.spawn(move || {
                    let hook = Hook { size, counter: 0, side_ops: 0, solo, tx: tx.clone(), rx: crx };
                    let mut sm = Meter { ops, cap, tests: 0, hits: 0, k: None, phases: [0; 16], hook: Some(Box::new(hook)), race: None, ob: None, ob_spent: 0, ob_hit: false, ev: [0; 7], types: [0; 24] };
                    let res = crate::run_stage(num, stage, &mut sm);
                    let h = sm.hook.take().unwrap();
                    let types = crate::stage_types(stage["t"].as_str().unwrap(), h.side_ops, sm.tests, &sm.phases, &sm.ev);
                    let end = SideEnd { res, ops: sm.ops, side_ops: h.side_ops, tests: sm.tests, hits: sm.hits, k: sm.k, phases: sm.phases, types };
                    tx.send(Ev::Done(end)).unwrap();
                });
            } else {
                cmd_tx[cur].as_ref().unwrap().send(Cmd::Resume { ops: shared, solo }).unwrap();
            }
            match ev_rx[cur].recv().unwrap() {
                Ev::Paused { ops } => {
                    shared = ops;
                    state[cur] = St::Paused;
                    switches += 1;
                    cur = other;
                }
                Ev::Done(e) => {
                    shared = e.ops;
                    state[cur] = St::Done;
                    absorb(&e, m, &mut side_ops, cur);
                    match e.res {
                        Err(Budget) => break Err(Budget),
                        Ok(Some(d)) => {
                            m.k = e.k;
                            break Ok(Some(d));
                        }
                        Ok(None) => {
                            if sizes[other] > 0 && state[other] != St::Done {
                                cur = other; // runs alone from here
                            } else {
                                break Ok(None);
                            }
                        }
                    }
                }
            }
        };
        // teardown: a paused side unwinds through Budget; its counts so far are kept
        for i in 0..2 {
            if state[i] == St::Paused {
                cmd_tx[i].as_ref().unwrap().send(Cmd::Abort).unwrap();
                loop {
                    match ev_rx[i].recv().unwrap() {
                        Ev::Done(e) => {
                            absorb(&e, m, &mut side_ops, i);
                            break;
                        }
                        Ev::Paused { .. } => unreachable!("a torn-down side cannot pause"),
                    }
                }
                state[i] = St::Done;
            }
        }
        result
    });
    m.ops = shared;
    m.race = Some((side_ops[0], side_ops[1], switches));
    out
}
