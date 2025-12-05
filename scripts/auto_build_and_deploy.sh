#!/usr/bin/env bash
set -euo pipefail

# Auto build + deploy script for Hymo
# Usage examples:
#  ./scripts/auto_build_and_deploy.sh --ndk /home/an/android-ndk/android-ndk-r27c --node 20.19.1 --push --install
#  ./scripts/auto_build_and_deploy.sh --help

NODE_VERSION="20.19.1"
NDK_HOME=""
PUSH=false
INSTALL=false
DEVICE_PATH="/sdcard"
SKIP_WEBUI=false
CLEAN=true

print_help(){
  cat <<'EOF'
Usage: auto_build_and_deploy.sh [options]

Options:
  --ndk PATH          Set ANDROID_NDK_HOME (default: try /home/an/android-ndk/android-ndk-r27c then /home/an/android-ndk)
  --node VERSION      Node version to install/use via nvm (default: 20.19.1)
  --no-clean          Skip `cargo clean` before build
  --skip-webui        Skip building WebUI (faster)
  --push              Push resulting zip to device (to $DEVICE_PATH)
  --install           After push, run ksud module install on device (requires root)
  --device-path PATH  Target directory on device for push (default: /sdcard)
  -h, --help          Show this help

Examples:
  # Full clean build, push to /sdcard and install via ksud
  ./scripts/auto_build_and_deploy.sh --ndk /home/an/android-ndk/android-ndk-r27c --push --install

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ndk)
      NDK_HOME="$2"; shift 2;;
    --node)
      NODE_VERSION="$2"; shift 2;;
    --push)
      PUSH=true; shift;;
    --install)
      INSTALL=true; shift;;
    --device-path)
      DEVICE_PATH="$2"; shift 2;;
    --skip-webui)
      SKIP_WEBUI=true; shift;;
    --no-clean)
      CLEAN=false; shift;;
    -h|--help)
      print_help; exit 0;;
    *)
      echo "Unknown arg: $1"; print_help; exit 2;;
  esac
done

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Project root: $ROOT_DIR"

# choose NDK if not provided
if [ -z "$NDK_HOME" ]; then
  if [ -d "/home/an/android-ndk/android-ndk-r27c" ]; then
    NDK_HOME="/home/an/android-ndk/android-ndk-r27c"
  elif [ -d "/home/an/android-ndk" ]; then
    NDK_HOME="/home/an/android-ndk"
  else
    echo "ANDROID NDK not found. Please pass --ndk PATH" >&2
    exit 1
  fi
fi

echo "Using NDK: $NDK_HOME"

# Ensure nvm and Node
export NVM_DIR="$HOME/.nvm"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  echo "nvm not found, installing..."
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.6/install.sh | bash
fi
# shellcheck source=/dev/null
. "$NVM_DIR/nvm.sh"

echo "Installing/using Node $NODE_VERSION via nvm"
nvm install "$NODE_VERSION"
nvm use "$NODE_VERSION"

echo "Node: $(node --version)  npm: $(npm --version)"

export ANDROID_NDK_HOME="$NDK_HOME"

cd "$ROOT_DIR"

if [ "$CLEAN" = true ]; then
  echo "Running cargo clean..."
  cargo clean
fi

BUILD_CMD=(cargo run -p xtask -- build --release)
if [ "$SKIP_WEBUI" = true ]; then
  BUILD_CMD+=(-- --skip-webui)
fi

echo "Running: ${BUILD_CMD[*]}"
"${BUILD_CMD[@]}"

ZIP_PATH="$ROOT_DIR/output/"$(ls -1t "$ROOT_DIR/output"/*.zip | head -n1 | xargs -n1 basename)
if [ ! -f "$ROOT_DIR/output/$(basename "$ZIP_PATH")" ]; then
  echo "Build finished but zip not found in output/" >&2
  ls -la "$ROOT_DIR/output" || true
  exit 1
fi

ZIP_LOCAL="$ROOT_DIR/output/$(basename "$ZIP_PATH")"
echo "Built ZIP: $ZIP_LOCAL"

if [ "$PUSH" = true ]; then
  DEVICE_ZIP="$DEVICE_PATH/$(basename "$ZIP_LOCAL")"
  echo "Pushing $ZIP_LOCAL -> $DEVICE_ZIP"
  adb push "$ZIP_LOCAL" "$DEVICE_ZIP"
  adb shell chmod 0644 "$DEVICE_ZIP" || true

  if [ "$INSTALL" = true ]; then
    echo "Installing on device via ksud..."
    # Try to detect ksud path then run with root
    KSUD_PATH="$(adb shell 'which ksud' 2>/dev/null | tr -d '\r' || true)"
    if [ -z "$KSUD_PATH" ] || [ "$KSUD_PATH" = "which ksud" ]; then
      # common location from your device
      KSUD_PATH="/data/adb/ksu/bin/ksud"
    fi
    echo "Using ksud path: $KSUD_PATH"
    adb shell su -c "$KSUD_PATH module install '$DEVICE_ZIP'"
  fi
fi

echo "Done. Built: $ZIP_LOCAL"

exit 0
