# Copyright 2025 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Builds the crosvm dev container for Asahi Fedora Remix (aarch64).

TOOLS_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
CROSVM_ROOT := $(shell realpath $(TOOLS_DIR)/../../../)

BASE_VERSION := $(shell cat $(TOOLS_DIR)/base_version)
VERSION := $(shell cat $(TOOLS_DIR)/version)

BASE_IMAGE := gcr.io/crosvm-infra/crosvm_dev_base_asahi
DEV_IMAGE  := gcr.io/crosvm-infra/crosvm_dev_asahi

.PHONY: base dev upload_base upload_dev

base:
	docker build \
		--platform linux/arm64 \
		-f $(TOOLS_DIR)/Dockerfile.base \
		-t $(BASE_IMAGE):$(BASE_VERSION) \
		-t $(BASE_IMAGE):latest \
		$(CROSVM_ROOT)

dev: base
	docker build \
		--platform linux/arm64 \
		--build-arg BASE_VERSION=$(BASE_VERSION) \
		-f $(TOOLS_DIR)/Dockerfile \
		-t $(DEV_IMAGE):$(VERSION) \
		-t $(DEV_IMAGE):latest \
		$(CROSVM_ROOT)

upload_base: base
	docker push $(BASE_IMAGE):$(BASE_VERSION)
	docker push $(BASE_IMAGE):latest

upload_dev: dev
	docker push $(DEV_IMAGE):$(VERSION)
	docker push $(DEV_IMAGE):latest
