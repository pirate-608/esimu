#!/usr/bin/env bash
# esimu installer (Linux / macOS)
# Downloads latest release from GitHub and installs to ~/.local/bin
#
# Usage:
#   REPO=owner/name ./install.sh              (run as file)
#   curl ... | REPO=owner/name bash           (piped from web)
#   curl ... | bash                            (auto-detect from CWD git remote)
set -euo pipefail

REPO="${REPO:-${ESIMU_REPO:-}}"
VERSION="${VERSION:-latest}"
BIN_DIR="${HOME}/.local/bin"

# ── Resolve repository ──────────────────────────────────────────────
if [ -z "$REPO" ]; then
  # Try to detect from git remote (works both piped from web and as-file)
  REPO=$(git -C "$(pwd)" remote get-url origin 2>/dev/null || true)
  if [[ "$REPO" =~ github\.com[:/](.+)/(.+?)(\.git)?$ ]]; then
    REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  fi
fi

if [ -z "$REPO" ]; then
  # Hardcoded default — the repo this script lives in
  REPO="pirate-608/esimu"
  echo "Repository: $REPO (default)"
else
  echo "Repository: $REPO"
fi
fi

# ── Detect platform ─────────────────────────────────────────────────
OS=$(uname -s)
ARCH=$(uname -m)

case "$OS-$ARCH" in
  Linux-x86_64)
    ASSET="esimu-linux-x64.tar.gz"
    BINARY="esimu-linux-x64"
    ;;
  Darwin-arm64|Darwin-aarch64)
    ASSET="esimu-darwin-arm64.tar.gz"
    BINARY="esimu-darwin-arm64"
    ;;
  Darwin-x86_64)
    echo "macOS Intel is not pre-built. Please build from source: bun build src/cli.ts --compile"
    exit 1
    ;;
  *)
    echo "Unsupported platform: $OS-$ARCH"
    echo "Please build from source: bun build src/cli.ts --compile"
    exit 1
    ;;
esac

# ── Determine download URL ──────────────────────────────────────────
if [ "$VERSION" = "latest" ]; then
  API_URL="https://api.github.com/repos/${REPO}/releases/latest"
else
  API_URL="https://api.github.com/repos/${REPO}/releases/tags/${VERSION}"
fi

echo "Fetching release info..."
RELEASE_JSON=$(curl -fsSL -H "Accept: application/vnd.github+json" "$API_URL")
TAG=$(echo "$RELEASE_JSON" | grep -o '"tag_name": *"[^"]*"' | head -1 | sed 's/.*"\(.*\)".*/\1/')

DOWNLOAD_URL=$(echo "$RELEASE_JSON" | grep -o "\"browser_download_url\": *\"[^\"]*${ASSET}\"" | sed 's/.*"\(https:.*\)".*/\1/')

if [ -z "$DOWNLOAD_URL" ]; then
  echo "Asset '${ASSET}' not found in release ${TAG}"
  echo "Available assets:"
  echo "$RELEASE_JSON" | grep -o '"name": *"[^"]*"' | sed 's/.*"\(.*\)".*/  \1/'
  exit 1
fi

# ── Download & extract ──────────────────────────────────────────────
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Downloading ${ASSET}..."
curl -fsSL -o "${TMP_DIR}/${ASSET}" "$DOWNLOAD_URL"

echo "Extracting..."
tar -xzf "${TMP_DIR}/${ASSET}" -C "$TMP_DIR"

# ── Install ─────────────────────────────────────────────────────────
mkdir -p "$BIN_DIR"

if [ -f "${TMP_DIR}/${BINARY}" ]; then
  cp "${TMP_DIR}/${BINARY}" "${BIN_DIR}/esimu"
elif [ -f "${TMP_DIR}/esimu" ]; then
  cp "${TMP_DIR}/esimu" "${BIN_DIR}/esimu"
else
  echo "Binary not found in archive. Contents:"
  find "$TMP_DIR" -type f
  exit 1
fi

chmod +x "${BIN_DIR}/esimu"

echo ""
echo "esimu ${TAG} installed to ${BIN_DIR}/esimu"

# ── PATH check ──────────────────────────────────────────────────────
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
  echo ""
  echo "Add to PATH to use from anywhere:"
  PROFILE=""
  if [ -f "${HOME}/.bashrc" ]; then PROFILE="${HOME}/.bashrc";
  elif [ -f "${HOME}/.zshrc" ]; then PROFILE="${HOME}/.zshrc";
  elif [ -f "${HOME}/.profile" ]; then PROFILE="${HOME}/.profile"; fi

  if [ -n "$PROFILE" ]; then
    echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> $PROFILE"
    echo "  source $PROFILE"
  else
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi
fi

echo ""
echo "Run 'esimu --version' to verify."
