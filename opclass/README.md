# op-class v1: step 2 (counts and weights)

Procedure: [`reviews/opclass_procedure.md`](../reviews/opclass_procedure.md) (ADOPTED Oct 27; robust-rule option (b)).
**Nothing here is priced.** No break-even, no op-class ratio for any cell and no robust ratio under the new rule are
computed until the user says "step 3".

## Step 2.1: frozen before any count (this commit)

**Toolchain** (procedure, section 3): rustc 1.95.0 (59807616e 2026-04-14), cargo 1.95.0 (f2d3ce0bd 2026-03-21);
x86-64 baseline target (no `target-cpu`, no `target-feature`); `[profile.release]` opt-level 3, no LTO, default
codegen units; `cargo build --release --locked`, no environment flags.
`lampcore/Cargo.lock` sha256 `3fe5a57d381e98ac6cd19fb5857f9e327d3327818ccb8c7609513b3d267da596`.
Source: `lampcore/src` as in this commit (unchanged since 6031239, the free-2 meter correction).

**Binaries** (kept in `opclass/bin/`, gitignored; the hashes are the record):

| file | built with | sha256 |
|---|---|---|
| `opclass/bin/lampcore-release` | `cargo build --release --locked` (lampcore/target/release) | `1505efbffb20002326753d23a668d1c15f77a53d2b5577825a631330ca855a79` |
| `opclass/bin/lampcore-debug1` | the same with `CARGO_PROFILE_RELEASE_DEBUG=1` (line tables for callgrind) | `b5b8dc6aad3d24a7a9f55b60bec9cca033852392c3ce781622ae02c3e202f332` |

**Code identity, debug = 1 against release** (`text_identity.py`, `text_identity.out`): all 1,144 function bodies are
identical after normalising addresses, symbol names and hash suffixes, **except the C `main` shim**. Rust's
`fn main` is a separate, identical body. The shim differs by one instruction, a `movzbl` load of the
`.debug_gdb_scripts` marker byte, and runs once per process. A whole-file `.text` hash differs only because
functions are laid out at different addresses. Counting runs the debug = 1 binary under callgrind, for its line
tables. Its card code is the release binary's code.

**Line map** (`linemap.tsv`, checked by `check_map.py`): ranges tile every line of `lampcore/src/*.rs`
(2,843 lines) exactly once. Classes: the TYPE_ORDER types, `meter`, `uncharged:card`, `uncharged:harness`,
`@caller`, `decl`. Attribution rules R1–R6 and the judgement calls are in the file's header.

**Input set** (`inputs.json`, `inputs/*.in`, built by `make_inputs.py`; sha256 per input in the manifest):
- A: the qs reference (2′a: reference genes, goff = 1) and 2′b, on all map numbers at 72, 84 and 96 (480 / 560 / 640).
- B: the reference pipelines (td, rho, p−1, ecm, qs with budgets "(d) new winner, new budgets" and the 2′a qs
  stage) on all map numbers at 54, 72, 84 and 96.
- C, supplementary, for classes no reference run charges:
  - ecm alone, and p−1 with stage 2 (gene c), each on 96 map numbers at 54 and 72;
  - sq, ps (lump mode) and cfrac (lump mode), on 48 / 48 / 24 map numbers at 54;
  - td alone, on 16 map numbers at 54;
  - qs with the ledger check (gene check), on 48 map numbers at 72.

**Coverage** (`coverage.py`, `coverage.out`: op counts by class from the release binary's `--types`, no Ir, no
prices). Every TYPE_ORDER type ends nonzero except setup_full and confirm_full, which no card charges
(procedure, section 2). The smallest counts are setup_mul 1,870 and setup_euclid_N 2,775 (ecm setup). Their
stability is reviewed after counting, as section 4 requires.

## Step 2.2 onward

Two independent derivations, a comparison, the static cross-check, then the frozen weights "op-class v1". These
are recorded below and in NOTES when done.
