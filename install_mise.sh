#!/bin/sh
set -eu

#region logging setup
if [ "${MISE_DEBUG-}" = "true" ] || [ "${MISE_DEBUG-}" = "1" ]; then
  debug() {
    echo "$@" >&2
  }
else
  debug() {
    :
  }
fi

if [ "${MISE_QUIET-}" = "1" ] || [ "${MISE_QUIET-}" = "true" ]; then
  info() {
    :
  }
else
  info() {
    echo "$@" >&2
  }
fi

error() {
  echo "$@" >&2
  exit 1
}
#endregion

#region environment setup
get_os() {
  os="$(uname -s)"
  if [ "$os" = Darwin ]; then
    echo "macos"
  elif [ "$os" = Linux ]; then
    echo "linux"
  else
    error "unsupported OS: $os"
  fi
}

get_arch() {
  musl=""
  if type ldd >/dev/null 2>/dev/null; then
    if [ "${MISE_INSTALL_MUSL-}" = "1" ] || [ "${MISE_INSTALL_MUSL-}" = "true" ]; then
      musl="-musl"
    elif [ "$(uname -o)" = "Android" ]; then
      # Android (Termux) always uses musl
      musl="-musl"
    else
      libc=$(ldd /bin/ls | grep 'musl' | head -1 | cut -d ' ' -f1)
      if [ -n "$libc" ]; then
        musl="-musl"
      fi
    fi
  fi
  arch="$(uname -m)"
  if [ "$arch" = x86_64 ]; then
    echo "x64$musl"
  elif [ "$arch" = aarch64 ] || [ "$arch" = arm64 ]; then
    echo "arm64$musl"
  elif [ "$arch" = armv7l ]; then
    echo "armv7$musl"
  else
    error "unsupported architecture: $arch"
  fi
}

get_ext() {
  if [ -n "${MISE_INSTALL_EXT:-}" ]; then
    echo "$MISE_INSTALL_EXT"
  elif [ -n "${MISE_VERSION:-}" ] && echo "$MISE_VERSION" | grep -q '^v2024'; then
    # 2024 versions don't have zstd tarballs
    echo "tar.gz"
  elif tar_supports_zstd; then
    echo "tar.zst"
  elif command -v zstd >/dev/null 2>&1; then
    echo "tar.zst"
  else
    echo "tar.gz"
  fi
}

tar_supports_zstd() {
  # tar is bsdtar or version is >= 1.31
  if tar --version | grep -q 'bsdtar' && command -v zstd >/dev/null 2>&1; then
    true
  elif tar --version | grep -q '1\.(3[1-9]|[4-9][0-9]'; then
    true
  else
    false
  fi
}

shasum_bin() {
  if command -v shasum >/dev/null 2>&1; then
    echo "shasum"
  elif command -v sha256sum >/dev/null 2>&1; then
    echo "sha256sum"
  else
    error "mise install requires shasum or sha256sum but neither is installed. Aborting."
  fi
}

get_checksum() {
  version=$1
  os=$2
  arch=$3
  ext=$4
  url="https://github.com/jdx/mise/releases/download/v${version}/SHASUMS256.txt"

  # For current version use static checksum otherwise
  # use checksum from releases
  if [ "$version" = "v2026.2.19" ]; then
    checksum_linux_x86_64="a52b57e2694d3c22abe0f1ecc5e5b8b00aded34b7b4f570c8d1eb0737167656a  ./mise-v2026.2.19-linux-x64.tar.gz"
    checksum_linux_x86_64_musl="72e95fefc55e4d665543d13e76175853c2ef87365ecdd7b00ca99683de1c252a  ./mise-v2026.2.19-linux-x64-musl.tar.gz"
    checksum_linux_arm64="6fbab4e5aed4975144b000ae8a509404ef0a9304ccec3d2411465fbc98215441  ./mise-v2026.2.19-linux-arm64.tar.gz"
    checksum_linux_arm64_musl="74bd261911f1fd094053fa64fc0b41e7bc7b29b03ca75c82d742c0b22f0a90d8  ./mise-v2026.2.19-linux-arm64-musl.tar.gz"
    checksum_linux_armv7="ce2c00807c9edad790ee5a0ccfc4b6abf1b2191fe6b72bff3d43ef8b950042a7  ./mise-v2026.2.19-linux-armv7.tar.gz"
    checksum_linux_armv7_musl="a919054c71db13f35b104f34c2835d6e18984f9284c5cdc4249e5e6c52c42990  ./mise-v2026.2.19-linux-armv7-musl.tar.gz"
    checksum_macos_x86_64="a378879003ba0e0667b8bc39c02c90adc926f5211ccfae17bc755b3768842f50  ./mise-v2026.2.19-macos-x64.tar.gz"
    checksum_macos_arm64="dd4370e96dea209d7c091f8bba7239233bcbc8889b94263a0ea7d6adab23826d  ./mise-v2026.2.19-macos-arm64.tar.gz"
    checksum_linux_x86_64_zstd="8de4b319d532b81d0d4bb1726a8416d7476db6d149423b440fa385858b2c3c3a  ./mise-v2026.2.19-linux-x64.tar.zst"
    checksum_linux_x86_64_musl_zstd="e2b36e184291e7df09a59c3e603ccbb3595fbe68aec8528b707770835817811b  ./mise-v2026.2.19-linux-x64-musl.tar.zst"
    checksum_linux_arm64_zstd="0951f589e658ab243bab37d76d7839d255d61f17e9bdcd43a16a0fe2e0cfd8fe  ./mise-v2026.2.19-linux-arm64.tar.zst"
    checksum_linux_arm64_musl_zstd="36d58f2836815f6e931afe522b60921989abfd6bf78cf6645c995036fa0f1f4d  ./mise-v2026.2.19-linux-arm64-musl.tar.zst"
    checksum_linux_armv7_zstd="f729eff0d95bfa01f6f8828f17e0d9c084cf9c16b27304cbb1357003f3fb589d  ./mise-v2026.2.19-linux-armv7.tar.zst"
    checksum_linux_armv7_musl_zstd="7cff38b2a32a98af1daf5d264d5170555365e6466522f4ff83e02bca6833f79a  ./mise-v2026.2.19-linux-armv7-musl.tar.zst"
    checksum_macos_x86_64_zstd="a8cf9a993eee2cc6ef5eb398e628fb9a757f3bb9129f4d852aded94dcd1d0f7d  ./mise-v2026.2.19-macos-x64.tar.zst"
    checksum_macos_arm64_zstd="1f38d5ab0c89ddb4f090738070519a00a308ad7c385eb1d019f684d1465acbc4  ./mise-v2026.2.19-macos-arm64.tar.zst"

    # TODO: refactor this, it's a bit messy
    if [ "$ext" = "tar.zst" ]; then
      if [ "$os" = "linux" ]; then
        if [ "$arch" = "x64" ]; then
          echo "$checksum_linux_x86_64_zstd"
        elif [ "$arch" = "x64-musl" ]; then
          echo "$checksum_linux_x86_64_musl_zstd"
        elif [ "$arch" = "arm64" ]; then
          echo "$checksum_linux_arm64_zstd"
        elif [ "$arch" = "arm64-musl" ]; then
          echo "$checksum_linux_arm64_musl_zstd"
        elif [ "$arch" = "armv7" ]; then
          echo "$checksum_linux_armv7_zstd"
        elif [ "$arch" = "armv7-musl" ]; then
          echo "$checksum_linux_armv7_musl_zstd"
        else
          warn "no checksum for $os-$arch"
        fi
      elif [ "$os" = "macos" ]; then
        if [ "$arch" = "x64" ]; then
          echo "$checksum_macos_x86_64_zstd"
        elif [ "$arch" = "arm64" ]; then
          echo "$checksum_macos_arm64_zstd"
        else
          warn "no checksum for $os-$arch"
        fi
      else
        warn "no checksum for $os-$arch"
      fi
    else
      if [ "$os" = "linux" ]; then
        if [ "$arch" = "x64" ]; then
          echo "$checksum_linux_x86_64"
        elif [ "$arch" = "x64-musl" ]; then
          echo "$checksum_linux_x86_64_musl"
        elif [ "$arch" = "arm64" ]; then
          echo "$checksum_linux_arm64"
        elif [ "$arch" = "arm64-musl" ]; then
          echo "$checksum_linux_arm64_musl"
        elif [ "$arch" = "armv7" ]; then
          echo "$checksum_linux_armv7"
        elif [ "$arch" = "armv7-musl" ]; then
          echo "$checksum_linux_armv7_musl"
        else
          warn "no checksum for $os-$arch"
        fi
      elif [ "$os" = "macos" ]; then
        if [ "$arch" = "x64" ]; then
          echo "$checksum_macos_x86_64"
        elif [ "$arch" = "arm64" ]; then
          echo "$checksum_macos_arm64"
        else
          warn "no checksum for $os-$arch"
        fi
      else
        warn "no checksum for $os-$arch"
      fi
    fi
  else
    if command -v curl >/dev/null 2>&1; then
      debug ">" curl -fsSL "$url"
      checksums="$(curl --compressed -fsSL "$url")"
    else
      if command -v wget >/dev/null 2>&1; then
        debug ">" wget -qO - "$url"
        checksums="$(wget -qO - "$url")"
      else
        error "mise standalone install specific version requires curl or wget but neither is installed. Aborting."
      fi
    fi
    # TODO: verify with minisign or gpg if available

    checksum="$(echo "$checksums" | grep "$os-$arch.$ext")"
    if ! echo "$checksum" | grep -Eq "^([0-9a-f]{32}|[0-9a-f]{64})"; then
      warn "no checksum for mise $version and $os-$arch"
    else
      echo "$checksum"
    fi
  fi
}

#endregion

download_file() {
  url="$1"
  download_dir="$2"
  filename="$(basename "$url")"
  file="$download_dir/$filename"

  info "mise: installing mise..."

  if command -v curl >/dev/null 2>&1; then
    debug ">" curl -#fLo "$file" "$url"
    curl -#fLo "$file" "$url"
  else
    if command -v wget >/dev/null 2>&1; then
      debug ">" wget -qO "$file" "$url"
      stderr=$(mktemp)
      wget -O "$file" "$url" >"$stderr" 2>&1 || error "wget failed: $(cat "$stderr")"
      rm "$stderr"
    else
      error "mise standalone install requires curl or wget but neither is installed. Aborting."
    fi
  fi

  echo "$file"
}

install_mise() {
  version="${MISE_VERSION:-v2026.2.19}"
  version="${version#v}"
  os="${MISE_INSTALL_OS:-$(get_os)}"
  arch="${MISE_INSTALL_ARCH:-$(get_arch)}"
  ext="${MISE_INSTALL_EXT:-$(get_ext)}"
  install_path="${MISE_INSTALL_PATH:-$HOME/.local/bin/mise}"
  install_dir="$(dirname "$install_path")"
  install_from_github="${MISE_INSTALL_FROM_GITHUB:-}"
  if [ "$version" != "v2026.2.19" ] || [ "$install_from_github" = "1" ] || [ "$install_from_github" = "true" ]; then
    tarball_url="https://github.com/jdx/mise/releases/download/v${version}/mise-v${version}-${os}-${arch}.${ext}"
  elif [ -n "${MISE_TARBALL_URL-}" ]; then
    tarball_url="$MISE_TARBALL_URL"
  else
    tarball_url="https://mise.jdx.dev/v${version}/mise-v${version}-${os}-${arch}.${ext}"
  fi

  download_dir="$(mktemp -d)"
  cache_file=$(download_file "$tarball_url" "$download_dir")
  debug "mise-setup: tarball=$cache_file"

  debug "validating checksum"
  cd "$(dirname "$cache_file")" && get_checksum "$version" "$os" "$arch" "$ext" | "$(shasum_bin)" -c >/dev/null

  # extract tarball
  mkdir -p "$install_dir"
  rm -rf "$install_path"
  extract_dir="$(mktemp -d)"
  cd "$extract_dir"
  if [ "$ext" = "tar.zst" ] && ! tar_supports_zstd; then
    zstd -d -c "$cache_file" | tar -xf -
  else
    tar -xf "$cache_file"
  fi
  mv mise/bin/mise "$install_path"

  # cleanup
  cd / # Move out of $extract_dir before removing it
  rm -rf "$download_dir"
  rm -rf "$extract_dir"

  info "mise: installed successfully to $install_path"
}

after_finish_help() {
  case "${SHELL:-}" in
  */zsh)
    info "mise: run the following to activate mise in your shell:"
    info "echo \"eval \\\"\\\$($install_path activate zsh)\\\"\" >> \"${ZDOTDIR-$HOME}/.zshrc\""
    info ""
    info "mise: run \`mise doctor\` to verify this is set up correctly"
    ;;
  */bash)
    info "mise: run the following to activate mise in your shell:"
    info "echo \"eval \\\"\\\$($install_path activate bash)\\\"\" >> ~/.bashrc"
    info ""
    info "mise: run \`mise doctor\` to verify this is set up correctly"
    ;;
  */fish)
    info "mise: run the following to activate mise in your shell:"
    info "echo \"$install_path activate fish | source\" >> ~/.config/fish/config.fish"
    info ""
    info "mise: run \`mise doctor\` to verify this is set up correctly"
    ;;
  *)
    info "mise: run \`$install_path --help\` to get started"
    ;;
  esac
}

install_mise
if [ "${MISE_INSTALL_HELP-}" != 0 ]; then
  after_finish_help
fi
