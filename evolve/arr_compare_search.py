"""Compare two arrangement-v1 search runs (the user's ruling, Oct 30: the void run 39ffaf5 against its re-run under the
hardened sandbox, same seed and settings). Not a judge file; reads the two search records and the two sealed-run logs.

Compared, in this order, stopping at the first difference: the training numbers; rho's records; the budget; the
number of evaluations; the selected genome; per pair (in the record's order): the final genome, its fitness, its
search entry and its per-number training records; then the sweep log lines (timestamps stripped). Fields the old
code did not write are not compared, and are listed: the per-number "term" (the early-exit audit), the "invalid"
flag, and the evaluated-genome list (absent from 39ffaf5's record). When both records hold an evaluated-genome list
(the theta reruns, Oct 30), it is compared too, in order, after the pairs and before the sweep log, termination and
invalid flag included (both runs wrote them).
  python3 arr_compare_search.py OLD_RECORD OLD_LOG NEW_RECORD NEW_LOG   -> "identical" or the first difference"""
import json, re, sys

NEW_ONLY = {"term", "why", "invalid"}

def strip(x):
    if isinstance(x, dict):
        return {k: strip(v) for k, v in x.items() if k not in NEW_ONLY}
    if isinstance(x, list):
        return [strip(v) for v in x]
    return x

def first_diff(a, b, path="$"):
    if type(a) != type(b):
        return f"{path}: type {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return f"{path}: keys {sorted(set(a) ^ set(b))} differ"
        for k in a:
            d = first_diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    return None if a == b else f"{path}: {a!r} vs {b!r}"

def sweeps(log):
    return [re.sub(r"^\[\s*\d+s\]\s*", "", l.rstrip()) for l in open(log) if "sweep" in l or "best overall" in l]

def main(old_rec, old_log, new_rec, new_log):
    a, b = json.load(open(old_rec)), json.load(open(new_rec))
    order = ["numbers", "rho", "budget", "evaluations", "best", "pairs"]
    for k in order:
        if k == "pairs":
            if list(a[k]) != list(b[k]):
                return f"pairs: the pair lists differ ({list(a[k])} vs {list(b[k])})"
            for name in a[k]:
                for part in ("genome", "fitness", "search", "dropped_at", "records"):
                    if part not in a[k][name] and part not in b[k][name]:
                        continue
                    d = first_diff(strip(a[k][name].get(part)), strip(b[k][name].get(part)), f"pairs.{name}.{part}")
                    if d:
                        return d
            continue
        d = first_diff(strip(a.get(k)), strip(b.get(k)), k)
        if d:
            return d
    if "evaluated" in a and "evaluated" in b:
        d = first_diff(a["evaluated"], b["evaluated"], "evaluated")
        if d:
            return d
    la, lb = sweeps(old_log), sweeps(new_log)
    for i, (x, y) in enumerate(zip(la, lb)):
        if x != y:
            return f"sweep log line {i}: {x!r} vs {y!r}"
    if len(la) != len(lb):
        return f"sweep log: {len(la)} vs {len(lb)} lines"
    return None

if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    d = main(*sys.argv[1:])
    both = all("evaluated" in json.load(open(p)) for p in (sys.argv[1], sys.argv[3]))
    print("compared: training numbers, rho's records, budget, evaluation count, selected genome, every pair's final genome, "
          "fitness, search entry and per-number training records, " + ("the evaluated-genome list, " if both else "")
          + "and the sweep log; not compared: per-number termination and the invalid flag in the pairs"
          + ("" if both else ", and the evaluated-genome list (not in both records)"))
    print("identical" if d is None else f"FIRST DIFFERENCE: {d}")
