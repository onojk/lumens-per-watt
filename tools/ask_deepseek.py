#!/usr/bin/env python3
"""Ask DeepSeek (its OpenAI-compatible chat endpoint) for a review round.

  tools/ask_deepseek.py PROMPT_FILE [--round NN] [--dry-run]

The prompt sent is the card's parameter sheet (reviews/card_params.md) followed by PROMPT_FILE. A system line asks
for English replies with the working shown. The prompt as sent is saved to reviews/deepseek_rNN.prompt.md and the
reply to reviews/deepseek_rNN.md (NN: --round, or the next free number above the existing files and above 53, the
last hand-relayed round), and the reply is printed. Nothing is committed here.

Environment: DEEPSEEK_API_KEY (required; never written anywhere), DEEPSEEK_MODEL (default deepseek-v4-pro),
DEEPSEEK_BASE_URL (default https://api.deepseek.com; the request goes to <base>/chat/completions).
Standard library only.
"""
import argparse, datetime, json, os, re, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(ROOT, "reviews")
FLOOR = 53                     # DeepSeek rounds up to 53 were relayed by hand (NOTES.md); the first automated round is 54
SYSTEM = ("Reply in English. Show your working: state every input you use and where it comes from (the parameter "
          "sheet, the prompt, or your own assumption, labelled as such), and the arithmetic step by step. Use the "
          "card's measured parameters from the sheet; do not invent parameters. If a needed value is missing, say "
          "so instead of guessing.")

def next_round():
    nums = [int(m.group(1)) for f in os.listdir(REV) if (m := re.fullmatch(r"deepseek_r(\d+)\.md", f))]
    return max(nums + [FLOOR]) + 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt_file")
    ap.add_argument("--round", type=int)
    ap.add_argument("--dry-run", action="store_true", help="build and save the prompt, send nothing")
    a = ap.parse_args()
    nn = a.round or next_round()
    out, pout = os.path.join(REV, f"deepseek_r{nn}.md"), os.path.join(REV, f"deepseek_r{nn}.prompt.md")
    if os.path.exists(out):
        sys.exit(f"{out} exists; pick another --round")
    sheet = open(os.path.join(REV, "card_params.md")).read()
    body = open(a.prompt_file).read()
    user = sheet + "\n\n---\n\n" + body
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
    base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    with open(pout, "w") as f:
        f.write(f"<!-- round {nn}; model {model}; base {base}; {datetime.datetime.now().isoformat(timespec='seconds')} -->\n\n"
                f"## System\n\n{SYSTEM}\n\n## User\n\n{user}\n")
    if a.dry_run:
        print(f"dry run: prompt saved to {pout}")
        return
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        sys.exit("DEEPSEEK_API_KEY is not set (put it in your shell profile, not the repo)")
    req = urllib.request.Request(base + "/chat/completions", method="POST",
                                 data=json.dumps({"model": model, "messages": [{"role": "system", "content": SYSTEM},
                                                                              {"role": "user", "content": user}],
                                                  "stream": False}).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            resp = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode(errors='replace')[:2000]}")
    msg = resp["choices"][0]["message"]
    reply = msg.get("content") or ""
    with open(out, "w") as f:
        f.write(f"<!-- round {nn}; model {resp.get('model', model)}; prompt deepseek_r{nn}.prompt.md; usage {json.dumps(resp.get('usage', {}))} -->\n\n")
        if msg.get("reasoning_content"):
            f.write("## Reasoning (as returned)\n\n" + msg["reasoning_content"] + "\n\n## Reply\n\n")
        f.write(reply + "\n")
    print(reply)
    print(f"\n[saved {out} and {pout}]", file=sys.stderr)

if __name__ == "__main__":
    main()
