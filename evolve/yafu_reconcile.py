"""Reconciling siqs() direct (10.5 ms per number, 20-number batches) with abs + QS alone (4.6 + 1.97 ms, 80-number
batches) at 96 bits, balanced band (information only, before baseline-yafu-qs is timed). Each expression on the 80
balanced numbers repeated k = 1, 2, 4 times in one batch (80 / 160 / 320 lines), median of 3, pinned core 2, Run B's
conditions. A least-squares line wall = a + b * lines gives the per-line cost b and the one-time cost a.
  python3 yafu_reconcile.py -> yafu_reconcile.json, stdout"""
import json, statistics, subprocess, sys, tempfile, time
import partition as P, sizescale2 as S2
from baseline_msieve import conditions, cool
from yafu_diag import YAFU

if __name__ == "__main__":
    bad = conditions()
    if bad:
        print("timing skipped: " + "; ".join(bad)); sys.exit(2)
    nums = [N for N, _, _ in S2.map_nums(96)[-P.PER_BAND:]]
    out = {}
    for f in ("abs(@)", "smallmpqs(@)", "siqs(@)"):
        pts = []
        for k in (1, 2, 4):
            ws = []
            for r in range(3):
                cool()
                t0 = time.perf_counter()
                subprocess.run(["taskset", "-c", "2", YAFU, f, "-threads", "1"], input="".join(f"{N}\n" for N in nums * k),
                               cwd=tempfile.mkdtemp(prefix="yr_"), capture_output=True, text=True, check=True)
                ws.append(time.perf_counter() - t0)
            pts.append((len(nums) * k, statistics.median(ws)))
        xs, ys = zip(*pts)
        mx, my = statistics.mean(xs), statistics.mean(ys)
        b = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x in xs)
        a = my - b * mx
        out[f] = {"points_s": pts, "per_line_ms": 1e3 * b, "one_time_ms": 1e3 * a}
        print(f"{f}: " + ", ".join(f"{n} lines {1e3 * w / n:.2f} ms/line" for n, w in pts)
              + f"; fit: per line {1e3 * b:.2f} ms, one-time {1e3 * a:.1f} ms", flush=True)
    json.dump(out, open("yafu_reconcile.json", "w"), indent=1)
