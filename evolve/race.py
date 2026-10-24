"""Stage 9 race combinator (NOTES.md, "Stage 9: race combinator", accepted Oct 23).

  {"t": "race", "a": stageA, "b": stageB, "sa": opsA, "sb": opsB}

A runs for a slice of sa official ops, then B for sb, alternating on one meter, until a side
returns a factor or the cap is reached. Each side runs in its own thread with strict handoff
(exactly one runs at any moment), so every side resumes from its own state and no lamp's
code changes.

- Switching costs 0 ops (SWITCH_COST, a mutation hook, must stay 0). Nothing is charged for
  the race itself.
- The slice rule: every charge is applied whole, to the meter and to the side's slice
  counter. The slice ends at the first charge that brings the counter to or past the slice
  size, and the hand-over happens right after that charge is applied, so every charge a
  card has recorded in its trace has been applied. The overshoot belongs to that side, and
  the next slice starts at 0. A factor found mid-slice is returned at once.
- A side whose slice size is 0 never runs (so sb = 0 is A alone, sa = 0 is B alone).
- A side that ends without a factor leaves the other to run alone, with no more switching.
  Both ending without a factor: the race returns None. A Budget raised in either side ends
  the whole race as a miss.
- Prechecks reading m.ops / m.cap (ps, pm1) read the shared meter.
- Tests and hits go to the shared meter as they happen; the winner's k is the race's k.

Set race.TRACE = {} before a run to record, per side, official ops, tests, hits, slice
lengths, ops per type (optypes.py; the two sides sum to the race's ops) and how it ended,
plus the switches. RECORD_CHARGES = True also records each side's charge sizes in order
(tests only).
"""
import threading
import optypes
import qs, ecm, cfrac

TRACE = None
RECORD_CHARGES = False
SWITCH_COST = 0                     # mutation hook for race_accept.py; the cost model says 0
TRACED = {"qs": qs, "ecm": ecm, "cfrac": cfrac}   # cards that read module TRACE at entry

def validate(s):
    """Raises ValueError for a race stage that may not be built: a nested race, a missing
    or negative slice, or sa = sb = 0."""
    for side in ("a", "b"):
        if not isinstance(s.get(side), dict) or "t" not in s[side]:
            raise ValueError(f"race: side {side} must be a stage")
        if s[side]["t"] == "race":
            raise ValueError("race: nested races are out of scope")
    for k in ("sa", "sb"):
        if not isinstance(s.get(k), int) or s[k] < 0:
            raise ValueError(f"race: {k} must be a non-negative integer")
    if s["sa"] == 0 and s["sb"] == 0:
        raise ValueError("race: sa = sb = 0 is invalid")

def validate_genome(gen):
    for s in gen:
        if s["t"] == "race":
            validate(s)

class _Teardown(BaseException):
    """Unwinds a paused side whose race has ended. BaseException, so no card catches it."""

class _Side:
    def __init__(self, race, idx, stage, size):
        self.race, self.idx, self.stage, self.size = race, idx, stage, size
        self.counter = 0            # ops in the current slice
        self.ops = self.tests = self.hits = 0
        self.k = None               # the shared-meter instrumentation slot, per side
        self.slices = []            # lengths of finished slices (each ended by a hand-over)
        self.charges = [] if RECORD_CHARGES else None
        self.trace = {} if (TRACE is not None and stage["t"] in TRACED) else None
        self.sem = threading.Semaphore(0)
        self.thread = None
        self.state = "new"          # new, running, paused, done
        self.abort = False
        self.result = None          # ("found", d) | ("none",) | ("error", exc)

    # ---- the meter interface the cards use ----
    @property
    def ops_shared(self):
        return self.race.m.ops

    def tick(self, k=1):
        r = self.race
        self.ops += k                                  # counted before Budget, as Meter.tick does
        self.counter += k
        if self.charges is not None:
            self.charges.append(k)
        r.m.tick(k)                                    # may raise Budget: the whole race misses
        oth = r.other(self)
        if self.counter >= self.size and oth.size > 0 and oth.state in ("new", "paused"):
            self.slices.append(self.counter)
            self.counter = 0
            r.pause(self)                              # returns when this side is resumed
            if SWITCH_COST:
                self.ops += SWITCH_COST
                r.m.tick(SWITCH_COST)

    def test(self, hit):
        self.race.m.test(hit)
        self.tests += 1
        if hit:
            self.hits += 1

class _SideMeter:
    """What a card sees: tick/test go through the side; ops and cap are the shared meter's."""
    def __init__(self, side):
        self._s = side
    def tick(self, k=1):
        self._s.tick(k)
    def test(self, hit):
        self._s.test(hit)
    @property
    def ops(self):
        return self._s.race.m.ops
    @property
    def cap(self):
        return self._s.race.m.cap
    @property
    def k(self):
        return self._s.k
    @k.setter
    def k(self, v):
        self._s.k = v

class _Race:
    def __init__(self, N, s, m):
        self.N, self.m = N, m
        self.sides = [_Side(self, 0, s["a"], s["sa"]), _Side(self, 1, s["b"], s["sb"])]
        self.main = threading.Semaphore(0)
        self.switches = 0

    def other(self, side):
        return self.sides[1 - side.idx]

    # ---- side thread ----
    def _body(self, side):
        from lamps import LAMPS                       # lamps imports this module
        try:
            d = LAMPS[side.stage["t"]](self.N, side.stage, _SideMeter(side))
            side.result = ("found", d) if d else ("none",)
        except _Teardown:
            side.result = ("torn down",)
            return                                    # the main thread is not waiting
        except BaseException as e:                    # Budget, or a real error
            side.result = ("error", e)
        side.state = "done"
        self.main.release()

    def pause(self, side):
        side.state = "paused"
        self.main.release()
        side.sem.acquire()
        if side.abort:
            raise _Teardown()
        side.state = "running"

    # ---- main thread ----
    def _resume(self, side):
        side.state = "running"
        if side.thread is None:
            mod = TRACED.get(side.stage["t"])
            saved = mod.TRACE if mod else None
            if mod:
                mod.TRACE = side.trace                # the card reads it once, at entry
            side.thread = threading.Thread(target=self._body, args=(side,), daemon=True)
            side.thread.start()
            self.main.acquire()
            if mod:
                mod.TRACE = saved
        else:
            side.sem.release()
            self.main.acquire()

    def _teardown(self):
        for side in self.sides:
            if side.state == "paused":
                side.abort = True
                side.sem.release()
                side.thread.join()

    def run(self):
        cur = self.sides[0] if self.sides[0].size > 0 else self.sides[1]
        try:
            while True:
                self._resume(cur)
                oth = self.other(cur)
                if cur.state == "paused":             # its slice ended: hand over
                    self.switches += 1
                    cur = oth
                    continue
                res = cur.result                      # cur is done
                if res[0] == "error":
                    raise res[1]
                if res[0] == "found":
                    self.m.k = cur.k
                    return res[1]
                if oth.size > 0 and oth.state in ("new", "paused"):
                    cur = oth                         # runs alone from here: no more switching
                    continue
                return None
        finally:
            self._teardown()
            self._record()

    def _record(self):
        if TRACE is None:
            return
        sides = []
        for sd in self.sides:
            res = sd.result[0] if sd.result else "not run"
            per_type = optypes.per_type(sd.stage, sd.trace, sd.ops, sd.tests, self.N) if sd.ops or sd.trace else {}
            sides.append({"t": sd.stage["t"], "size": sd.size, "ops": sd.ops, "tests": sd.tests,
                          "hits": sd.hits, "slices": sd.slices, "end": res, "per_type": per_type,
                          "phases": dict(sd.trace["ops"]) if sd.trace and "ops" in sd.trace else None,
                          "charges": sd.charges})
        TRACE.update(sides=sides, switches=self.switches,
                     winner=next((sd.idx for sd in self.sides if sd.result and sd.result[0] == "found"), None))

def lamp_race(N, s, m):
    validate(s)
    return _Race(N, s, m).run()
