#!/usr/bin/env bash
# install_cw_wrappers.sh — install the `cw` CLI into PATH
# Usage: bash scripts/install_cw_wrappers.sh [--bin-dir <dir>]
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${CW_BIN_DIR:-$HOME/.local/bin}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bin-dir) BIN_DIR="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $(basename "$0") [--bin-dir <dir>]"
      echo "Installs the cw CLI (a real file, not a symlink) into BIN_DIR."
      exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$BIN_DIR"

# Remove legacy workspace-scoped wrappers (cw-sysop-*, cw-main-*, etc.) if present.
removed=0
for f in "$BIN_DIR"/cw-*; do
  [[ -e "$f" ]] || continue
  rm -f "$f"
  removed=$((removed+1))
done

# Remove old symlink-based cw if present.
if [[ -L "$BIN_DIR/cw" ]]; then
  rm -f "$BIN_DIR/cw"
  removed=$((removed+1))
fi

# Install real launcher file (not a symlink) so the target is self-contained.
cat > "$BIN_DIR/cw" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "$SCRIPT_DIR/cw" "\$@"
EOF
chmod +x "$BIN_DIR/cw"
chmod +x "$SCRIPT_DIR/cw"

echo "Installed: $BIN_DIR/cw → $SCRIPT_DIR/cw"
echo "Cleaned up: $removed legacy wrapper(s) removed."
echo ""
echo "Quick start:"
echo "  cw agent use <your-agent-id>   # set active agent"
echo "  cw join <room-id>              # join a room"
echo "  cw continue 5                  # add 5 turns"
echo "  cw continue 5 --agent quant    # add turns for a specific agent"
echo "  cw status                      # check room/agent status"

if ! echo ":$PATH:" | grep -q ":$BIN_DIR:"; then
  echo ""
  echo "NOTE: $BIN_DIR is not in PATH. Add to your shell profile:"
  echo "  export PATH=\"$BIN_DIR:\$PATH\""
fi
