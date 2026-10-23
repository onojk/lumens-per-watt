"""Trace a genome's family line from lineage.jsonl.

  python3 ancestry.py                 # every run's final champion
  python3 ancestry.py L13-0412        # one named genome
"""
import json, sys

def load(path="lineage.jsonl"):
    rows = [json.loads(line) for line in open(path)]
    first = {}                  # name -> the row from the generation it was first scored
    last_champ = {}
    for r in rows:
        first.setdefault(r["name"], r)
        if r["champion"]:
            last_champ[r["run"]] = r["name"]
    return first, last_champ

def trace(name, first):
    """Follow the first parent back to a seed; note any second (crossover) parent."""
    line = []
    while name in first:
        r = first[name]
        line.append(r)
        if not r["parents"]:
            break
        name = r["parents"][0]
    return line

def show(name, first):
    line = trace(name, first)
    print(f"\n{name}: {len(line)} generations of ancestry, oldest first")
    for r in reversed(line):
        other = f" × {r['parents'][1]}" if len(r["parents"]) > 1 else ""
        print(f"  gen {r['born']:3d}  {r['name']:9s} {r['op']:13s} train N^{r['train']:.3f}"
              f"{other}\n             {r['describe']}")

if __name__ == "__main__":
    first, last_champ = load()
    names = sys.argv[1:] or list(last_champ.values())
    for n in names:
        show(n, first)
