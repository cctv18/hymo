#!/system/bin/sh

MODDIR="${0%/*}"
BASE_DIR="/data/adb/hymo"
LOG_FILE="$BASE_DIR/daemon.log"

mkdir -p "$BASE_DIR"

if [ -f "$LOG_FILE" ]; then
    rm "$LOG_FILE"
fi

log() {
    echo "[Wrapper] $1" >> "$LOG_FILE"
}

log "Starting Hymod..."


BINARY="$MODDIR/hymod"
if [ ! -f "$BINARY" ]; then
    log "ERROR: Binary not found at $BINARY"
    exit 1
fi

chmod 755 "$BINARY"

"$BINARY" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

log "Hymod exited with code $EXIT_CODE"

if [ "$EXIT_CODE" = "0" ]; then
    /data/adb/ksud kernel notify-module-mounted
fi

exit $EXIT_CODE