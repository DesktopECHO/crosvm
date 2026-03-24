// Copyright 2022 The ChromiumOS Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

use std::path::PathBuf;
use pkg_config::Config;

fn main() {
    // Skip building dependencies when generating documents.
    if std::env::var("CARGO_DOC").is_ok() {
        return;
    }

    // ffmpeg is currently only supported on unix
    if std::env::var("CARGO_CFG_UNIX").is_err() {
        return;
    }

    // ffmpeg is not supported by CI on 32-bit arm
    if std::env::var("CARGO_CFG_TARGET_ARCH").unwrap() == "arm" {
        return;
    }

    // Match all ffmpeg 6.0+ versions.
    let avcodec = Config::new()
        .atleast_version("60")
        .probe("libavcodec")
        .unwrap();
    let avutil = Config::new()
        .atleast_version("58")
        .probe("libavutil")
        .unwrap();
    let swscale = Config::new()
        .atleast_version("7")
        .probe("libswscale")
        .unwrap();

    // Build bindgen with include paths sourced from pkg-config so that clang
    // can locate headers regardless of distro conventions (Fedora installs to
    // /usr/include, but the .pc IncludeDirs field is authoritative).
    let mut builder = bindgen::Builder::default()
        .header("src/bindings.h")
        .allowlist_function("av_.*")
        .allowlist_function("avcodec_.*")
        .allowlist_function("sws_.*")
        .allowlist_function("av_image_.*")
        .allowlist_var("AV_PROFILE.*")
        .allowlist_var("AV_.*")
        .allowlist_var("AVERROR_.*")
        // Skip va_list and functions that use it to avoid ABI problems on aarch64.
        .blocklist_type(".*va_list.*")
        .blocklist_function("av_log_.*")
        .blocklist_function("av_vlog");

    // Feed pkg-config include paths into clang so it can find the headers.
    // On Fedora, ffmpeg-free-devel installs headers to /usr/include/ffmpeg/
    // rather than /usr/include/, so we add that path explicitly as a fallback.
    let mut extra_includes: Vec<std::path::PathBuf> = vec![
        "/usr/include/ffmpeg".into(),
    ];

    for path in avcodec
        .include_paths
        .iter()
        .chain(avutil.include_paths.iter())
        .chain(swscale.include_paths.iter())
        .chain(extra_includes.iter())
    {
        builder = builder.clang_arg(format!("-I{}", path.display()));
    }

    let bindings = builder.generate().expect("failed to generate bindings");

    let out_path = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("writing bindings to file failed");
}
