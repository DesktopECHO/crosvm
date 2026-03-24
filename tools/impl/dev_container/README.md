# Dev Container (Asahi Fedora Remix)

This directory contains the dev container for crosvm on **Asahi Fedora Remix (aarch64)**.

The container is split into two images:

- **`crosvm_dev_base_asahi`** — defined by `Dockerfile.base`
  Installs all RPM packages via `tools/deps/install-aarch64-rpms`.
  Update infrequently; only when RPM packages change.

- **`crosvm_dev_asahi`** — defined by `Dockerfile`
  Builds on top of the base image and installs Rust toolchains, cargo tools,
  and rutabaga_gfx dependencies.

## Updating the base image

Modify `tools/deps/install-aarch64-rpms`, uprev `base_version`, then:

```bash
make -C tools/impl/dev_container base
# Test locally with: ./tools/dev_container
# When satisfied, upload:
make -C tools/impl/dev_container upload_base
```

## Updating the dev image

Modify the relevant install scripts, uprev `version`, then:

```bash
make -C tools/impl/dev_container dev
# Stop any running container first:
./tools/dev_container --stop
# Test locally:
./tools/dev_container
# Upload:
make -C tools/impl/dev_container upload_dev
```

## Authentication

You need to be a Googler to upload containers. Authenticate via:

```bash
gcloud auth configure-docker gcr.io
```

## Notes

- The container targets `linux/arm64` only. There is no x86_64 or riscv64 variant.
- The Golang builder stage uses `docker.io/golang:latest` (multi-arch, resolves to arm64).
- All Debian/apt-get references have been replaced with Fedora/dnf equivalents.
