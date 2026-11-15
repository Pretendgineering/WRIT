#!/usr/bin/env bash
# writ installer — also safe to re-run to upgrade an existing install.
set -e

REPO="https://github.com/Spasm0dic/WRIT.git"
BRANCH="main"
VENV_DIR="$HOME/.local/share/writ"
BIN_DIR="$HOME/.local/bin"

# ── Check Python 3.10+ ────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "error: python3 not found. Install Python 3.10 or higher and try again."
    exit 1
fi

python3 - <<'EOF'
import sys
if sys.version_info < (3, 10):
    print(f"error: Python 3.10+ required (found {sys.version.split()[0]})")
    sys.exit(1)
EOF

# ── Create venv ─────────────────────────────────────────────────────────
if [[ -x "$VENV_DIR/env/bin/pip" ]]; then
    echo "→ Existing install found at $VENV_DIR — upgrading"
else
    echo "→ Creating virtual environment at $VENV_DIR"
    if ! python3 -m venv "$VENV_DIR/env"; then
        echo "error: could not create a virtualenv."
        echo "       On Debian/Ubuntu, install it with:  sudo apt install python3-venv"
        exit 1
    fi
fi

# ── Install writ ────────────────────────────────────────────────────────
echo "→ Installing writ from GitHub..."
"$VENV_DIR/env/bin/pip" install --quiet --no-cache-dir --upgrade --force-reinstall "git+$REPO@$BRANCH"

# ── Symlink binary ───────────────────────────────────────────────────────────
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/env/bin/writ" "$BIN_DIR/writ"

# ── Ensure ~/.local/bin is on PATH ────────────────────────────────────────────
add_to_path() {
    local rc="$1"
    if [[ -f "$rc" ]] && ! grep -q 'local/bin' "$rc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
        echo "  added \$HOME/.local/bin to PATH in $rc"
    fi
}

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    add_to_path "$HOME/.bashrc"
    add_to_path "$HOME/.zshrc"
    export PATH="$BIN_DIR:$PATH"
fi

# ── First-time setup (download KJV translation) ────────────────────────────────
# 'writ setup' skips automatically if the KJV is already installed.
echo "→ Setting up King James Bible (public domain)..."
"$BIN_DIR/writ" setup

echo ""
echo "✓ Done. Start with:  writ ge 1"
echo ""
echo "  If 'writ' isn't found, run:  source ~/.bashrc  (or open a new terminal)"
