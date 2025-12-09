#!/system/bin/sh
# Hymo Hot Mount Script
MODULE_ID=$1
if [ -z "$MODULE_ID" ]; then
  echo "Usage: $0 <module_id>"
  exit 1
fi

# Remove marker file
rm -f "/data/adb/hymo/run/hot_unmounted/$MODULE_ID"

# Enable module (if it was disabled normally)
rm -f "/data/adb/modules/$MODULE_ID/disable"

# Use targeted add command instead of full reload
/data/adb/modules/hymo/hymod add "$MODULE_ID"
