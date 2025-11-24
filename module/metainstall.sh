#!/system/bin/sh
############################################
# meta-hybrid metainstall.sh
############################################

# This tells KernelSU it's a metamodule
export KSU_HAS_METAMODULE="true"
export KSU_METAMODULE="meta-hybrid"

# Constants
BASE_DIR="/data/adb/meta-hybrid"
IMG_FILE="$BASE_DIR/modules.img"
MNT_DIR="$BASE_DIR/mnt"

# Helper to mount image if needed
ensure_image_mounted() {
    if ! mountpoint -q "$MNT_DIR" 2>/dev/null; then
        mkdir -p "$MNT_DIR"
        mount -t ext4 -o loop,rw,noatime "$IMG_FILE" "$MNT_DIR"
    fi
}

# 1. Determine if we need to move files to the image
# If the module has a system/ folder and doesn't explicitly skip, we move it.
module_requires_move() {
    if [ -f "$MODPATH/skip_mount" ]; then return 1; fi
    if [ ! -d "$MODPATH/system" ]; then return 1; fi
    return 0
}

# 2. The installation process
ui_print "- Using Hybrid Mount metainstall"

# Standard installation
install_module

# Post-install: Move content to image
if module_requires_move; then
    ui_print "- Moving module content to Hybrid image..."
    
    if [ ! -f "$IMG_FILE" ]; then
        ui_print "! Error: modules.img not found. Please reinstall Meta-Hybrid."
    else
        ensure_image_mounted
        
        if mountpoint -q "$MNT_DIR"; then
            # Create destination in image
            MOD_IMG_DIR="$MNT_DIR/$MODID"
            mkdir -p "$MOD_IMG_DIR"
            
            # Move partitions
            for partition in system vendor product system_ext odm oem; do
                if [ -d "$MODPATH/$partition" ]; then
                    ui_print "  Moving $partition..."
                    cp -af "$MODPATH/$partition" "$MOD_IMG_DIR/"
                    rm -rf "$MODPATH/$partition"
                fi
            done
            
            # Ensure permissions (rough fix)
            chmod -R u+rwX,go+rX "$MOD_IMG_DIR"
            chcon -R u:object_r:system_file:s0 "$MOD_IMG_DIR" 2>/dev/null
            
            ui_print "- Content moved to image storage"
        else
            ui_print "! Error: Failed to mount image. Files kept in standard path."
        fi
    fi
else
    ui_print "- Skipping move to image (skip_mount or no system files)"
fi

ui_print "- Installation complete"