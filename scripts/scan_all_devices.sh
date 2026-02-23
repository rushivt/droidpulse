#!/bin/bash
# DroidPulse - Multi-Device Scanner
# Scans all connected ADB devices and generates reports

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_DIR/src"
VENV_DIR="$PROJECT_DIR/venv"

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "[ERROR] Virtual environment not found at $VENV_DIR"
    echo "  Run: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# Check ADB
if ! command -v adb &> /dev/null; then
    echo "[ERROR] ADB not found. Install with: sudo dnf install android-tools"
    exit 1
fi

# Get connected devices
DEVICES=$(adb devices | grep -w "device" | awk '{print $1}')
DEVICE_COUNT=$(echo "$DEVICES" | grep -c .)

if [ -z "$DEVICES" ]; then
    echo "[ERROR] No ADB devices found."
    echo "  - Check USB connections"
    echo "  - Ensure USB debugging is enabled"
    exit 1
fi

echo "============================================"
echo "  DroidPulse - Multi-Device Scanner"
echo "============================================"
echo ""
echo "  Found $DEVICE_COUNT device(s):"
echo ""

# List all devices
INDEX=1
for DEVICE in $DEVICES; do
    MODEL=$(adb -s "$DEVICE" shell getprop ro.product.model 2>/dev/null)
    BRAND=$(adb -s "$DEVICE" shell getprop ro.product.brand 2>/dev/null)
    echo "  [$INDEX] $BRAND $MODEL ($DEVICE)"
    INDEX=$((INDEX + 1))
done

echo ""
echo "============================================"
echo ""

# Parse arguments
REPORT_FLAG=""
JSON_FLAG=""
VERBOSE_FLAG=""

for arg in "$@"; do
    case $arg in
        --report)  REPORT_FLAG="--report" ;;
        --json)    JSON_FLAG="--json" ;;
        --verbose) VERBOSE_FLAG="--verbose" ;;
    esac
done

# Scan each device
for DEVICE in $DEVICES; do
    MODEL=$(adb -s "$DEVICE" shell getprop ro.product.model 2>/dev/null)
    BRAND=$(adb -s "$DEVICE" shell getprop ro.product.brand 2>/dev/null)

    echo ">>> Scanning: $BRAND $MODEL ($DEVICE)"
    echo "--------------------------------------------"

    cd "$SRC_DIR"
    python main.py --device "$DEVICE" $REPORT_FLAG $JSON_FLAG $VERBOSE_FLAG

    echo ""
    echo ">>> Scan complete: $BRAND $MODEL"
    echo "============================================"
    echo ""
done

echo "[DroidPulse] All devices scanned."

# Show cron job example
if [ "$1" == "--help-cron" ]; then
    echo ""
    echo "To schedule automatic scans, add a cron job:"
    echo ""
    echo "  # Edit crontab"
    echo "  crontab -e"
    echo ""
    echo "  # Run DroidPulse every hour with report generation"
    echo "  0 * * * * $SCRIPT_DIR/scan_all_devices.sh --report"
    echo ""
    echo "  # Run DroidPulse every 6 hours"
    echo "  0 */6 * * * $SCRIPT_DIR/scan_all_devices.sh --report"
    echo ""
    echo "  # Run DroidPulse daily at 9am"
    echo "  0 9 * * * $SCRIPT_DIR/scan_all_devices.sh --report"
    echo ""
fi
