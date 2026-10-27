"""Work-trace prototype (IDEAS I-044; information only, Python card only, read-only hook qs.WORKTRACE): one polynomial
of one 96-bit map number, as motion on the sieve line. x = sieve position (or the candidate's position for
per-candidate work), y = op order (time runs down). Each op is a mark coloured by its charged type; uncharged work grey.
Cells: the reference (2'a), 2'b, and 2'b+pp3 (+0) drawn under the uncorrected meter (the free 2's writes uncharged,
as before 6031239). Checks that the run's op count is identical with the hook on and off.
  Also the reference since Oct 27 (2'b; no pp, so the corrected meter changes nothing in it). All pictures share one y axis.
  python3 worktrace.py -> worktrace_<cell>.png, worktrace.json (event counts), stdout"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import partition as P, sizescale2 as S2, qs, lamps
from lctest import ref

TARGET = 1                       # the run's second polynomial: the first with a Gray switch
N = S2.map_nums(96)[0][0]
g0 = dict(ref(96), goff=1)
CELLS = [("2'a (reference)", "2a", dict(g0), "corrected"),
         ("2'b", "2b", dict(g0, confirm="root"), "corrected"),
         ("2'b+pp3 +0, uncorrected meter", "2b_pp3_uncorrected", dict(g0, confirm="root", pp=3), "uncorrected"),
         ("the reference since Oct 27 (2'b), corrected meter", "reference_2b", dict(g0, confirm="root"), "corrected")]
COL = {"setup_gray": "#8c6bb1", "sieve_scan": "#4daf4a", "sieve_update": "#1f78b4", "word": "#ff7f00",
       "root_test": "#e31a1c", "confirm_td": "#a6761d", "hash": "#f781bf", "lp_small": "#66c2a5", "lp_full": "#1b9e77",
       "sieve_scan:free2": "#4daf4a"}
summary = {}
traces = []
for title, tag, g, meter in CELLS:
    qs.WORKTRACE = None
    ops0, f0 = lamps.run([g], N, P.QS_CAP)
    qs.WORKTRACE = {"target": TARGET, "meter": meter}
    ops1, f1 = lamps.run([g], N, P.QS_CAP)
    wt = qs.WORKTRACE; qs.WORKTRACE = None
    assert (ops0, f0) == (ops1, f1), "the hook changed the run"
    traces.append((title, tag, wt))
YMAX = max(len(wt["events"]) for _, _, wt in traces)     # one y axis for every picture
for title, tag, wt in traces:
    ev = wt["events"]
    fig, ax = plt.subplots(figsize=(11.5, 11), dpi=110)
    groups = {}
    for i, (x, t, c) in enumerate(ev):
        key = t if c else "uncharged"
        groups.setdefault(key, ([], []))
        groups[key][0].append(x); groups[key][1].append(i)
    order = ["setup_gray", "sieve_scan", "sieve_update", "word", "root_test", "confirm_td", "hash", "lp_small", "lp_full",
             "sieve_scan:free2", "uncharged"]
    for k in order:
        if k in groups:
            xs, ys = groups[k]
            ax.scatter(xs, ys, s=1.2, c="#9e9e9e" if k == "uncharged" else COL[k], linewidths=0,
                       label=f"{'uncharged (free-2 writes)' if k == 'uncharged' else k} ({len(xs):,})")
    ax.set_xlim(-10, wt["width"] + 10)
    ax.set_ylim(YMAX * 1.01, -YMAX * 0.01)
    ax.set_xlabel(f"sieve position (width {wt['width']:,}; candidates at x = their position)")
    ax.set_ylabel("op order (time runs down)")
    ax.set_title(f"{title}: one polynomial, 96-bit map number 0, polynomial {TARGET}\n{len(ev):,} ops; F = {wt['F']}; "
                 f"{len(wt['cand'])} candidates", fontsize=10)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), markerscale=6, fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(f"worktrace_{tag}.png")
    plt.close(fig)
    cnt = {}
    for _, t, c in ev:
        k = t if c else "uncharged"
        cnt[k] = cnt.get(k, 0) + 1
    summary[tag] = {"ops_traced": len(ev), "by_type": cnt, "candidates": len(wt["cand"]), "width": wt["width"],
                    "run_ops_unchanged": True}
    print(tag, len(ev), cnt, flush=True)
json.dump({"N": str(N), "target": TARGET, "cells": summary}, open("worktrace.json", "w"), indent=1)
