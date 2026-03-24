# Copyright 2025 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Test VM management for Asahi Fedora Remix (aarch64).
# x86_64 support and Debian image references have been removed.

import json
import os
import socket
import subprocess
import sys
import time
import typing
from contextlib import closing
from pathlib import Path
from random import randrange
from typing import Dict, List, Literal, Optional, Tuple

from .common import CACHE_DIR, download_file, cmd, rich, console

KVM_SUPPORT = os.access("/dev/kvm", os.W_OK)

# Only aarch64 is supported on Asahi Fedora Remix.
Arch = Literal["aarch64"]
ARCH_OPTIONS = typing.cast(Tuple[Arch], typing.get_args(Arch))

SCRIPT_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPT_DIR.joinpath("testvm")
ID_RSA = SRC_DIR.joinpath("id_rsa")
BASE_IMG_VERSION = open(SRC_DIR.joinpath("version"), "r").read().strip()
IMAGE_DIR_URL = "https://storage.googleapis.com/crosvm/testvm"

EFI_BIOS = Path("/usr/share/edk2/aarch64/QEMU_EFI.fd")


def cargo_target_dir():
    env_target = os.environ.get("CARGO_TARGET_DIR")
    if env_target:
        return Path(env_target)
    text = subprocess.run(
        ["cargo", "metadata", "--no-deps", "--format-version=1"],
        check=True, capture_output=True, text=True,
    ).stdout
    metadata = json.loads(text)
    return Path(metadata["target_directory"])


def data_dir(arch: Arch = "aarch64"):
    return CACHE_DIR.joinpath("crosvm_tools").joinpath(arch)


def pid_path(arch: Arch = "aarch64"):
    return data_dir(arch).joinpath("pid")


def ssh_port_path(arch: Arch = "aarch64"):
    return data_dir(arch).joinpath("ssh_port")


def log_path(arch: Arch = "aarch64"):
    return data_dir(arch).joinpath("vm_log")


def base_img_name(arch: Arch = "aarch64"):
    return f"base-{arch}-{BASE_IMG_VERSION}.qcow2"


def base_img_url(arch: Arch = "aarch64"):
    return f"{IMAGE_DIR_URL}/{base_img_name(arch)}"


def base_img_path(arch: Arch = "aarch64"):
    return data_dir(arch).joinpath(base_img_name(arch))


def run_img_path(arch: Arch = "aarch64"):
    return data_dir(arch).joinpath(f"run-{arch}.qcow2")


def qemu_cmd(arch: Arch = "aarch64") -> List[str]:
    if not EFI_BIOS.exists():
        raise FileNotFoundError(
            f"EFI firmware not found at {EFI_BIOS}. "
            "Install edk2-aarch64: sudo dnf install edk2-aarch64"
        )
    return [
        "qemu-system-aarch64",
        "-cpu", "host" if KVM_SUPPORT else "cortex-a57",
        "-M", "virt",
        "-bios", str(EFI_BIOS),
    ]


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def is_port_open(port: int) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        return s.connect_ex(("localhost", port)) == 0


def ensure_base_image(arch: Arch = "aarch64"):
    path = base_img_path(arch)
    if not path.exists():
        data_dir(arch).mkdir(parents=True, exist_ok=True)
        console.print(f"Downloading base image for {arch}...")
        download_file(base_img_url(arch), path)
    return path


def start(arch: Arch = "aarch64", ssh_port: Optional[int] = None):
    "Start the aarch64 test VM."
    ensure_base_image(arch)

    if ssh_port is None:
        ssh_port = find_free_port()

    run_img = run_img_path(arch)
    base_img = base_img_path(arch)

    if not run_img.exists():
        subprocess.run(
            ["qemu-img", "create", "-f", "qcow2", "-b", str(base_img), "-F", "qcow2", str(run_img)],
            check=True,
        )

    kvm_args = ["-enable-kvm", "-cpu", "host"] if KVM_SUPPORT else ["-cpu", "cortex-a57"]
    launch_cmd = [
        *qemu_cmd(arch),
        *kvm_args,
        "-m", "4G",
        "-smp", "4",
        "-nographic",
        "-drive", f"file={run_img},if=virtio",
        "-netdev", f"user,id=net0,hostfwd=tcp::{ssh_port}-:22",
        "-device", "virtio-net-pci,netdev=net0",
    ]

    log = open(log_path(arch), "w")
    process = subprocess.Popen(launch_cmd, stdout=log, stderr=log)

    pid_path(arch).parent.mkdir(parents=True, exist_ok=True)
    pid_path(arch).write_text(str(process.pid))
    ssh_port_path(arch).write_text(str(ssh_port))

    console.print(f"Started aarch64 VM (pid={process.pid}, ssh_port={ssh_port})")
    console.print("Waiting for SSH...")

    deadline = time.time() + 120
    while time.time() < deadline:
        if is_port_open(ssh_port):
            break
        time.sleep(2)
    else:
        raise TimeoutError("VM did not start within 120 seconds.")

    return ssh_port


def ssh_cmd(arch: Arch = "aarch64") -> List[str]:
    port = int(ssh_port_path(arch).read_text())
    return [
        "ssh",
        "-i", str(ID_RSA),
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "crosvm@localhost",
    ]
