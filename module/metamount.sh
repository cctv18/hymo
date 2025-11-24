#!/system/bin/sh
# Hybrid Mount Startup Script

MODDIR="${0%/*}"
BASE_DIR="/data/adb/meta-hybrid"
IMG_FILE="$BASE_DIR/modules.img"
MNT_DIR="$BASE_DIR/mnt"
LOG_FILE="$BASE_DIR/daemon.log"

# Ensure base directory exists
mkdir -p "$BASE_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [Wrapper] $1" >> "$LOG_FILE"
}

log "Starting Hybrid Mount..."

# 1. Mount modules.img if not mounted
if ! mountpoint -q "$MNT_DIR"; then
    if [ -f "$IMG_FILE" ]; then
        log "Mounting modules.img..."
        mkdir -p "$MNT_DIR"
        # Attempt to mount
        mount -t ext4 -o loop,rw,noatime "$IMG_FILE" "$MNT_DIR"
        if [ $? -ne 0 ]; then
            log "ERROR: Failed to mount modules.img"
        fi
    else
        log "WARNING: modules.img not found."
    fi
fi

# 2. Prepare Rust binary
BINARY="$MODDIR/meta-hybrid"
if [ ! -f "$BINARY" ]; then
    log "ERROR: Binary not found at $BINARY"
    exit 1
fi

chmod 755 "$BINARY"

# 3. Execute Rust Binary
"$BINARY" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

log "Hybrid Mount exited with code $EXIT_CODE"

# 4. Notify KernelSU
if [ "$EXIT_CODE" = "0" ]; then
    /data/adb/ksud kernel notify-module-mounted
fi

exit $EXIT_CODE