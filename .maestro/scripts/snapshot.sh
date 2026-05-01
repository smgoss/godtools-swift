#!/usr/bin/env bash
# Run all generated content flows and capture screenshots into a named snapshot dir.
#
# Usage:
#   .maestro/scripts/snapshot.sh <name> [--device <udid>]
#
# Example:
#   .maestro/scripts/snapshot.sh baseline --device 75D0CB15-...
#   .maestro/scripts/snapshot.sh current  --device 75D0CB15-...
#
# Output goes to .maestro/snapshots/<name>/<abbreviation>/<page>.png
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: $0 <snapshot-name> [--device <udid>]" >&2
    exit 64
fi

NAME=$1
shift

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
SNAPSHOT_DIR="$ROOT/.maestro/snapshots/$NAME"
FLOW_DIR="$ROOT/.maestro/flows/generated"

if ! command -v maestro >/dev/null 2>&1; then
    if [[ -x "$HOME/.maestro/bin/maestro" ]]; then
        export PATH="$PATH:$HOME/.maestro/bin"
    else
        echo "error: maestro CLI not on PATH" >&2
        exit 127
    fi
fi

mkdir -p "$SNAPSHOT_DIR"
echo "Snapshot dir: $SNAPSHOT_DIR"
echo "Flow dir:     $FLOW_DIR"

maestro "$@" test --include-tags=generated --env SNAPSHOT_DIR="$SNAPSHOT_DIR" "$FLOW_DIR"
