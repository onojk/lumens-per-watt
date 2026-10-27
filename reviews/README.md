# reviews/

This folder holds outside review rounds (DeepSeek; Grok when available) and the parameter sheet sent with every prompt.

## Files

- `deepseek_rNN.prompt.md`: the prompt as sent (system line plus user text).
- `deepseek_rNN.md`: the reply as returned (with the model's reasoning, when the API returns it).
- `card_params.md`: the card's parameter sheet, prepended to every prompt.

## Usage

```
tools/ask_deepseek.py <prompt-file> [--round NN] [--dry-run]
```

- The endpoint is DeepSeek's OpenAI-compatible chat API. The model comes from `DEEPSEEK_MODEL` (default `deepseek-v4-pro`) and the base URL from `DEEPSEEK_BASE_URL` (default `https://api.deepseek.com`).
- A system line asks for English replies with the working shown, and for no invented parameters.
- `--dry-run` builds and saves the prompt without sending anything.
- The tool commits nothing: commit the prompt and reply yourself (explicit `git add`), before any run they predict.

## The key

The key lives only in the environment, as `DEEPSEEK_API_KEY`, set in your shell profile (`~/.bashrc` or `~/.profile`). It never goes in the repo or any file the tool writes.

## The parameter sheet

`card_params.md` holds only measured values, each with its source (commit or file).
- It is updated whenever a measurement it quotes changes.
- Its "Last updated / card commit" line says which card the values describe.
- If a reviewer needs a value that isn't on the sheet, they should ask rather than estimate.

## Round numbering

The next round is one more than the highest round on record: the largest "round NN" in NOTES.md or `reviews/`, or NN in a `deepseek_rNN` file name. Hand-relayed rounds so far go up to 55, so the next automated round is 56. `--round` overrides this.

## Recording

Replies are recorded as given. The reviewer's corrections go in separate notes (in NOTES.md, next to the round), never into the reply file. A round's predictions count as sealed only if they were committed before the run they predict (PROTOCOL.md).
