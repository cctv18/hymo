#!/system/bin/sh

ui_print "- Detecting device architecture..."

# Detect architecture using ro.product.cpu.abi
ABI=$(grep_get_prop ro.product.cpu.abi)
ui_print "- Detected ABI: $ABI"

# Select the correct binary based on architecture
case "$ABI" in
    arm64-v8a)
        ui_print "- Selected architecture: ARM64"
        ARCH_BINARY="arm64-v8a/magic_mount_rs"
        ;;
    armeabi-v7a)
        ui_print "- Selected architecture: ARM"
        ARCH_BINARY="armeabi-v7a/magic_mount_rs"
        ;;
    x86_64)
        ui_print "- Selected architecture: AMD64"
        ARCH_BINARY="x86_64/magic_mount_rs"
        ;;
    *)
        abort "! Unsupported architecture: $ABI"
        ;;
esac

# Verify the selected binary exists
if [ ! -f "$MODPATH/bin/$ARCH_BINARY" ]; then
    abort "! Binary not found: $ARCH_BINARY"
fi

ui_print "- Installing $ARCH_BINARY as meta-mm"

# Rename the selected binary to the generic name
mv "$MODPATH/bin/$ARCH_BINARY" "$MODPATH/meta-mm" || abort "! Failed to rename binary"

# Remove the unused binary
rm -rf "$MODPATH/bin"

# Ensure the binary is executable
chmod 755 "$MODPATH/meta-mm" || abort "! Failed to set permissions"

ui_print "- Architecture-specific binary installed successfully"

ui_print "- Installation complete"
ui_print "- Image is ready for module installations"
