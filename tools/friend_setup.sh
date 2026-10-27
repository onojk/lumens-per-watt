#!/usr/bin/env bash
# tools/friend_setup.sh [FOLDER]: one-time setup for a friend's machine (FRIEND.md). Linux and WSL; macOS works with
# a warning (no taskset, so timings are noisier). It:
#   1. checks git, Python 3 (with numpy) and Rust, and offers to install what is missing;
#   2. clones https://github.com/onojk/lumens-per-watt into FOLDER (default ~/lumens-per-watt), unless it is run from
#      inside a copy already, or that folder already holds one;
#   3. builds lampcore in release mode;
#   4. runs the quick self-test (evolve/ci_quick.py) and prints PASS or FAIL.
# sudo is used only by the system package manager, and the script says so and asks before each such step. No keys or
# accounts are needed; nothing is uploaded.
set -uo pipefail
REPO_URL=https://github.com/onojk/lumens-per-watt
say() { printf '\n== %s\n' "$*"; }
ask() { read -r -p "$1 [y/N] " a; [[ "$a" =~ ^[Yy] ]]; }
fail() { printf '\nFAIL: %s\n' "$*"; exit 1; }

os=$(uname -s)
wsl=no; grep -qi microsoft /proc/version 2>/dev/null && wsl=yes
say "System: $os$( [ $wsl = yes ] && echo ' (WSL)')"
[ "$os" = Darwin ] && echo "NOTE: on macOS there is no taskset, so runs cannot be pinned to one core; timings will be noisier."

pm=""
for c in apt-get dnf pacman zypper brew; do command -v $c >/dev/null && { pm=$c; break; }; done
pkg_install() {   # pkg_install <apt name> <dnf name> <pacman name> <brew name>
    case $pm in
        apt-get) echo "This step uses sudo (the package manager needs it): sudo apt-get install -y $1"
                 ask "Run it?" && sudo apt-get update && sudo apt-get install -y "$1" ;;
        dnf)     echo "This step uses sudo (the package manager needs it): sudo dnf install -y $2"
                 ask "Run it?" && sudo dnf install -y "$2" ;;
        pacman)  echo "This step uses sudo (the package manager needs it): sudo pacman -S --needed $3"
                 ask "Run it?" && sudo pacman -S --needed "$3" ;;
        zypper)  echo "This step uses sudo (the package manager needs it): sudo zypper install -y $1"
                 ask "Run it?" && sudo zypper install -y "$1" ;;
        brew)    echo "Installing with Homebrew (no sudo): brew install $4"
                 ask "Run it?" && brew install "$4" ;;
        *)       return 1 ;;
    esac
}

say "1. Tools"
command -v git >/dev/null || pkg_install git git git git || fail "git is needed; please install it and run this again"
command -v python3 >/dev/null || pkg_install python3 python3 python python || fail "Python 3 is needed; please install it and run this again"
if ! python3 -c "import numpy" 2>/dev/null; then
    echo "Python's numpy package is missing."
    if [ "$pm" = brew ] || [ -z "$pm" ]; then
        ask "Install it for your user only with pip (no sudo)?" && python3 -m pip install --user numpy
    else
        pkg_install python3-numpy python3-numpy python-numpy numpy
    fi
    python3 -c "import numpy" 2>/dev/null || fail "numpy is still missing"
fi
[ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
if ! command -v cargo >/dev/null; then
    echo "Rust is missing. The official installer (rustup, from https://rustup.rs) installs it for your user only, no sudo."
    ask "Download and run the Rust installer?" || fail "Rust is needed"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y || fail "the Rust installer failed"
    . "$HOME/.cargo/env"
fi
command -v cc >/dev/null || command -v gcc >/dev/null || pkg_install build-essential gcc base-devel gcc || fail "a C linker (gcc) is needed to build Rust programs"
echo "git $(git --version | cut -d' ' -f3), $(python3 --version), numpy $(python3 -c 'import numpy; print(numpy.__version__)'), $(cargo --version)"

say "2. The repository"
here=$(cd "$(dirname "$0")/.." 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$here" ] && [ -f "$here/lampcore/Cargo.toml" ]; then
    dir=$here; echo "Using the copy this script came from: $dir"
else
    dir=${1:-$HOME/lumens-per-watt}
    if [ -f "$dir/lampcore/Cargo.toml" ]; then
        echo "Using the existing copy in $dir (run 'git -C $dir pull' to update it)"
    else
        git clone "$REPO_URL" "$dir" || fail "could not download the repository"
    fi
fi
cd "$dir" || fail "cannot enter $dir"
echo "Commit: $(git rev-parse --short HEAD)"

say "3. Building lampcore (a few minutes the first time)"
(cd lampcore && cargo build --release) || fail "the build failed"

say "4. Self-test"
if (cd evolve && python3 ci_quick.py); then
    printf '\nPASS: this machine is ready. Next: tools/friend_run.sh <run-name> (see FRIEND.md).\n'
else
    fail "the self-test found a mismatch; please send the text above back unchanged"
fi
