"""
DroidPulse - Terminal Dashboard
Displays device health data in a color-coded terminal dashboard.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box


console = Console()


def get_score_color(score):
    """Return color based on health score."""
    if score >= 8:
        return "green"
    elif score >= 5:
        return "yellow"
    else:
        return "red"


def get_status_color(status):
    """Return color based on status string."""
    status = status.lower()
    if status in ("good", "excellent"):
        return "green"
    elif status in ("warning", "fair"):
        return "yellow"
    else:
        return "red"


def get_severity_color(severity):
    """Return color based on severity level."""
    if severity == "critical":
        return "red"
    elif severity == "warning":
        return "yellow"
    else:
        return "cyan"


def display_header(device_info):
    """Display device identity header."""
    header = Text()
    header.append("DroidPulse", style="bold cyan")
    header.append(" — Device Health Dashboard\n\n", style="dim")
    header.append(f"  Device:    ", style="dim")
    header.append(f"{device_info.get('brand', 'N/A')} {device_info.get('device', 'N/A')} ({device_info.get('model', 'N/A')})\n", style="bold white")
    header.append(f"  Android:   ", style="dim")
    header.append(f"{device_info.get('android_version', 'N/A')} (SDK {device_info.get('sdk_level', 'N/A')})\n", style="white")
    header.append(f"  Build:     ", style="dim")
    header.append(f"{device_info.get('build_number', 'N/A')}\n", style="white")
    header.append(f"  Serial:    ", style="dim")
    header.append(f"{device_info.get('serial', 'N/A')}\n", style="white")
    header.append(f"  Hardware:  ", style="dim")
    header.append(f"{device_info.get('hardware', 'N/A')}\n", style="white")
    header.append(f"  Scanned:   ", style="dim")
    header.append(f"{device_info.get('timestamp', 'N/A')}", style="white")

    console.print(Panel(header, title="[bold cyan]Device Info[/]", border_style="cyan", box=box.ROUNDED))


def display_health_score(analysis):
    """Display AI health score prominently."""
    score = analysis.get("health_score", 0)
    color = get_score_color(score)

    score_bar = "█" * score + "░" * (10 - score)
    score_text = Text()
    score_text.append(f"\n  Health Score: ", style="dim")
    score_text.append(f"{score}/10", style=f"bold {color}")
    score_text.append(f"  [{score_bar}]\n\n", style=color)
    score_text.append(f"  {analysis.get('summary', 'No summary available.')}\n", style="white")

    console.print(Panel(score_text, title=f"[bold {color}]AI Health Analysis[/]", border_style=color, box=box.ROUNDED))


def display_battery(battery):
    """Display battery health section."""
    level = battery.get("level", 0)
    bar_filled = int(level / 5)
    bar_empty = 20 - bar_filled

    if level > 50:
        bar_color = "green"
    elif level > 20:
        bar_color = "yellow"
    else:
        bar_color = "red"

    text = Text()
    text.append(f"\n  Level:        ", style="dim")
    text.append(f"{level}%", style=f"bold {bar_color}")
    text.append(f"  [{'█' * bar_filled}{'░' * bar_empty}]\n", style=bar_color)
    text.append(f"  Health:       ", style="dim")
    text.append(f"{battery.get('health_text', 'N/A')}\n", style=f"bold {get_status_color(battery.get('health_text', ''))}")
    text.append(f"  Status:       ", style="dim")
    text.append(f"{battery.get('status_text', 'N/A')}\n", style="white")
    text.append(f"  Temperature:  ", style="dim")
    temp = battery.get("temperature_celsius", 0)
    temp_color = "green" if temp < 35 else "yellow" if temp < 45 else "red"
    text.append(f"{temp}°C\n", style=temp_color)
    text.append(f"  Voltage:      ", style="dim")
    text.append(f"{battery.get('voltage', 'N/A')}mV\n", style="white")
    text.append(f"  Technology:   ", style="dim")
    text.append(f"{battery.get('technology', 'N/A')}\n", style="white")
    text.append(f"  Power:        ", style="dim")
    power = "USB" if battery.get("usb_powered") else "AC" if battery.get("ac_powered") else "Battery"
    text.append(f"{power}\n", style="white")

    console.print(Panel(text, title="[bold green]Battery[/]", border_style="green", box=box.ROUNDED))


def display_storage(storage):
    """Display storage usage section."""
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("Partition", style="white")
    table.add_column("Size", justify="right")
    table.add_column("Used", justify="right")
    table.add_column("Available", justify="right")
    table.add_column("Usage", justify="right")
    table.add_column("Bar", min_width=12)

    for part in storage:
        pct_str = part.get("use_percent", "0%").replace("%", "")
        pct = int(pct_str) if pct_str.isdigit() else 0
        bar_len = int(pct / 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        color = "green" if pct < 75 else "yellow" if pct < 90 else "red"

        table.add_row(
            part.get("mounted_on", "N/A"),
            part.get("size", "N/A"),
            part.get("used", "N/A"),
            part.get("available", "N/A"),
            f"[{color}]{part.get('use_percent', 'N/A')}[/]",
            f"[{color}]{bar}[/]"
        )

    console.print(Panel(table, title="[bold blue]Storage[/]", border_style="blue", box=box.ROUNDED))


def display_memory(memory):
    """Display memory usage section."""
    used_pct = memory.get("used_percent", 0)
    bar_len = int(used_pct / 5)
    bar = "█" * bar_len + "░" * (20 - bar_len)
    color = "green" if used_pct < 75 else "yellow" if used_pct < 90 else "red"

    text = Text()
    text.append(f"\n  RAM Usage:  ", style="dim")
    text.append(f"{used_pct}%", style=f"bold {color}")
    text.append(f"  [{bar}]\n", style=color)
    text.append(f"  Total:      ", style="dim")
    text.append(f"{memory.get('total_mb', 'N/A')} MB\n", style="white")
    text.append(f"  Used:       ", style="dim")
    text.append(f"{memory.get('used_mb', 'N/A')} MB\n", style="white")
    text.append(f"  Available:  ", style="dim")
    text.append(f"{memory.get('available_mb', 'N/A')} MB\n", style="white")

    # Top consumers table
    consumers = memory.get("top_consumers", [])[:5]
    if consumers:
        text.append(f"\n  Top Memory Consumers:\n", style="bold dim")
        for c in consumers:
            mem_mb = round(c["memory_kb"] / 1024, 1)
            text.append(f"    {mem_mb:>7.1f} MB  ", style="yellow")
            text.append(f"{c['process']}\n", style="white")

    console.print(Panel(text, title="[bold magenta]Memory[/]", border_style="magenta", box=box.ROUNDED))


def display_cpu(cpu):
    """Display CPU usage section."""
    text = Text()
    text.append(f"\n  Load Average:  ", style="dim")
    text.append(f"{cpu.get('load_1min', 'N/A')}", style="bold white")
    text.append(f" / {cpu.get('load_5min', 'N/A')} / {cpu.get('load_15min', 'N/A')}", style="white")
    text.append(f"  (1m / 5m / 15m)\n", style="dim")

    consumers = cpu.get("top_consumers", [])[:5]
    if consumers:
        text.append(f"\n  Top CPU Consumers:\n", style="bold dim")
        for c in consumers:
            pct = c["cpu_percent"]
            color = "red" if pct > 20 else "yellow" if pct > 10 else "white"
            text.append(f"    {pct:>5.1f}%  ", style=color)
            text.append(f"{c['process']}\n", style="white")

    console.print(Panel(text, title="[bold yellow]CPU[/]", border_style="yellow", box=box.ROUNDED))


def display_network(network):
    """Display network status section."""
    signal = network.get("signal_quality", "Unknown")
    signal_color = get_status_color(signal)

    text = Text()
    text.append(f"\n  SSID:          ", style="dim")
    text.append(f"{network.get('ssid', 'N/A')}\n", style="bold white")
    text.append(f"  Signal:        ", style="dim")
    text.append(f"{signal} ({network.get('rssi', 'N/A')} dBm)\n", style=f"bold {signal_color}")
    text.append(f"  Band:          ", style="dim")
    text.append(f"{network.get('band', 'N/A')}\n", style="white")
    text.append(f"  Link Speed:    ", style="dim")
    text.append(f"{network.get('link_speed_mbps', 'N/A')} Mbps\n", style="white")
    text.append(f"  Frequency:     ", style="dim")
    text.append(f"{network.get('frequency_mhz', 'N/A')} MHz\n", style="white")
    text.append(f"  IP Address:    ", style="dim")
    text.append(f"{network.get('ip_address', 'N/A')}/{network.get('subnet_mask', 'N/A')}\n", style="white")
    text.append(f"  IPv6:          ", style="dim")
    text.append(f"{network.get('ipv6_address', 'N/A')}\n", style="white")
    text.append(f"  Connection:    ", style="dim")
    text.append(f"{network.get('connection_type', 'N/A')}\n", style="white")
    dns = network.get("dns", [])
    text.append(f"  DNS:           ", style="dim")
    text.append(f"{', '.join(dns) if dns else 'Not configured'}\n", style="white")

    console.print(Panel(text, title="[bold cyan]Network[/]", border_style="cyan", box=box.ROUNDED))


def display_apps(apps):
    """Display installed apps summary."""
    text = Text()
    text.append(f"\n  Total Packages:    ", style="dim")
    text.append(f"{apps.get('total_packages', 0)}\n", style="bold white")
    text.append(f"  System Apps:       ", style="dim")
    text.append(f"{apps.get('system_count', 0)}\n", style="white")
    text.append(f"  Third-Party Apps:  ", style="dim")
    text.append(f"{apps.get('third_party_count', 0)}\n", style="yellow")

    console.print(Panel(text, title="[bold white]Apps[/]", border_style="white", box=box.ROUNDED))


def display_issues(analysis):
    """Display critical issues from AI analysis."""
    issues = analysis.get("critical_issues", [])
    if not issues:
        console.print(Panel("[green]  No critical issues found![/]", title="[bold green]Issues[/]", border_style="green", box=box.ROUNDED))
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold red")
    table.add_column("Severity", width=10)
    table.add_column("Category", width=12)
    table.add_column("Issue")
    table.add_column("Recommendation")

    for issue in issues:
        sev = issue.get("severity", "info")
        color = get_severity_color(sev)
        table.add_row(
            f"[{color}]{sev.upper()}[/]",
            issue.get("category", "N/A"),
            issue.get("description", "N/A"),
            issue.get("recommendation", "N/A")
        )

    console.print(Panel(table, title="[bold red]Issues & Recommendations[/]", border_style="red", box=box.ROUNDED))


def display_recommendations(analysis):
    """Display AI recommendations."""
    recs = analysis.get("recommendations", [])
    if not recs:
        return

    text = Text()
    for i, rec in enumerate(recs, 1):
        text.append(f"\n  {i}. ", style="bold cyan")
        text.append(f"{rec}", style="white")
    text.append("\n")

    console.print(Panel(text, title="[bold cyan]AI Recommendations[/]", border_style="cyan", box=box.ROUNDED))


def display(device_data, analysis):
    """Display the full terminal dashboard."""
    console.clear()
    console.print()

    display_header(device_data.get("device_info", {}))
    display_health_score(analysis)
    display_battery(device_data.get("battery", {}))
    display_storage(device_data.get("storage", []))
    display_memory(device_data.get("memory", {}))
    display_cpu(device_data.get("cpu", {}))
    display_network(device_data.get("network", {}))
    display_apps(device_data.get("apps", {}))
    display_issues(analysis)
    display_recommendations(analysis)

    console.print("\n[dim]  Report generated by DroidPulse | AI-Powered Device Health Dashboard[/]\n")


# Run standalone for testing
if __name__ == "__main__":
    from collector import collect_all, get_connected_devices
    from analyzer import analyze

    devices = get_connected_devices()
    if not devices:
        print("[ERROR] No devices found.")
    else:
        data = collect_all(devices[0])
        analysis = analyze(data)
        display(data, analysis)
