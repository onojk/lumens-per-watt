"""Checks that the debug = 1 build has the same code as the frozen release build (procedure, section 4): every
function body, disassembled and normalised (addresses, immediates of 4+ hex digits, symbol names and comments
removed), compared as a multiset. Run from the repo root: python3 opclass/text_identity.py > opclass/text_identity.out"""
import collections, re, subprocess
def bodies(path):
    txt = subprocess.run(["objdump", "-d", "--no-show-raw-insn", path], capture_output=True, text=True, check=True).stdout
    out, cur, body = [], None, []
    for line in txt.splitlines():
        m = re.match(r'^([0-9a-f]+) <(.*)>:$', line.strip())
        if m:
            if cur is not None:
                out.append((cur, "\n".join(body)))
            cur, body = m.group(2), []
            continue
        if cur and ':' in line:
            ins = line.split(':', 1)[1].strip()
            ins = re.sub(r'#.*$', '', ins); ins = re.sub(r'0x[0-9a-f]+', 'H', ins)
            ins = re.sub(r'\b[0-9a-f]{4,}\b', 'H', ins); ins = re.sub(r'<[^>]*>', '<S>', ins)
            body.append(ins.strip())
    if cur is not None:
        out.append((cur, "\n".join(body)))
    return out
A, B = bodies("opclass/bin/lampcore-release"), bodies("opclass/bin/lampcore-debug1")
ca, cb = collections.Counter(b for _, b in A), collections.Counter(b for _, b in B)
na, nb = {b: n for n, b in A}, {b: n for n, b in B}
print(f"functions: release {len(A)}, debug = 1 {len(B)}")
print(f"bodies only in release: {sum((ca - cb).values())} {[na[b] for b in ca - cb]}")
print(f"bodies only in debug = 1: {sum((cb - ca).values())} {[nb[b] for b in cb - ca]}")
for b in ca - cb:
    print("release", na[b], "\n  " + b.replace("\n", "\n  "))
for b in cb - ca:
    print("debug = 1", nb[b], "\n  " + b.replace("\n", "\n  "))
