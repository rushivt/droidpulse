#!/bin/bash
# DroidPulse - ADB Command Wrappers
# Collects device health data via ADB

DEVICE_ID="${1:-}"

# Helper: run adb command with optional device targeting
run_adb() {
    if [ -n "$DEVICE_ID" ]; then
        adb -s "$DEVICE_ID" "$@"
    else
        adb "$@"
    fi
}

# Get basic device info
get_device_info() {
    echo "=== DEVICE INFO ==="
    echo "Model: $(run_adb shell getprop ro.product.model)"
    echo "Brand: $(run_adb shell getprop ro.product.brand)"
    echo "Device: $(run_adb shell getprop ro.product.device)"
    echo "Android Version: $(run_adb shell getprop ro.build.version.release)"
    echo "SDK Level: $(run_adb shell getprop ro.build.version.sdk)"
    echo "Build Number: $(run_adb shell getprop ro.build.display.id)"
    echo "Serial: $(run_adb shell getprop ro.serialno)"
    echo "Hardware: $(run_adb shell getprop ro.hardware)"
}

# Get battery health data
get_battery() {
    echo "=== BATTERY ==="
    run_adb shell dumpsys battery
}

# Get storage usage
get_storage() {
    echo "=== STORAGE ==="
    run_adb shell df -h
}

# Get memory info
get_memory() {
    echo "=== MEMORY ==="
    run_adb shell cat /proc/meminfo | head -5
    echo "--- Top Memory Consumers ---"
    run_adb shell dumpsys meminfo | head -20
}

# Get CPU usage
get_cpu() {
    echo "=== CPU ==="
    run_adb shell dumpsys cpuinfo | head -20
}

# Get network info
get_network() {
    echo "=== NETWORK ==="
    echo "--- WiFi Info ---"
    run_adb shell dumpsys wifi | grep -E "mWifiInfo|SSID|BSSID|RSSI|Link speed|Frequency"
    echo "--- IP Configuration ---"
    run_adb shell ip addr show wlan0
    echo "--- DNS ---"
    run_adb shell getprop net.dns1
    run_adb shell getprop net.dns2
}

# Get installed packages
get_apps() {
    echo "=== INSTALLED APPS ==="
    echo "Total packages: $(run_adb shell pm list packages | wc -l)"
    echo "Third-party apps: $(run_adb shell pm list packages -3 | wc -l)"
    echo "--- Third-party App List ---"
    run_adb shell pm list packages -3
}

# Get running processes
get_processes() {
    echo "=== RUNNING PROCESSES ==="
    run_adb shell ps -A | head -20
}

# Get recent error logs
get_logs() {
    echo "=== RECENT ERROR LOGS ==="
    run_adb logcat -d *:E | tail -30
}

# Run all checks
run_all() {
    get_device_info
    echo ""
    get_battery
    echo ""
    get_storage
    echo ""
    get_memory
    echo ""
    get_cpu
    echo ""
    get_network
    echo ""
    get_apps
    echo ""
    get_processes
    echo ""
    get_logs
}

# Main: run specific check or all
case "${2:-all}" in
    info)      get_device_info ;;
    battery)   get_battery ;;
    storage)   get_storage ;;
    memory)    get_memory ;;
    cpu)       get_cpu ;;
    network)   get_network ;;
    apps)      get_apps ;;
    processes) get_processes ;;
    logs)      get_logs ;;
    all)       run_all ;;
    *)         echo "Usage: $0 [device_id] [info|battery|storage|memory|cpu|network|apps|processes|logs|all]" ;;
esac
