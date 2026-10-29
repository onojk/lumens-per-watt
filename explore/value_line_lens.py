"""Value-line lens, "k of n" (the user's "Seven of Nine" card, stage 1, Oct 28): an illumination-map panel.
VISUALIZATION ONLY: never fitness, never in a charged path, imported by nothing in evolve/ or lampcore.
Dot "k of n" sits at k/n on [0, 1]. Tower N's dot k collides with a smaller tower iff gcd(k, N) > 1; the lowest dot
underneath is in tower n' = N / gcd(k, N) and carries the tag "k/gcd of n'". The panel draws towers 1..N-1 in grey,
tower N on top (fresh ground blue, collisions ember), and each collision's dashed drop to the tag it lands on.
The counts are counted dot by dot from gcd; phi(N) is never computed or used here (it is the answer, not an input).
  python3 value_line_lens.py [N] -> value_line_lens_<N>.png, stdout (the collision list)"""
import math, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def collisions(N):
    """[(k, g, tag_k, tag_n)] for k = 1..N with g = gcd(k, N) > 1: k of N lands on tag_k of tag_n."""
    out = []
    for k in range(1, N + 1):
        g = math.gcd(k, N)
        if g > 1:
            out.append((k, g, k // g, N // g))
    return out

def panel(N, path):
    hit = collisions(N)
    hk = {k for k, *_ in hit}
    fig, ax = plt.subplots(figsize=(16, 9.6), dpi=100)
    xs, ys = zip(*[(k / n, n) for n in range(1, N) for k in range(1, n + 1)])
    ax.scatter(xs, ys, s=3, c="0.75", lw=0)
    fresh = [k for k in range(1, N + 1) if k not in hk]
    ax.scatter([k / N for k in fresh], [N] * len(fresh), s=12, c="#8cb3e6", lw=0)
    for k, g, tk, tn in hit:
        x = k / N
        ax.plot([x, x], [N, tn], ls="--", lw=0.7, c="#e0551b")
        ax.scatter([x, x], [N, tn], s=40, c="#e0551b", lw=0, zorder=3)
        ax.annotate(f"{tk} of {tn}", (x, tn), textcoords="offset points", xytext=(0, -11), ha="center", fontsize=7,
                    color="#b03a0e")
    ax.set_xlabel("value k/n (0 to 1)"); ax.set_ylabel("tower n")
    ax.set_title(f"Tower {N} over towers 1-{N - 1}: {len(hit)} collisions (ember), {len(fresh)} on fresh ground")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)
    return hit, fresh

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 77
    hit, fresh = panel(N, f"value_line_lens_{N}.png")
    print(f"N = {N}: k = 1..{N}: {len(fresh)} on fresh ground, {len(hit)} collisions (counted by gcd)")
    print("collisions: " + ", ".join(f"{k} of {N} -> {tk} of {tn}" for k, g, tk, tn in hit))
