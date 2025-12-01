#!/system/bin/sh

ui_print "- Detecting device architecture..."

# Detect architecture using ro.product.cpu.abi
ABI=$(grep_get_prop ro.product.cpu.abi)
ui_print "- Detected ABI: $ABI"

# Select appropriate binary based on ABI
case "$ABI" in
    arm64-v8a)
        BINARY_NAME="hymo-arm64-v8a"
        ;;
    armeabi-v7a|armeabi)
        BINARY_NAME="hymo-armeabi-v7a"
        ;;
    x86_64)
        BINARY_NAME="hymo-x86_64"
        ;;
    x86)
        BINARY_NAME="hymo-x86"
        ;;
    *)
        abort "! Unsupported architecture: $ABI"
        ;;
esac

ui_print "- Selected binary: $BINARY_NAME"

# Verify binary exists
if [ ! -f "$MODPATH/$BINARY_NAME" ]; then
    abort "! Binary not found: $BINARY_NAME"
fi

# Create symlink for easy access (optional)
ln -sf "$BINARY_NAME" "$MODPATH/hymo" 2>/dev/null

# Set permissions for the selected binary
chmod 755 "$MODPATH/$BINARY_NAME"

# Remove unused architecture binaries to save space
ui_print "- Cleaning unused binaries..."
for binary in hymo-arm64-v8a hymo-armeabi-v7a hymo-x86_64 hymo-x86; do
    if [ "$binary" != "$BINARY_NAME" ] && [ -f "$MODPATH/$binary" ]; then
        rm -f "$MODPATH/$binary"
        ui_print "  Removed: $binary"
    fi
done

# Base directory setup
BASE_DIR="/data/adb/hymo"
mkdir -p "$BASE_DIR"

# Handle Config
if [ ! -f "$BASE_DIR/config.toml" ]; then
  ui_print "- Installing default config"
  cat "$MODPATH/config.toml" > "$BASE_DIR/config.toml"
fi

# Handle Image Creation (Borrowed from meta-overlayfs)
IMG_FILE="$BASE_DIR/modules.img"
IMG_SIZE_MB=2048

if [ ! -f "$IMG_FILE" ]; then
    ui_print "- Creating 2GB ext4 image for module storage..."
    truncate -s ${IMG_SIZE_MB}M "$IMG_FILE"
    
    # [Stealth Update] Remove journal to prevent creating jbd2 sysfs node/threads
    /system/bin/mke2fs -t ext4 -O ^has_journal -F "$IMG_FILE" >/dev/null 2>&1
    
    if [ $? -ne 0 ]; then
        ui_print "! Failed to format ext4 image"
    else
        ui_print "- Image created successfully (No Journal Mode)"
    fi
else
    ui_print "- Reusing existing modules.img"
fi

ui_print "- Installation complete"