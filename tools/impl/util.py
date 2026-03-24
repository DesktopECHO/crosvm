#!/usr/bin/env python3
# Copyright 2025 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# General utility functions.
# Asahi Fedora Remix (aarch64): non-aarch64 shorthands and Debian references removed.

import argparse
import contextlib
import datetime
import functools
import os
import re
import subprocess
import sys
import urllib
import urllib.request
import urllib.error
from pathlib import Path
from subprocess import DEVNULL, PIPE, STDOUT  # type: ignore
from typing import (
    Dict,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)

PathLike = Union[Path, str]

# Regex that matches ANSI escape sequences
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def find_crosvm_root():
    "Walk up from CWD until we find the crosvm root dir."
    path = Path("").resolve()
    while True:
        if (path / "tools/impl/common.py").is_file():
            return path
        if path.parent:
            path = path.parent
        else:
            raise Exception("Cannot find crosvm root dir.")


"Root directory of crosvm derived from CWD."
CROSVM_ROOT = find_crosvm_root()

"Cargo.toml file of crosvm"
CROSVM_TOML = CROSVM_ROOT / "Cargo.toml"

"""
Root directory of crosvm devtools. May differ from `CROSVM_ROOT/tools`, which
allows you to run the crosvm dev tools from this directory on another crosvm repo.
"""
TOOLS_ROOT = Path(__file__).parent.parent.resolve()

"Cache directory that is preserved between builds in CI."
CACHE_DIR = Path(os.environ.get("CROSVM_CACHE_DIR", os.environ.get("TMPDIR", "/tmp")))

assert 'name = "crosvm"' in CROSVM_TOML.read_text()

global_time_records: List[Tuple[str, datetime.timedelta]] = []


def crosvm_target_dir():
    crosvm_target = os.environ.get("CROSVM_TARGET_DIR")
    cargo_target = os.environ.get("CARGO_TARGET_DIR")
    if crosvm_target:
        return Path(crosvm_target)
    elif cargo_target:
        return Path(cargo_target) / "crosvm"
    else:
        return CROSVM_ROOT / "target/crosvm"


@functools.lru_cache(None)
def parse_common_args():
    parser = argparse.ArgumentParser(add_help=False)
    add_common_args(parser)
    return parser.parse_known_args()[0]


def add_common_args(parser: argparse.ArgumentParser):
    "These args are added to all commands."
    parser.add_argument(
        "--color",
        default="auto",
        choices=("always", "never", "auto"),
    )
    parser.add_argument("--verbose", "-v", action="store_true", default=False)
    parser.add_argument("--very-verbose", "-vv", action="store_true", default=False)
    parser.add_argument("--timing-info", action="store_true", default=False)


def verbose():
    return very_verbose() or parse_common_args().verbose


def very_verbose():
    return parse_common_args().very_verbose


def color_enabled():
    color_arg = parse_common_args().color
    if color_arg == "never":
        return False
    if color_arg == "always":
        return True
    return sys.stdout.isatty()


def find_scripts(path: Path, shebang: str):
    for file in path.glob("*"):
        if file.is_file() and file.open(errors="ignore").read(512).startswith(f"#!{shebang}"):
            yield file


def confirm(message: str, default: bool = False):
    print(message, "[y/N]" if default == False else "[Y/n]", end=" ", flush=True)
    try:
        response = sys.stdin.readline().strip()
    except KeyboardInterrupt:
        sys.exit(1)
    if response in ("y", "Y"):
        return True
    if response in ("n", "N"):
        return False
    return default


def is_cros_repo():
    dot_git = CROSVM_ROOT / ".git"
    if not dot_git.is_symlink() and dot_git.is_dir():
        return False
    return (cros_repo_root() / ".repo").exists()


def cros_repo_root():
    return (CROSVM_ROOT / "../../..").resolve()


def is_kiwi_repo():
    return (CROSVM_ROOT / ".kiwi_repo").exists()


def kiwi_repo_root():
    return (CROSVM_ROOT / "../..").resolve()


def is_aosp_repo():
    return (CROSVM_ROOT / "Android.bp").exists()


def aosp_repo_root():
    return (CROSVM_ROOT / "../..").resolve()


def sudo_is_passwordless():
    ret, _ = subprocess.getstatusoutput("SUDO_ASKPASS=false sudo --askpass true")
    return ret == 0


def rust_sysroot():
    from .command import cmd
    return Path(cmd("rustc --print=sysroot").stdout())


# Only the native aarch64 target is supported on Asahi Fedora Remix.
SHORTHANDS = {
    "aarch64": "aarch64-unknown-linux-gnu",
}


class Triple(NamedTuple):
    """
    Build triple in cargo format: <arch>-<vendor>-<sys>-<abi>
    Only aarch64-unknown-linux-gnu is supported on Asahi Fedora Remix.
    """

    arch: str
    vendor: str
    sys: Optional[str]
    abi: Optional[str]

    @classmethod
    def from_shorthand(cls, shorthand: str):
        if "-" in shorthand:
            triple = shorthand
        elif shorthand in SHORTHANDS:
            triple = SHORTHANDS[shorthand]
        else:
            raise Exception(f"Not a valid build triple shorthand: {shorthand}")
        return cls.from_str(triple)

    @classmethod
    def from_str(cls, triple: str):
        parts = triple.split("-")
        if len(parts) < 2:
            raise Exception(f"Unsupported triple {triple}")
        return cls(
            parts[0],
            parts[1],
            parts[2] if len(parts) > 2 else None,
            parts[3] if len(parts) > 3 else None,
        )

    @classmethod
    def from_linux_arch(cls, arch: str):
        return cls.from_str(f"{arch}-unknown-linux-gnu")

    @classmethod
    def host_default(cls):
        rustc_info = subprocess.check_output(["rustc", "-vV"], text=True)
        match = re.search(r"host: (\S+)", rustc_info)
        if not match:
            raise Exception(f"Cannot parse rustc info: {rustc_info}")
        return cls.from_str(match.group(1))

    @property
    def feature_flag(self):
        triple_to_shorthand = {v: k for k, v in SHORTHANDS.items()}
        shorthand = triple_to_shorthand.get(str(self))
        if not shorthand:
            raise Exception(f"No feature set for triple {self}")
        return f"all-{shorthand}"

    @property
    def target_dir(self):
        return crosvm_target_dir() / str(self)

    def get_cargo_env(self) -> Dict[str, str]:
        env: Dict[str, str] = {}
        env["CARGO_BUILD_TARGET"] = str(self)
        env["CARGO_TARGET_DIR"] = str(self.target_dir)
        env["CROSVM_TARGET_DIR"] = str(crosvm_target_dir())
        return env

    def __str__(self):
        parts = [self.arch, self.vendor]
        if self.sys:
            parts = [*parts, self.sys]
        if self.abi:
            parts = [*parts, self.abi]
        return "-".join(parts)


def download_file(url: str, filename: Path, attempts: int = 3):
    assert attempts > 0
    while True:
        attempts -= 1
        try:
            urllib.request.urlretrieve(url, filename)
            return
        except Exception as e:
            if attempts == 0:
                raise e
            else:
                print("Download failed:", e)


def strip_ansi_escape_sequences(line: str) -> str:
    return ANSI_ESCAPE.sub("", line)


def ensure_packages_exist(*packages: str):
    """
    Exits if one of the listed Python packages does not exist.
    """
    missing_packages: List[str] = []
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        # Some packages (e.g. argh) have no Fedora RPM — install via pip3.
        rpm_packages = [f"python3-{p}" for p in missing_packages]
        package_list = " ".join(rpm_packages)
        print("Missing python dependencies. Please re-run ./tools/setup")
        print(f"Or try: sudo dnf install {package_list}")
        print(f"If not available as RPM: pip3 install --user {' '.join(missing_packages)}")
        sys.exit(1)


@contextlib.contextmanager
def record_time(title: str):
    start_time = datetime.datetime.now()
    try:
        yield
    finally:
        global_time_records.append((title, datetime.datetime.now() - start_time))


def print_timing_info():
    print()
    print("Timing info:")
    print()
    for title, delta in global_time_records:
        print(f"  {title:20} {delta.total_seconds():.2f}s")
