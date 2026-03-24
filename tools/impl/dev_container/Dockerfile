# syntax=docker/dockerfile:1.11.1
# Copyright 2025 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Development container for crosvm on Asahi Fedora Remix (aarch64).
# Provides all dependencies for native aarch64 builds only.
# Windows, riscv64, and x86_64 cross-compilation paths have been removed.
#
# See Makefile for build instructions.

ARG BASE_VERSION

# Build catapult dashboard upload tool
FROM docker.io/golang:latest AS gobuilder
WORKDIR /root/
RUN git clone https://fuchsia.googlesource.com/infra/infra
WORKDIR /root/infra/cmd/catapult
RUN go build

FROM gcr.io/crosvm-infra/crosvm_dev_base_asahi:${BASE_VERSION}

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/workspace/tools:/usr/local/cargo/bin:$PATH

# Install pipx applications globally in /usr/local/bin
ENV PIPX_HOME=/usr/local/pipx \
    PIPX_BIN_DIR=/usr/local/bin

# Use a dedicated target directory so we do not write into the source directory.
RUN mkdir -p /scratch/cargo_target \
    && mkdir /cache

# Prevent the container from writing __pycache__ files into the src.
ENV PYTHONDONTWRITEBYTECODE=1
ENV CARGO_TARGET_DIR=/scratch/cargo_target

# Allow DNF to cache packages between docker image builds
RUN echo 'keepcache=True' >> /etc/dnf/dnf.conf

# Install non-RPM dependencies (Rust toolchain, cargo tools, mdformat)
COPY --chmod=555 \
    tools/deps/install-aarch64-other \
    tools/deps/install_rutabaga_gfx_deps \
    rust-toolchain \
    /tools/deps/

RUN cd /tools/deps \
    && ./install-aarch64-other \
    && ./install_rutabaga_gfx_deps \
    # We only use the nightly toolchain for rustfmt; remove other parts to save space.
    && rustup component remove --toolchain nightly rust-std \
    && rustup component remove --toolchain nightly cargo

# Install cargo config for native aarch64
COPY --chmod=444 .cargo/config.toml /.cargo/config.toml

# Install catapult dashboard upload tool
COPY --from=gobuilder /root/infra/cmd/catapult/catapult /tools/

# Cache CARGO_HOME between container runs in CI.
VOLUME /cache
ENV CROSVM_CACHE_DIR=/cache
ENV CARGO_HOME=/cache/cargo_home

VOLUME /workspace
WORKDIR /workspace
