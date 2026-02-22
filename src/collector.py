"""
DroidPulse - ADB Data Collector
Collects device health data via ADB and parses into structured format.
"""

import subprocess
import re
import json
from datetime import datetime


def run_adb(command, device_id=None):
    """Run an ADB command and return the output as string."""
    cmd = ["adb"]
    if device_id:
        cmd += ["-s", device_id]
    cmd += command.split()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"[ERROR] ADB command timed out: {' '.join(cmd)}")
        return ""
    except FileNotFoundError:
        print("[ERROR] ADB not found. Install with: sudo dnf install android-tools")
        return ""


def get_connected_devices():
    """Get list of connected ADB device IDs."""
    output = run_adb("devices")
    devices = []
    for line in output.splitlines()[1:]:
        if "\tdevice" in line:
            devices.append(line.split("\t")[0])
    return devices


def get_device_info(device_id=None):
    """Collect basic device information."""
    props = {
        "model": "ro.product.model",
        "brand": "ro.product.brand",
        "device": "ro.product.device",
        "android_version": "ro.build.version.release",
        "sdk_level": "ro.build.version.sdk",
        "build_number": "ro.build.display.id",
        "serial": "ro.serialno",
        "hardware": "ro.hardware"
    }

    info = {}
    for key, prop in props.items():
        info[key] = run_adb(f"shell getprop {prop}", device_id)

    info["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return info


def get_battery(device_id=None):
    """Collect battery health data."""
    output = run_adb("shell dumpsys battery", device_id)
    battery = {}

    patterns = {
        "level": r"level:\s*(\d+)",
        "scale": r"scale:\s*(\d+)",
        "voltage": r"voltage:\s*(\d+)",
        "temperature": r"temperature:\s*(\d+)",
        "technology": r"technology:\s*(.+)",
        "status": r"status:\s*(\d+)",
        "health": r"health:\s*(\d+)",
        "ac_powered": r"AC powered:\s*(\w+)",
        "usb_powered": r"USB powered:\s*(\w+)",
        "wireless_powered": r"Wireless powered:\s*(\w+)",
        "present": r"present:\s*(\w+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            val = match.group(1)
            if val.isdigit():
                val = int(val)
            elif val.lower() in ("true", "false"):
                val = val.lower() == "true"
            battery[key] = val

    # Convert temperature from tenths of degree
    if "temperature" in battery:
        battery["temperature_celsius"] = battery["temperature"] / 10

    # Map status codes to readable strings
    status_map = {1: "Unknown", 2: "Charging", 3: "Discharging",
                  4: "Not Charging", 5: "Full"}
    health_map = {1: "Unknown", 2: "Good", 3: "Overheat",
                  4: "Dead", 5: "Over Voltage", 6: "Failure", 7: "Cold"}

    if "status" in battery:
        battery["status_text"] = status_map.get(battery["status"], "Unknown")
    if "health" in battery:
        battery["health_text"] = health_map.get(battery["health"], "Unknown")

    return battery


def get_storage(device_id=None):
    """Collect storage usage data."""
    output = run_adb("shell df -h", device_id)
    storage = []

    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 6:
            mount = parts[5]
            # Only include important partitions
            if mount in ("/data", "/storage/emulated"):
                storage.append({
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "use_percent": parts[4],
                    "mounted_on": mount
                })

    return storage


def get_memory(device_id=None):
    """Collect memory usage data."""
    output = run_adb("shell cat /proc/meminfo", device_id)
    memory = {}

    patterns = {
        "total_kb": r"MemTotal:\s+(\d+)",
        "free_kb": r"MemFree:\s+(\d+)",
        "available_kb": r"MemAvailable:\s+(\d+)",
        "buffers_kb": r"Buffers:\s+(\d+)",
        "cached_kb": r"Cached:\s+(\d+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            memory[key] = int(match.group(1))

    # Calculate usage percentage
    if "total_kb" in memory and "available_kb" in memory:
        used = memory["total_kb"] - memory["available_kb"]
        memory["used_kb"] = used
        memory["used_percent"] = round((used / memory["total_kb"]) * 100, 1)

    # Convert to MB for readability
    for key in list(memory.keys()):
        if key.endswith("_kb"):
            mb_key = key.replace("_kb", "_mb")
            memory[mb_key] = round(memory[key] / 1024, 1)

    # Get top memory consumers
    mem_output = run_adb("shell dumpsys meminfo", device_id)
    consumers = []
    for line in mem_output.splitlines():
        match = re.match(r"\s+([\d,]+)K:\s+(.+?)(?:\s+\(pid.*)?$", line)
        if match and len(consumers) < 10:
            consumers.append({
                "memory_kb": int(match.group(1).replace(",", "")),
                "process": match.group(2).strip()
            })
    memory["top_consumers"] = consumers

    return memory


def get_cpu(device_id=None):
    """Collect CPU usage data."""
    output = run_adb("shell dumpsys cpuinfo", device_id)
    cpu = {}

    # Parse load averages
    load_match = re.search(r"Load:\s+([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)", output)
    if load_match:
        cpu["load_1min"] = float(load_match.group(1))
        cpu["load_5min"] = float(load_match.group(2))
        cpu["load_15min"] = float(load_match.group(3))

    # Parse top CPU consumers
    consumers = []
    for line in output.splitlines():
        match = re.match(r"\s+([\d.]+)%\s+(\d+)/(.+?):\s+(.*)", line)
        if match and len(consumers) < 10:
            consumers.append({
                "cpu_percent": float(match.group(1)),
                "pid": int(match.group(2)),
                "process": match.group(3).strip(),
                "details": match.group(4).strip()
            })
    cpu["top_consumers"] = consumers

    return cpu


def get_network(device_id=None):
    """Collect network information."""
    network = {}

    # Parse WiFi info
    wifi_output = run_adb("shell dumpsys wifi", device_id)
    wifi_match = re.search(
        r'mWifiInfo SSID: "([^"]+)".*?RSSI: (-?\d+).*?'
        r'Link speed: (\d+)Mbps.*?Frequency: (\d+)MHz',
        wifi_output
    )
    if wifi_match:
        network["ssid"] = wifi_match.group(1)
        network["rssi"] = int(wifi_match.group(2))
        network["link_speed_mbps"] = int(wifi_match.group(3))
        network["frequency_mhz"] = int(wifi_match.group(4))

        # Determine band
        freq = network["frequency_mhz"]
        network["band"] = "5GHz" if freq >= 5000 else "2.4GHz"

        # Signal quality assessment
        rssi = network["rssi"]
        if rssi >= -50:
            network["signal_quality"] = "Excellent"
        elif rssi >= -60:
            network["signal_quality"] = "Good"
        elif rssi >= -70:
            network["signal_quality"] = "Fair"
        else:
            network["signal_quality"] = "Poor"

    # Parse IP configuration
    ip_output = run_adb("shell ip addr show wlan0", device_id)
    ip_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", ip_output)
    if ip_match:
        network["ip_address"] = ip_match.group(1)
        network["subnet_mask"] = ip_match.group(2)

    ipv6_match = re.search(r"inet6 ([\da-f:]+)/\d+ scope global", ip_output)
    if ipv6_match:
        network["ipv6_address"] = ipv6_match.group(1)

    # Get DNS
    dns1 = run_adb("shell getprop net.dns1", device_id)
    dns2 = run_adb("shell getprop net.dns2", device_id)
    network["dns"] = [d for d in [dns1, dns2] if d]

    # Get connection type
    conn_output = run_adb("shell dumpsys connectivity", device_id)
    if "WIFI" in conn_output:
        network["connection_type"] = "WiFi"
    elif "MOBILE" in conn_output:
        network["connection_type"] = "Mobile Data"
    else:
        network["connection_type"] = "Unknown"

    return network


def get_apps(device_id=None):
    """Collect installed apps information."""
    apps = {}

    all_pkgs = run_adb("shell pm list packages", device_id)
    third_party = run_adb("shell pm list packages -3", device_id)

    all_list = [p.replace("package:", "") for p in all_pkgs.splitlines() if p]
    third_list = [p.replace("package:", "") for p in third_party.splitlines() if p]

    apps["total_packages"] = len(all_list)
    apps["third_party_count"] = len(third_list)
    apps["system_count"] = len(all_list) - len(third_list)
    apps["third_party_apps"] = sorted(third_list)

    return apps


def get_error_logs(device_id=None):
    """Collect recent error logs."""
    output = run_adb("logcat -d *:E", device_id)
    lines = output.splitlines()

    # Get last 30 error lines
    recent = lines[-30:] if len(lines) > 30 else lines
    return {
        "total_errors": len(lines),
        "recent_errors": recent
    }


def collect_all(device_id=None):
    """Collect all device data and return as structured dictionary."""
    print(f"[DroidPulse] Collecting data from device: {device_id or 'default'}...")

    data = {
        "device_info": get_device_info(device_id),
        "battery": get_battery(device_id),
        "storage": get_storage(device_id),
        "memory": get_memory(device_id),
        "cpu": get_cpu(device_id),
        "network": get_network(device_id),
        "apps": get_apps(device_id),
        "error_logs": get_error_logs(device_id)
    }

    print("[DroidPulse] Data collection complete.")
    return data


# Run standalone for testing
if __name__ == "__main__":
    devices = get_connected_devices()
    if not devices:
        print("[ERROR] No devices found. Check USB connection and USB debugging.")
    else:
        print(f"[DroidPulse] Found devices: {devices}")
        data = collect_all(devices[0])
        print(json.dumps(data, indent=2))
