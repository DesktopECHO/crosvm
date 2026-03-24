# crosvm — Asahi Fedora Remix Refactor

This directory contains the files that have been changed or added to refactor
crosvm for **native aarch64 builds on Asahi Fedora Remix on Apple Silicon**.

All Debian-specific package management, multi-arch cross-compilation toolchains,
x86_64, riscv64, and Windows (mingw64/wine) code paths have been removed.

---

## Quick Start

```bash
# Install all build dependencies (replaces the old Debian apt-get setup)
./tools/setup

# Build crosvm natively for aarch64
cargo build --features=all-aarch64

# Run tests
./tools/run_tests

# Enter dev container (Fedora-based)
./tools/dev_container
```

---

## What Changed

### Removed files (delete from your tree)

| Path | Reason |
|---|---|
| `tools/deps/install-x86_64-debs` | x86_64 Debian packages |
| `tools/deps/install-x86_64-other` | x86_64 Rust/cargo tools |
| `tools/deps/install-aarch64-debs` | aarch64 cross-compile Debian packages |
| `tools/deps/install-riscv64-debs` | riscv64 Debian packages |
| `tools/deps/install-riscv64-other` | riscv64 Rust target |
| `tools/deps/install-mingw64-debs` | Windows/Wine Debian packages |
| `tools/deps/install-mingw64-other` | Windows/Wine setup |
| `tools/setup-aarch64` | Merged into `tools/setup` |
| `tools/x86vm` | x86_64 test VM launcher |
| `tools/impl/dev_container/Dockerfile.base` (old) | Debian base image |
| `win_audio/` | Windows audio crate |
| `win_util/` | Windows utilities crate |
| `riscv64/` | riscv64 arch crate |
| `x86_64/` | x86_64 arch crate |
| `.cargo/config.debian.toml` | Debian cross-compile config |

### New/replaced files (apply from this directory)

| Path | What changed |
|---|---|
| `tools/deps/install-aarch64-rpms` | **New** — `dnf` equivalent of all Debian deps |
| `tools/deps/install-aarch64-other` | Stripped mingw64/riscv64/android Rust targets |
| `tools/deps/install_rutabaga_gfx_deps` | Native aarch64 only; removed x86_64 cross paths |
| `tools/setup` | Single unified setup script (replaces setup + setup-aarch64) |
| `tools/impl/dev_container/Dockerfile.base` | `FROM fedora:latest`, `dnf` installs |
| `tools/impl/dev_container/Dockerfile` | Removed mingw64/riscv64/wine install steps |
| `tools/impl/dev_container/Makefile` | `--platform linux/arm64`, Fedora image names |
| `.devcontainer/devcontainer.json` | Points to new Fedora-based image |
| `.cargo/config.toml` | Removed riscv64/windows linker/runner/pkg-config entries |
| `tools/impl/test_config.py` | `BUILD_FEATURES` aarch64 only; removed win64/wine/riscv64 |
| `tools/impl/util.py` | `SHORTHANDS` aarch64 only; `dnf` in `ensure_packages_exist` |
| `tools/impl/testvm.py` | Removed x86_64 `Arch` type; Fedora EFI path |
| `tools/impl/testvm/cloud_init.yaml` | `dnf` packages; removed x86_64 conditionals |
| `tools/impl/testvm/Makefile` | aarch64 only; Fedora Cloud image source |
| `tools/presubmit` | `PLATFORMS = Literal["aarch64"]` only |
| `tools/run_tests` | Removed win64/wine/riscv64 imports and logic |
| `Cargo.toml` | Removed `win_audio`, `win_util`, `riscv64`, `x86_64` from workspace |

---

## Package Name Mapping (Debian → Fedora)

| Debian | Fedora |
|---|---|
| `libcap-dev` | `libcap-devel` |
| `libdbus-1-dev` | `dbus-devel` |
| `libdrm-dev` | `libdrm-devel` |
| `libepoxy-dev` | `libepoxy-devel` |
| `libglib2.0-dev` | `glib2-devel` |
| `libslirp-dev` | `libslirp-devel` |
| `libssl-dev` | `openssl-devel` |
| `libva-dev` | `libva-devel` |
| `libwayland-dev` | `wayland-devel` |
| `libxext-dev` | `libXext-devel` |
| `ncat` | `nmap-ncat` |
| `python3-black` | `python3-black` |
| `qemu-efi-aarch64` | `edk2-aarch64` |
| `qemu-system-aarch64` | `qemu-system-aarch64` |
| `wayland-protocols` | `wayland-protocols-devel` |
| `libavcodec-dev` / `libavutil-dev` / `libswscale-dev` | `ffmpeg-free-devel` |
| `cloud-image-utils` | `cloud-utils` |

---

## Dev Container

The dev container is now based on `fedora:latest` instead of `debian:testing-slim`.
The image is tagged `gcr.io/crosvm-infra/crosvm_dev_asahi`.

To rebuild the container locally:
```bash
cd tools/impl/dev_container
make dev
```

---

## Notes

- **No cross-compilation** — this build targets only `aarch64-unknown-linux-gnu`
  (the native host on Apple Silicon). The Debian multi-arch dpkg setup, QEMU
  user-mode emulation runners, and cross-linker wrapper scripts are gone.
- **KVM** — Asahi Linux ships KVM support for Apple Silicon. Ensure your kernel
  has `CONFIG_KVM_ARM_HOST=y` and your user is in the `kvm` group.
- **EFI firmware** — test VMs use `/usr/share/edk2/aarch64/QEMU_EFI.fd`
  (from the `edk2-aarch64` RPM) instead of the Debian `qemu-efi-aarch64` path.
