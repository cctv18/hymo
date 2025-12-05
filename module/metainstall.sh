#!/system/bin/sh

export KSU_HAS_METAMODULE="true"
export KSU_METAMODULE="hymo"

BASE_DIR="/data/adb/hymo"

ui_print "- Using Hymo metainstall"

install_module


ui_print "- Installation complete"