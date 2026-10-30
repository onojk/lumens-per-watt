"""The judge's pins (design docs/planning/arrangement_lamps.md §6; Novelty Plan phase 2, "the judge locked away").

The judge is every file that decides a score: the lampcore binary and its source, the Python twin and meter, the op
types and prices, the frozen fitness definitions, the scoring harness, tools/sealed_run.sh and this file, and the
predictions themselves. Their sha256s are pinned in predictions/<id>.md, in a block appended after the sealed text:

    ## Judge pins, pin <n> (...)
    <!-- judge-pins begin -->
    <sha256>  <path>
    pending  <path>                    a judge file not yet written: check refuses until a later pin names its hash
    <sha256>  @predictions             the predictions' own text above the first "## Judge pins" heading
    <!-- judge-pins end -->

A later pin (a new block, appended, never an edit of an earlier one) supersedes the earlier ones; check reads the last.
  python3 tools/judge.py pin EXPERIMENT [--add PATH ...] [--pending PATH ...]
                                                                prints the next pin block (does not write the file):
                                                                JUDGE below, plus each --add (the experiment's own
                                                                judge files, e.g. its scoring harness), plus pending
  python3 tools/judge.py check EXPERIMENT [--allow-pending]     exit 0 if every pin matches, 1 otherwise (lists each);
                                                                --allow-pending: pending entries pass (the search
                                                                sandbox only; a scored run never passes it)
  python3 tools/judge.py paths EXPERIMENT                       the last pin's paths, one per line (for the sandbox)
check also refuses when LAMPCORE is set in the environment: fastlamps.BIN would then not be the pinned binary.
Run from anywhere inside the repo; paths are relative to the repo root."""
import hashlib, os, re, subprocess, sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                      cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
HEAD = "## Judge pins"
BEGIN, END = "<!-- judge-pins begin -->", "<!-- judge-pins end -->"

JUDGE = [
    "lampcore/target/release/lampcore",          # the binary fastlamps.BIN runs
    "lampcore/Cargo.toml", "lampcore/Cargo.lock",
    "lampcore/src/*.rs",                          # every source file, expanded at pin time
    "evolve/lamps.py", "evolve/arr.py", "evolve/fastlamps.py", "evolve/optypes.py",
    "evolve/qs.py", "evolve/cfrac.py", "evolve/ecm.py", "evolve/race.py", "evolve/ledger.py", "evolve/blockflash.py",
    "evolve/calibrate.json", "opclass/opclass_v1.json",
    "reviews/growth_fitness_rho.md", "reviews/growth_fitness.md",
    "tools/sealed_run.sh", "tools/judge.py", "tools/search_sandbox.sh",
]

def sha(path):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, path), "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def pred_path(exp):
    if not re.fullmatch(r"[A-Za-z0-9._-]+", exp):
        sys.exit("experiment ID must be [A-Za-z0-9._-]+")
    return os.path.join(ROOT, "predictions", exp + ".md")

def body_sha(exp):
    """sha256 of the predictions' text above the first pin heading (the sealed text; pins are appended below it),
    trailing blank lines ignored: appending a pin, with or without a blank line before it, leaves the hash as it was."""
    text = open(pred_path(exp), "rb").read()
    i = text.find(("\n" + HEAD).encode())
    return hashlib.sha256((text if i < 0 else text[:i + 1]).rstrip(b"\n") + b"\n").hexdigest()

def expand(pats):
    import glob
    out = []
    for p in pats:
        hits = sorted(os.path.relpath(x, ROOT) for x in glob.glob(os.path.join(ROOT, p)))
        if not hits:
            sys.exit(f"judge file missing: {p}")
        out += hits
    return out

def last_pin(exp):
    text = open(pred_path(exp)).read()
    blocks = re.findall(re.escape(BEGIN) + r"\n(.*?)" + re.escape(END), text, re.S)
    if not blocks:
        return None, 0
    pins = []
    for line in blocks[-1].strip().splitlines():
        h, p = line.split(None, 1)
        pins.append((h, p.strip()))
    return pins, len(blocks)

def cmd_pin(exp, add, pending):
    _, n = last_pin(exp)
    rows = [(sha(p), p) for p in expand(JUDGE + add)] + [("pending", p) for p in pending] + [(body_sha(exp), "@predictions")]
    w = max(len(h) for h, _ in rows)
    print(f"{HEAD}, pin {n + 1}\n")
    print(BEGIN)
    for h, p in rows:
        print(f"{h:<{w}}  {p}")
    print(END)

def cmd_check(exp, allow_pending=False):
    pins, n = last_pin(exp)
    if pins is None:
        print(f"JUDGE: no pins in predictions/{exp}.md")
        return 1
    bad = []
    if "LAMPCORE" in os.environ:
        bad.append(f"LAMPCORE is set ({os.environ['LAMPCORE']}): the meter would not run the pinned binary")
    for h, p in pins:
        if h == "pending":
            if allow_pending:
                print(f"JUDGE: {p} pending (allowed: search_sandbox.sh only)")
                continue
            bad.append(f"{p}: pending (not yet pinned)")
            continue
        try:
            now = body_sha(exp) if p == "@predictions" else sha(p)
        except OSError as e:
            bad.append(f"{p}: missing ({e.strerror})")
            continue
        if now != h:
            bad.append(f"{p}: sha256 {now[:16]}… does not match the pin {h[:16]}…")
    for b in bad:
        print("JUDGE MISMATCH:", b)
    print(f"JUDGE: pin {n}, {len(pins)} entries: " + ("ok" if not bad else f"{len(bad)} failed"))
    return 1 if bad else 0

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("pin", "check", "paths"):
        sys.exit(__doc__)
    if a[0] == "pin":
        opt = lambda o: [a[i + 1] for i, x in enumerate(a) if x == o]
        cmd_pin(a[1], opt("--add"), opt("--pending"))
    elif a[0] == "check":
        sys.exit(cmd_check(a[1], "--allow-pending" in a))
    else:
        pins, _ = last_pin(a[1])
        print("\n".join(p for _, p in pins or [] if p != "@predictions"))
