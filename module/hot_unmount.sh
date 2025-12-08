#!/system/bin/sh
# Hymo Hot Unmount Script
MODULE_ID=$1
if [ -z "$MODULE_ID" ]; then
  echo "Usage: $0 <module_id>"
  exit 1
fi

# Create marker file to indicate hot unmount state
mkdir -p "/data/adb/hymo/run/hot_unmounted"
touch "/data/adb/hymo/run/hot_unmounted/$MODULE_ID"

# Reload HymoFS
/data/adb/modules/hymo/hymod reload
