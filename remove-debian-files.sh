#!/usr/bin/env bash
# remove-debian-files.sh
# Run once from your crosvm root after unzipping the overlay:
#
#   cd ~/crosvm
#   unzip crosvm-asahi-refactor.zip
#   bash remove-debian-files.sh
#
# Removes all Debian/multi-arch/Windows/riscv64/x86_64 files that are no
# longer needed for a native aarch64 Asahi Fedora Remix build.

set -euo pipefail

CROSVM_ROOT="${1:-$(pwd)}"

if ! grep -q 'name = "crosvm"' "$CROSVM_ROOT/Cargo.toml" 2>/dev/null; then
    echo "ERROR: Run this from your crosvm root, or pass it as an argument."
    echo "Usage: bash remove-debian-files.sh [/path/to/crosvm]"
    exit 1
fi

echo "Removing Debian/multi-arch/Windows/riscv64/x86_64 files from: $CROSVM_ROOT"

d() {
    local t="$CROSVM_ROOT/$1"
    if [[ -e "$t" ]]; then
        rm -rf "$t"
        echo "  removed: $1"
    fi
}

# Debian apt-get dependency scripts
d tools/deps/install-x86_64-debs
d tools/deps/install-x86_64-other
d tools/deps/install-aarch64-debs
d tools/deps/install-riscv64-debs
d tools/deps/install-riscv64-other
d tools/deps/install-mingw64-debs
d tools/deps/install-mingw64-other

# Superseded setup scripts (replaced by unified tools/setup)
d tools/setup-aarch64

# x86_64-only VM launcher
d tools/x86vm

# Debian-specific cargo cross-compile config
d .cargo/config.debian.toml

# Windows-only Rust crates
d win_audio
d win_util

# Removed architecture crates
d riscv64
d x86_64

echo ""
echo "Done. Next steps:"
echo "  ./tools/setup                        # install dnf deps + Rust toolchain"
echo "  cargo build --features=all-aarch64"
echo "  ./tools/run_tests"
