"""
DroidPulse - AI-Powered Android Device Health Dashboard
Main entry point.
"""

import argparse
import json
from collector import collect_all, get_connected_devices
from analyzer import analyze
from dashboard import display
from wifi_manager import collect_network_diagnostics


def main():
    parser = argparse.ArgumentParser(
        description="DroidPulse - AI-Powered Android Device Health Dashboard"
    )
    parser.add_argument("-d", "--device", help="Target device ID (default: first found)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show raw JSON data")
    parser.add_argument("-j", "--json", action="store_true", help="Output JSON only")
    parser.add_argument("-r", "--report", action="store_true", help="Generate HTML report")
    parser.add_argument("-w", "--wifi", action="store_true", help="Switch to WiFi ADB mode")
    parser.add_argument("--usb", action="store_true", help="Switch back to USB ADB mode")
    args = parser.parse_args()

    # Handle WiFi/USB switching
    if args.wifi:
        from wifi_manager import switch_to_wifi
        switch_to_wifi()
        return
    if args.usb:
        from wifi_manager import switch_to_usb
        switch_to_usb()
        return

    # Find devices
    devices = get_connected_devices()
    if not devices:
        print("[ERROR] No ADB devices found.")
        print("  - Check USB connection")
        print("  - Ensure USB debugging is enabled")
        print("  - Run 'adb devices' to verify")
        return

    device_id = args.device if args.device else devices[0]
    if device_id not in devices:
        print(f"[ERROR] Device {device_id} not found.")
        print(f"  Available devices: {devices}")
        return

    # Collect device data
    data = collect_all(device_id)

    # Collect network diagnostics
    net_diag = collect_network_diagnostics(device_id)
    data["network_diagnostics"] = net_diag

    # Run AI analysis
    analysis = analyze(data)

    # Output based on flags
    if args.json:
        output = {"device_data": data, "analysis": analysis}
        print(json.dumps(output, indent=2))
    elif args.verbose:
        print("\n=== RAW DEVICE DATA ===")
        print(json.dumps(data, indent=2))
        print("\n=== AI ANALYSIS ===")
        print(json.dumps(analysis, indent=2))
        print("\n=== DASHBOARD ===")
        display(data, analysis)
    else:
        display(data, analysis)

    # Generate HTML report if requested
    if args.report:
        try:
            from reporter import generate_report
            report_path = generate_report(data, analysis)
            print(f"\n[DroidPulse] HTML report saved: {report_path}")
        except ImportError:
            print("\n[DroidPulse] HTML reporter not yet implemented.")


if __name__ == "__main__":
    main()
