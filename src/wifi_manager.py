"""
DroidPulse - WiFi Manager & Network Diagnostics
Handles ADB over WiFi and advanced network diagnostics.
"""

import subprocess
import re
import time
from collector import run_adb


def get_connection_type(device_id=None):
    """Detect if device is connected via USB or WiFi."""
    if device_id and ":" in device_id:
        return "WiFi"
    return "USB"


def get_phone_ip(device_id=None):
    """Get the phone's WiFi IP address."""
    output = run_adb("shell ip addr show wlan0", device_id)
    match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", output)
    if match:
        return match.group(1)
    return None


def switch_to_wifi(device_id=None, port=5555):
    """Switch ADB connection from USB to WiFi."""
    print(f"[DroidPulse] Switching to WiFi mode on port {port}...")

    # Get phone IP while still on USB
    phone_ip = get_phone_ip(device_id)
    if not phone_ip:
        print("[ERROR] Could not find phone IP. Ensure WiFi is connected.")
        return None

    # Enable TCP/IP mode
    output = run_adb(f"tcpip {port}", device_id)
    print(f"[DroidPulse] TCP/IP mode enabled: {output}")

    # Wait for device to switch
    time.sleep(2)

    # Connect over WiFi
    wifi_target = f"{phone_ip}:{port}"
    output = run_adb(f"connect {wifi_target}")
    print(f"[DroidPulse] WiFi connection: {output}")

    if "connected" in output.lower():
        print(f"[DroidPulse] Connected wirelessly to {wifi_target}")
        print("[DroidPulse] You can now unplug the USB cable.")
        return wifi_target
    else:
        print("[ERROR] WiFi connection failed. Check network.")
        return None


def switch_to_usb(device_id=None):
    """Switch ADB connection back to USB."""
    print("[DroidPulse] Switching back to USB mode...")
    if device_id and ":" in device_id:
        run_adb(f"disconnect {device_id}")
    output = run_adb("usb", device_id)
    print(f"[DroidPulse] USB mode: {output}")


def ping_device(phone_ip, count=5):
    """Ping the phone from Fedora to measure latency."""
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "2", phone_ip],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout

        # Parse ping statistics
        stats = {}
        packets_match = re.search(
            r"(\d+) packets transmitted, (\d+) received.+?(\d+)% packet loss",
            output
        )
        if packets_match:
            stats["packets_sent"] = int(packets_match.group(1))
            stats["packets_received"] = int(packets_match.group(2))
            stats["packet_loss"] = f"{packets_match.group(3)}%"

        rtt_match = re.search(
            r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)",
            output
        )
        if rtt_match:
            stats["rtt_min_ms"] = float(rtt_match.group(1))
            stats["rtt_avg_ms"] = float(rtt_match.group(2))
            stats["rtt_max_ms"] = float(rtt_match.group(3))
            stats["rtt_mdev_ms"] = float(rtt_match.group(4))

        return stats

    except subprocess.TimeoutExpired:
        return {"error": "Ping timed out"}
    except Exception as e:
        return {"error": str(e)}


def dns_test(device_id=None):
    """Test DNS resolution on the device."""
    tests = {}
    targets = ["google.com", "github.com"]

    for target in targets:
        output = run_adb(f"shell ping -c 1 -W 2 {target}", device_id)
        if "1 received" in output or "1 packets received" in output:
            # Extract IP
            ip_match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)", output)
            # Extract time
            time_match = re.search(r"time[=<]([\d.]+)\s*ms", output)
            tests[target] = {
                "resolved": True,
                "ip": ip_match.group(1) if ip_match else "N/A",
                "latency_ms": float(time_match.group(1)) if time_match else None
            }
        else:
            tests[target] = {"resolved": False, "ip": None, "latency_ms": None}

    return tests


def get_wifi_details(device_id=None):
    """Get detailed WiFi information from the device."""
    wifi = {}

    # WiFi info from dumpsys
    output = run_adb("shell dumpsys wifi", device_id)

    # Parse primary mWifiInfo
    match = re.search(
        r'mWifiInfo SSID: "([^"]+)".*?'
        r'Security type: (\d+).*?'
        r'Wi-Fi standard: (\d+).*?'
        r'RSSI: (-?\d+).*?'
        r'Link speed: (\d+)Mbps.*?'
        r'Tx Link speed: (\d+)Mbps.*?'
        r'Rx Link speed: (\d+)Mbps.*?'
        r'Frequency: (\d+)MHz',
        output
    )
    if match:
        wifi["ssid"] = match.group(1)
        wifi["security_type"] = int(match.group(2))
        wifi["wifi_standard"] = int(match.group(3))
        wifi["rssi"] = int(match.group(4))
        wifi["link_speed_mbps"] = int(match.group(5))
        wifi["tx_speed_mbps"] = int(match.group(6))
        wifi["rx_speed_mbps"] = int(match.group(7))
        wifi["frequency_mhz"] = int(match.group(8))

        # Determine band and channel width
        freq = wifi["frequency_mhz"]
        wifi["band"] = "5GHz" if freq >= 5000 else "2.4GHz"

        # WiFi standard mapping
        standard_map = {4: "WiFi 4 (802.11n)", 5: "WiFi 5 (802.11ac)", 6: "WiFi 6 (802.11ax)"}
        wifi["wifi_standard_name"] = standard_map.get(wifi["wifi_standard"], f"Unknown ({wifi['wifi_standard']})")

        # Security type mapping
        sec_map = {0: "Open", 1: "WEP", 2: "WPA-PSK", 3: "WPA-EAP", 4: "WPA3-SAE", 5: "WPA3-Suite-B", 6: "OWE"}
        wifi["security_name"] = sec_map.get(wifi["security_type"], f"Unknown ({wifi['security_type']})")

        # Signal quality
        rssi = wifi["rssi"]
        if rssi >= -50:
            wifi["signal_quality"] = "Excellent"
            wifi["signal_percent"] = min(100, 2 * (rssi + 100))
        elif rssi >= -60:
            wifi["signal_quality"] = "Good"
            wifi["signal_percent"] = min(100, 2 * (rssi + 100))
        elif rssi >= -70:
            wifi["signal_quality"] = "Fair"
            wifi["signal_percent"] = min(100, 2 * (rssi + 100))
        else:
            wifi["signal_quality"] = "Poor"
            wifi["signal_percent"] = max(0, 2 * (rssi + 100))

    # Get routing info
    route_output = run_adb("shell ip route", device_id)
    gw_match = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", route_output)
    if gw_match:
        wifi["gateway"] = gw_match.group(1)

    return wifi


def collect_network_diagnostics(device_id=None):
    """Run full network diagnostic suite."""
    print("[DroidPulse] Running network diagnostics...")

    diag = {}

    # Connection type
    diag["connection_type"] = get_connection_type(device_id)
    print(f"  Connection: {diag['connection_type']}")

    # WiFi details
    diag["wifi"] = get_wifi_details(device_id)
    print(f"  WiFi: {diag['wifi'].get('ssid', 'N/A')} ({diag['wifi'].get('signal_quality', 'N/A')})")

    # Phone IP
    phone_ip = get_phone_ip(device_id)
    diag["phone_ip"] = phone_ip
    print(f"  Phone IP: {phone_ip}")

    # Ping test (Fedora to phone)
    if phone_ip:
        print(f"  Pinging {phone_ip}...")
        diag["ping"] = ping_device(phone_ip)
        avg = diag["ping"].get("rtt_avg_ms", "N/A")
        loss = diag["ping"].get("packet_loss", "N/A")
        print(f"  Ping: avg={avg}ms, loss={loss}")
    else:
        diag["ping"] = {"error": "No phone IP found"}

    # DNS test
    print("  Testing DNS...")
    diag["dns_tests"] = dns_test(device_id)
    for host, result in diag["dns_tests"].items():
        status = "OK" if result["resolved"] else "FAIL"
        print(f"  DNS {host}: {status}")

    print("[DroidPulse] Network diagnostics complete.")
    return diag


# Run standalone for testing
if __name__ == "__main__":
    from collector import get_connected_devices

    devices = get_connected_devices()
    if not devices:
        print("[ERROR] No devices found.")
    else:
        print(f"[DroidPulse] Device: {devices[0]}")
        print()

        # Run diagnostics
        import json
        diag = collect_network_diagnostics(devices[0])
        print("\n=== FULL DIAGNOSTICS ===")
        print(json.dumps(diag, indent=2))

        # Test WiFi switch
        print("\n--- WiFi Manager ---")
        print("To switch to WiFi: python wifi_manager.py --wifi")
        print("To switch to USB:  python wifi_manager.py --usb")
