# DroidPulse Runbook

## Table of Contents

1. [Quick Start](#quick-start)
2. [Common ADB Commands](#common-adb-commands)
3. [Troubleshooting](#troubleshooting)
4. [Scheduled Scans](#scheduled-scans)
5. [Architecture](#architecture)

---

## Quick Start

### First Time Setup

```bash
# 1. Clone the repo
git clone https://github.com/rushivt/droidpulse.git
cd droidpulse

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Set API key
echo 'GROQ_API_KEY=your-key-here' > .env

# 4. Connect Android device via USB with USB Debugging enabled

# 5. Verify connection
adb devices

# 6. Run DroidPulse
cd src
python main.py
```

### Daily Usage

```bash
cd ~/Desktop/droidpulse
source venv/bin/activate

# Terminal dashboard
cd src && python main.py

# Generate HTML report
python main.py --report

# Scan all connected devices
cd .. && ./scripts/scan_all_devices.sh --report
```

---

## Common ADB Commands

### Device Management

| Command | Description |
|---|---|
| `adb devices` | List connected devices |
| `adb -s <id> shell` | Open shell on specific device |
| `adb kill-server` | Stop ADB server |
| `adb start-server` | Start ADB server |
| `adb reboot` | Reboot device |
| `adb usb` | Switch to USB mode |
| `adb tcpip 5555` | Enable WiFi ADB mode |

### Device Information

| Command | Description |
|---|---|
| `adb shell getprop ro.product.model` | Get device model |
| `adb shell getprop ro.build.version.release` | Get Android version |
| `adb shell dumpsys battery` | Battery health info |
| `adb shell df -h` | Storage usage |
| `adb shell cat /proc/meminfo` | Memory info |
| `adb shell dumpsys cpuinfo` | CPU usage |
| `adb shell dumpsys wifi` | WiFi details |

### App Management

| Command | Description |
|---|---|
| `adb shell pm list packages` | List all packages |
| `adb shell pm list packages -3` | List third-party apps |
| `adb install app.apk` | Install an app |
| `adb uninstall com.package.name` | Uninstall an app |
| `adb shell am force-stop com.package.name` | Force stop an app |
| `adb shell pm clear com.package.name` | Clear app cache/data |

### File Transfer

| Command | Description |
|---|---|
| `adb push local_file /sdcard/` | Copy file to device |
| `adb pull /sdcard/file .` | Copy file from device |

### Logging

| Command | Description |
|---|---|
| `adb logcat` | View live logs |
| `adb logcat -d *:E` | Dump error logs |
| `adb logcat -c` | Clear log buffer |
| `adb logcat -d > device_log.txt` | Save logs to file |

### Network

| Command | Description |
|---|---|
| `adb shell ip addr show wlan0` | WiFi IP address |
| `adb shell ip route` | Routing table |
| `adb shell ping -c 5 google.com` | Test connectivity |
| `adb shell dumpsys connectivity` | Connection details |
| `adb shell getprop net.dns1` | DNS server |

---

## Troubleshooting

### ADB Device Not Found

**Symptom:** `adb devices` shows empty list.

**Solutions:**
1. Check USB cable is connected properly
2. Ensure USB Debugging is enabled:
   - Settings → Developer Options → USB Debugging → ON
3. Change USB mode on phone:
   - Pull down notification → tap USB → select File Transfer (MTP)
4. Add udev rule for your device:
   ```bash
   # For OnePlus/OPPO (vendor ID: 22d9)
   echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="22d9", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/51-android.rules
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```
5. Restart ADB:
   ```bash
   adb kill-server
   adb start-server
   adb devices
   ```

### ADB Device Shows "unauthorized"

**Symptom:** `adb devices` shows `<serial> unauthorized`.

**Solutions:**
1. Check phone screen for "Allow USB Debugging" prompt
2. Tap "Always allow from this computer" and tap Allow
3. If no prompt appears:
   - Settings → Developer Options → Revoke USB debugging authorizations
   - Re-enable USB Debugging
   - Reconnect USB cable

### scrcpy FFmpeg Decoder Error

**Symptom:** `ERROR: [FFmpeg] Unable to create decoder`

**Solution:** Fedora ships limited `ffmpeg-free` without H.264/H.265 codecs. Replace with full version:
```bash
sudo dnf swap ffmpeg-free ffmpeg --allowerasing
sudo dnf install ffmpeg-libs
```

### scrcpy Not Found in dnf

**Symptom:** `sudo dnf install scrcpy` returns no matches.

**Solution:** scrcpy is not in default Fedora repos. Install via COPR:
```bash
sudo dnf copr enable zeno/scrcpy
sudo dnf install scrcpy
```

### Groq API Rate Limit

**Symptom:** `429 RESOURCE_EXHAUSTED` error.

**Solutions:**
1. Wait a few minutes and retry (free tier has per-minute limits)
2. DroidPulse automatically falls back to rule-based analysis
3. Check usage at https://console.groq.com

### ADB over WiFi Connection Drops

**Symptom:** WiFi ADB connection lost after some time.

**Causes:**
- Phone went to sleep
- WiFi network changed
- Phone or ADB server restarted

**Solution:** Reconnect via USB, then re-enable WiFi mode:
```bash
adb tcpip 5555
adb connect <phone-ip>:5555
```

### Permission Denied on Scripts

**Symptom:** `Permission denied` when running bash scripts.

**Solution:**
```bash
chmod +x scripts/adb_commands.sh
chmod +x scripts/scan_all_devices.sh
```

---

## Scheduled Scans

### Using cron

```bash
# Edit crontab
crontab -e

# Run DroidPulse every hour
0 * * * * cd /home/student/Desktop/droidpulse && ./scripts/scan_all_devices.sh --report

# Run every 6 hours
0 */6 * * * cd /home/student/Desktop/droidpulse && ./scripts/scan_all_devices.sh --report

# Run daily at 9 AM
0 9 * * * cd /home/student/Desktop/droidpulse && ./scripts/scan_all_devices.sh --report
```

### Using systemd Timer (Alternative)

```bash
# Create service file
sudo nano /etc/systemd/system/droidpulse.service
```

```ini
[Unit]
Description=DroidPulse Device Health Scan

[Service]
Type=oneshot
User=student
WorkingDirectory=/home/student/Desktop/droidpulse
ExecStart=/home/student/Desktop/droidpulse/scripts/scan_all_devices.sh --report
```

```bash
# Create timer file
sudo nano /etc/systemd/system/droidpulse.timer
```

```ini
[Unit]
Description=Run DroidPulse every hour

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Enable and start
sudo systemctl enable droidpulse.timer
sudo systemctl start droidpulse.timer
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    DroidPulse                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  main.py (Entry Point)                              │
│    ├── collector.py (ADB Data Collection)           │
│    │     └── Runs ADB commands via subprocess       │
│    ├── wifi_manager.py (Network Diagnostics)        │
│    │     ├── WiFi health checks                     │
│    │     ├── Ping / DNS tests                       │
│    │     └── ADB over WiFi management               │
│    ├── analyzer.py (AI Analysis)                    │
│    │     ├── Groq API (Llama 3.3 70B)              │
│    │     └── Rule-based fallback                    │
│    ├── dashboard.py (Terminal Output)               │
│    │     └── Rich library for formatting            │
│    └── reporter.py (HTML Report)                    │
│          └── Jinja2 templating                      │
│                                                      │
│  scripts/                                            │
│    ├── adb_commands.sh (Bash ADB wrappers)          │
│    └── scan_all_devices.sh (Multi-device scanner)   │
│                                                      │
├─────────────────────────────────────────────────────┤
│  Android Device ←── ADB (USB / WiFi) ──→ Fedora    │
└─────────────────────────────────────────────────────┘
```

### Data Flow

1. `collector.py` runs ADB commands on the connected device
2. `wifi_manager.py` runs network diagnostics (ping, DNS, WiFi details)
3. Collected data is structured as JSON
4. `analyzer.py` sends JSON to Groq AI for health analysis
5. If AI unavailable, falls back to rule-based analysis
6. `dashboard.py` displays results in the terminal
7. `reporter.py` generates a professional HTML report
