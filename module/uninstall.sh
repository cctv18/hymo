#!/system/bin/sh
############################################
# hymo uninstall.sh
# Cleanup script for metamodule removal
############################################

BASE_DIR="/data/adb/hymo"
MNT_DIR="/dev/hymo_mirror"

if mountpoint -q "$MNT_DIR"; then
    umount "$MNT_DIR" 2>/dev/null || umount -l "$MNT_DIR"
fi

rm -rf "$BASE_DIR"

exit 0