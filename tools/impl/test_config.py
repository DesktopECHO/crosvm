# Copyright 2025 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Asahi Fedora Remix (aarch64) — all non-aarch64 platforms removed.

from typing import Dict

BUILD_FEATURES: Dict[str, str] = {
    "aarch64-unknown-linux-gnu": "linux-aarch64",
}

# Configuration of integration tests
#
# This configuration only applies to integration tests, to fine-tune which
# tests can run on this platform.
#
# This configuration does NOT apply to unit tests.

# List of integration tests that will ask for root privileges.
ROOT_TESTS = [
    "package(e2e_tests) & binary(pci_hotplug)",
    "package(e2e_tests) & binary(swap)",
    "package(net_util) & binary(unix_tap)",
    "package(cros_tracing) & binary(trace_marker)",
    "package(swap) & binary(page_handler)",
    "package(swap) & binary(main)",
    "package(ext2) & binary(tests)",
]

# Do not run these tests on any platform.
DO_NOT_RUN = [
    "package(io_uring)",
]

# Do not run these tests on aarch64.
DO_NOT_RUN_AARCH64 = [
    "package(hypervisor)",
    "package(e2e_tests)",
]

# Avoid e2e tests and benchmarks being automatically included as unit tests.
E2E_TESTS = [
    "package(e2e_tests)",
]
