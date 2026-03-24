# Copyright 2025 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Builds the aarch64 test VM image for Asahi Fedora Remix.
# x86_64 paths and Debian image sources have been removed.
#
# To build and upload a new base image, uprev the version in the `version` file
# and run:
#   make upload
#
# You need write access to the crosvm-testvm storage bucket.

TMPDIR           ?= /tmp
CROSVM_CACHE_DIR ?= $(TMPDIR)
ARCH             := aarch64
TARGET           := $(CROSVM_CACHE_DIR)/crosvm_tools/$(ARCH)

$(shell mkdir -p $(TARGET))

# Use QEMU with the Apple Silicon-compatible cortex-a57 CPU model.
QEMU_CMD := qemu-system-aarch64 \
    -cpu cortex-a57 \
    -M virt \
    -bios /usr/share/edk2/aarch64/QEMU_EFI.fd

GS_PREFIX      := gs://crosvm/testvm
# Fedora Cloud base image for aarch64
FEDORA_VERSION := 41
FEDORA_URL     := https://dl.fedoraproject.org/pub/fedora/linux/releases/$(FEDORA_VERSION)/Cloud/aarch64/images
FEDORA_IMG     := Fedora-Cloud-Base-Generic-$(FEDORA_VERSION)-1.4.aarch64.qcow2

BASE_IMG_NAME  := base-aarch64-$(shell cat version).qcow2
GS_URL         := $(GS_PREFIX)/$(BASE_IMG_NAME)
LOCAL_IMAGE    := $(TARGET)/$(BASE_IMG_NAME)

.PHONY: all clean upload

all: $(LOCAL_IMAGE)

clean:
	rm -rf $(TARGET)

upload: $(LOCAL_IMAGE)
	gsutil cp -n $(LOCAL_IMAGE) $(GS_URL)

# Download Fedora Cloud aarch64 as base image for the testvm.
$(TARGET)/fedora.qcow2:
	wget $(FEDORA_URL)/$(FEDORA_IMG) -O $@.tmp
	qemu-img resize $@.tmp 8G
	mv $@.tmp $@

# Apply cloud-init to configure the VM on first boot.
$(TARGET)/cloud_init.img: cloud_init.yaml
	cloud-localds -v $@ $<

# Boot the VM once to let cloud-init configure it, then export the result.
$(LOCAL_IMAGE): $(TARGET)/fedora.qcow2 $(TARGET)/cloud_init.img
	cp $(TARGET)/fedora.qcow2 $(TARGET)/disk.qcow2
	$(QEMU_CMD) \
	    -m 4G \
	    -smp 4 \
	    -nographic \
	    -drive file=$(TARGET)/disk.qcow2,if=virtio \
	    -drive file=$(TARGET)/cloud_init.img,if=virtio,format=raw \
	    -netdev user,id=net0 \
	    -device virtio-net-pci,netdev=net0
	qemu-img convert -O qcow2 -c $(TARGET)/disk.qcow2 $(LOCAL_IMAGE)
	qemu-img info $(LOCAL_IMAGE)
