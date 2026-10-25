#!/bin/sh
# NioXS & MicroLM Fleet installer for Linux, macOS, and Termux
# One-liner: curl -fsSL https://nio-labs.github.io/nio-xs-models/install.sh | bash
set -eu

REPO="nio-labs/nio-xs-models"
VERSION="${NIOXS_VERSION:-v0.1.0}"
DEFAULT_BIN_DIR="$HOME/.local/bin"

cleanup() {
    if [ -n "${TMP_DIR:-}" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}
trap cleanup EXIT INT TERM

echo "🚀 Installing Nio MicroLM Fleet (Viper, Nano, Micro, Mask, Mini)"

# 1. Detect OS
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
    linux)
        if [ -n "${TERMUX_VERSION:-}" ] || [ -d "/data/data/com.termux" ]; then
            PLATFORM="linux-android"
            DEFAULT_BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"
        elif ldd --version 2>&1 | grep -iq musl; then
            PLATFORM="unknown-linux-musl"
        else
            PLATFORM="unknown-linux-gnu"
        fi
        ;;
    darwin)
        PLATFORM="apple-darwin"
        ;;
    *)
        echo "❌ Unsupported operating system: $OS" >&2
        echo "   For Windows, run install.ps1 in PowerShell." >&2
        exit 1
        ;;
esac

# 2. Detect architecture
case "$ARCH" in
    x86_64|amd64)
        TARGET_ARCH="x86_64"
        ;;
    aarch64|arm64)
        TARGET_ARCH="aarch64"
        ;;
    *)
        echo "❌ Unsupported architecture: $ARCH" >&2
        exit 1
        ;;
esac

TARGET="${TARGET_ARCH}-${PLATFORM}"
echo "🔍 Detected target architecture: $TARGET"

# 3. Determine install destination
BIN_DIR="${BIN_DIR:-$DEFAULT_BIN_DIR}"
mkdir -p "$BIN_DIR"

TMP_DIR="$(mktemp -d)"

# Function to download or fallback to cargo build
install_binary() {
    BIN_NAME="$1"
    CRATE_NAME="$2"
    ASSET_NAME="${BIN_NAME}-${TARGET}.tar.gz"
    RELEASE_URL="https://github.com/${REPO}/releases/download/${VERSION}/${ASSET_NAME}"
    TARGET_PATH="${BIN_DIR}/${BIN_NAME}"

    echo "📦 Fetching ${BIN_NAME} (${VERSION})..."
    DOWNLOAD_SUCCESS=0
    if command -v curl >/dev/null 2>&1; then
        if curl --connect-timeout 8 --max-time 60 -fsSL "$RELEASE_URL" -o "${TMP_DIR}/${ASSET_NAME}" 2>/dev/null; then
            DOWNLOAD_SUCCESS=1
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget --timeout=15 -q "$RELEASE_URL" -O "${TMP_DIR}/${ASSET_NAME}" 2>/dev/null; then
            DOWNLOAD_SUCCESS=1
        fi
    fi

    if [ "$DOWNLOAD_SUCCESS" -eq 1 ]; then
        tar -xzf "${TMP_DIR}/${ASSET_NAME}" -C "${TMP_DIR}"
        mv "${TMP_DIR}/${BIN_NAME}" "$TARGET_PATH"
        chmod +x "$TARGET_PATH"
        echo "✅ Installed ${BIN_NAME} to ${TARGET_PATH}"
    else
        # Fallback 1: check if currently running inside the nio-xs-models repository
        if [ -f "Cargo.toml" ] && grep -q "crates/nioxs-cli" Cargo.toml 2>/dev/null; then
            echo "⚡ Compiling ${BIN_NAME} locally from repository source..."
            cargo build --release -p "$CRATE_NAME" 2>/dev/null || cargo build --release
            if [ -f "target/release/${BIN_NAME}" ]; then
                cp "target/release/${BIN_NAME}" "$TARGET_PATH"
                chmod +x "$TARGET_PATH"
                echo "✅ Installed ${BIN_NAME} to ${TARGET_PATH}"
                return 0
            fi
        fi

        # Fallback 2: cargo install from GitHub if cargo is available
        if command -v cargo >/dev/null 2>&1; then
            echo "⚡ Pre-built archive not yet uploaded for target; compiling via cargo..."
            cargo install --git "https://github.com/${REPO}.git" "$CRATE_NAME" --root "${TMP_DIR}/cargo_root"
            mv "${TMP_DIR}/cargo_root/bin/${BIN_NAME}" "$TARGET_PATH"
            chmod +x "$TARGET_PATH"
            echo "✅ Installed ${BIN_NAME} to ${TARGET_PATH}"
        else
            echo "⚠️ Could not download pre-built binary and cargo is not installed."
            echo "   Please install Rust and run: cargo install --git https://github.com/${REPO}.git ${CRATE_NAME}"
            return 1
        fi
    fi
}

install_binary "nioxs" "nioxs-cli"
install_binary "nioxs-mcp" "nio-mcp"

# 4. Check PATH
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
        echo ""
        echo "⚠️ $BIN_DIR is not in your PATH."
        echo "   Add it by adding this to your ~/.bashrc, ~/.zshrc, or ~/.profile:"
        echo "     export PATH=\"\$HOME/.local/bin:\$PATH\""
        ;;
esac

# 5. OpenCode MCP Integration
OPENCODE_CONFIG_DIR="$HOME/.config/opencode"
OPENCODE_CONFIG_FILE="$OPENCODE_CONFIG_DIR/opencode.jsonc"
if [ -d "$OPENCODE_CONFIG_DIR" ] || command -v opencode >/dev/null 2>&1; then
    mkdir -p "$OPENCODE_CONFIG_DIR"
    if [ ! -f "$OPENCODE_CONFIG_FILE" ]; then
        echo "⚙️ Configuring OpenCode MCP integration at $OPENCODE_CONFIG_FILE..."
        cat <<EOF > "$OPENCODE_CONFIG_FILE"
{
  "\$schema": "https://opencode.ai/config.json",
  "mcp": {
    "nio": {
      "type": "local",
      "command": [
        "$BIN_DIR/nioxs-mcp",
        "--stdio"
      ],
      "enabled": true
    }
  }
}
EOF
        echo "✅ OpenCode MCP configured automatically!"
    elif ! grep -q "nioxs-mcp" "$OPENCODE_CONFIG_FILE" 2>/dev/null; then
        echo "💡 Tip: To attach the Nio MCP server to OpenCode, add this to your $OPENCODE_CONFIG_FILE:"
        echo "   \"mcp\": { \"nio\": { \"type\": \"local\", \"command\": [\"$BIN_DIR/nioxs-mcp\", \"--stdio\"], \"enabled\": true } }"
    fi
fi

# 6. Verification
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ⚡ Nio MicroLM Fleet Installed Successfully! ⚡"
echo "════════════════════════════════════════════════════════════════"
if [ -x "$BIN_DIR/nioxs" ]; then
    "$BIN_DIR/nioxs" --version 2>/dev/null || echo "nioxs $VERSION"
fi
echo " • Viper (100M)  : AST-MicroLM pure-Rust reflex (27.14 MB peak RAM, <20µs)"
echo " • Nano (~0.5M)  : Intent & Directive Router (<0.1ms)"
echo " • Micro (5.0M)  : Policy Arbiter & Safety Clutch (<4ms)"
echo " • Mask (1.1M)   : Zero-Cloud Credential Redactor (<0.2ms)"
echo " • Mini (7.1M)   : Pre-Flight Defect Forecaster (<5ms)"
echo " • Empirical Token Conservation: 99.62%"
echo ""
echo "🚀 Try running:"
echo "   nioxs viper \"kill process on port 3000\""
echo "   nioxs proof"
echo "   nioxs-mcp --stdio"
echo "════════════════════════════════════════════════════════════════"
