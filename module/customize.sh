SKIPUNZIP=1

ui_print "- Extracting module files..."
unzip -o "$ZIPFILE" -d "$MODPATH" >&2

case "$ARCH" in
  "arm64")
    ABI="arm64-v8a"
    ;;
  "x64")
    ABI="x86_64"
    ;;
  "riscv64")
    ABI="riscv64"
    ;;
  *)
    abort "! Unsupported architecture: $ARCH"
    ;;
esac

ui_print "- Device Architecture: $ARCH ($ABI)"

BIN_SOURCE="$MODPATH/binaries/$ABI/hymod"
BIN_TARGET="$MODPATH/hymod"

if [ ! -f "$BIN_SOURCE" ]; then
  abort "! Binary for $ABI not found in this zip!"
fi

ui_print "- Installing binary for $ABI..."
cp -f "$BIN_SOURCE" "$BIN_TARGET"

set_perm "$BIN_TARGET" 0 0 0755

rm -rf "$MODPATH/binaries"
rm -rf "$MODPATH/system"

BASE_DIR="/data/adb/hymo"
mkdir -p "$BASE_DIR"

if [ ! -f "$BASE_DIR/config.toml" ]; then
  ui_print "- Installing default config"
  # 注意：这里假设 zip 根目录有 config.toml，如果没有，unzip 步骤已经释放到了 MODPATH
  cat "$MODPATH/config.toml" > "$BASE_DIR/config.toml"
fi

IMG_FILE="$BASE_DIR/modules.img"
IMG_SIZE_MB=2048

if [ ! -f "$IMG_FILE" ]; then
    ui_print "- Creating 2GB ext4 image for module storage..."
    truncate -s ${IMG_SIZE_MB}M "$IMG_FILE"
    
    /system/bin/mke2fs -t ext4 -O ^has_journal -F "$IMG_FILE" >/dev/null 2>&1
    
    if [ $? -ne 0 ]; then
        ui_print "! Failed to format ext4 image"
    else
        ui_print "- Image created successfully (No Journal Mode)"
    fi
else
    ui_print "- Reusing existing modules.img"
fi

set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm "$BIN_TARGET" 0 0 0755

ui_print "- Installation complete"