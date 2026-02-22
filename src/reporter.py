"""
DroidPulse - HTML Report Generator
Generates professional HTML health reports from device data and AI analysis.
"""

import os
from datetime import datetime
from jinja2 import Template


REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DroidPulse Report — {{ device.brand }} {{ device.device }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
            line-height: 1.6;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .header {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #1e293b, #334155);
            border-radius: 12px;
            margin-bottom: 1.5rem;
            border: 1px solid #475569;
        }
        .header h1 { font-size: 2rem; color: #38bdf8; margin-bottom: 0.5rem; }
        .header .subtitle { color: #94a3b8; font-size: 0.95rem; }
        .device-badge {
            display: inline-block;
            background: #1e293b;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            color: #38bdf8;
            border: 1px solid #38bdf8;
            margin-top: 0.8rem;
        }
        .card {
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid #334155;
        }
        .card h2 {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #334155;
        }
        .score-section { text-align: center; padding: 2rem; }
        .score-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .score-good { background: linear-gradient(135deg, #065f46, #059669); color: #6ee7b7; border: 3px solid #34d399; }
        .score-warning { background: linear-gradient(135deg, #713f12, #a16207); color: #fde047; border: 3px solid #facc15; }
        .score-critical { background: linear-gradient(135deg, #7f1d1d, #b91c1c); color: #fca5a5; border: 3px solid #f87171; }
        .summary { color: #94a3b8; margin-top: 0.8rem; max-width: 600px; margin-left: auto; margin-right: auto; }
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.6rem;
        }
        .info-item { display: flex; justify-content: space-between; padding: 0.4rem 0; }
        .info-label { color: #64748b; }
        .info-value { color: #e2e8f0; font-weight: 500; }
        .progress-container {
            background: #0f172a;
            border-radius: 8px;
            height: 24px;
            overflow: hidden;
            margin: 0.4rem 0;
            position: relative;
        }
        .progress-bar {
            height: 100%;
            border-radius: 8px;
            display: flex;
            align-items: center;
            padding-left: 8px;
            font-size: 0.75rem;
            font-weight: bold;
            color: white;
            transition: width 0.5s ease;
        }
        .bar-green { background: linear-gradient(90deg, #059669, #34d399); }
        .bar-yellow { background: linear-gradient(90deg, #a16207, #facc15); }
        .bar-red { background: linear-gradient(90deg, #b91c1c, #f87171); }
        .status-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .badge-good { background: #065f46; color: #6ee7b7; }
        .badge-warning { background: #713f12; color: #fde047; }
        .badge-critical { background: #7f1d1d; color: #fca5a5; }
        .badge-info { background: #1e3a5f; color: #7dd3fc; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.8rem;
        }
        th {
            text-align: left;
            padding: 0.6rem;
            background: #0f172a;
            color: #38bdf8;
            font-size: 0.85rem;
            border-bottom: 2px solid #334155;
        }
        td {
            padding: 0.6rem;
            border-bottom: 1px solid #1e293b;
            font-size: 0.9rem;
        }
        .issue-row { border-left: 3px solid; padding-left: 0.8rem; margin-bottom: 0.8rem; }
        .issue-critical { border-color: #f87171; background: #1a0505; padding: 0.8rem; border-radius: 0 8px 8px 0; }
        .issue-warning { border-color: #facc15; background: #1a1505; padding: 0.8rem; border-radius: 0 8px 8px 0; }
        .issue-info { border-color: #38bdf8; background: #051a2a; padding: 0.8rem; border-radius: 0 8px 8px 0; }
        .issue-title { font-weight: 600; margin-bottom: 0.3rem; }
        .issue-rec { color: #94a3b8; font-size: 0.9rem; }
        .rec-list { list-style: none; }
        .rec-list li {
            padding: 0.6rem 0.8rem;
            margin-bottom: 0.5rem;
            background: #0f172a;
            border-radius: 8px;
            border-left: 3px solid #38bdf8;
        }
        .rec-number { color: #38bdf8; font-weight: bold; margin-right: 0.5rem; }
        .footer {
            text-align: center;
            padding: 1.5rem;
            color: #475569;
            font-size: 0.85rem;
            border-top: 1px solid #334155;
            margin-top: 1rem;
        }
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
        @media (max-width: 700px) {
            .two-col, .info-grid { grid-template-columns: 1fr; }
            body { padding: 1rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DroidPulse</h1>
            <div class="subtitle">AI-Powered Android Device Health Report</div>
            <div class="device-badge">{{ device.brand }} {{ device.device }} ({{ device.model }}) — Android {{ device.android_version }}</div>
        </div>

        <!-- Health Score -->
        <div class="card score-section">
            {% set score = analysis.health_score %}
            {% if score >= 8 %}
                {% set score_class = "score-good" %}
            {% elif score >= 5 %}
                {% set score_class = "score-warning" %}
            {% else %}
                {% set score_class = "score-critical" %}
            {% endif %}
            <div class="score-circle {{ score_class }}">{{ score }}/10</div>
            <h2 style="border: none; text-align: center;">Device Health Score</h2>
            <div class="summary">{{ analysis.summary }}</div>
        </div>

        <div class="two-col">
            <!-- Battery -->
            <div class="card">
                <h2>🔋 Battery</h2>
                {% set bat_status = analysis.battery_analysis.status %}
                <span class="status-badge badge-{{ bat_status }}">{{ bat_status | upper }}</span>
                <div style="margin-top: 1rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Level</span><span>{{ battery.level }}%</span>
                    </div>
                    <div class="progress-container">
                        {% if battery.level > 50 %}{% set bcolor = "bar-green" %}
                        {% elif battery.level > 20 %}{% set bcolor = "bar-yellow" %}
                        {% else %}{% set bcolor = "bar-red" %}{% endif %}
                        <div class="progress-bar {{ bcolor }}" style="width: {{ battery.level }}%">{{ battery.level }}%</div>
                    </div>
                </div>
                <div class="info-grid" style="margin-top: 0.8rem;">
                    <div class="info-item"><span class="info-label">Health</span><span class="info-value">{{ battery.health_text }}</span></div>
                    <div class="info-item"><span class="info-label">Status</span><span class="info-value">{{ battery.status_text }}</span></div>
                    <div class="info-item"><span class="info-label">Temperature</span><span class="info-value">{{ battery.temperature_celsius }}°C</span></div>
                    <div class="info-item"><span class="info-label">Technology</span><span class="info-value">{{ battery.technology }}</span></div>
                </div>
                <div style="margin-top: 0.5rem; color: #94a3b8; font-size: 0.9rem;">{{ analysis.battery_analysis.detail }}</div>
            </div>

            <!-- Network -->
            <div class="card">
                <h2>🌐 Network</h2>
                {% set net_status = analysis.network_analysis.status %}
                <span class="status-badge badge-{{ net_status }}">{{ net_status | upper }}</span>
                <div class="info-grid" style="margin-top: 1rem;">
                    <div class="info-item"><span class="info-label">SSID</span><span class="info-value">{{ network.ssid }}</span></div>
                    <div class="info-item"><span class="info-label">Signal</span><span class="info-value">{{ network.signal_quality }} ({{ network.rssi }} dBm)</span></div>
                    <div class="info-item"><span class="info-label">Band</span><span class="info-value">{{ network.band }}</span></div>
                    <div class="info-item"><span class="info-label">Speed</span><span class="info-value">{{ network.link_speed_mbps }} Mbps</span></div>
                    <div class="info-item"><span class="info-label">Frequency</span><span class="info-value">{{ network.frequency_mhz }} MHz</span></div>
                    <div class="info-item"><span class="info-label">IP</span><span class="info-value">{{ network.ip_address }}/{{ network.subnet_mask }}</span></div>
                </div>
                <div style="margin-top: 0.5rem; color: #94a3b8; font-size: 0.9rem;">{{ analysis.network_analysis.detail }}</div>
            </div>
        </div>

        <!-- Storage -->
        <div class="card">
            <h2>💾 Storage</h2>
            {% set stor_status = analysis.storage_analysis.status %}
            <span class="status-badge badge-{{ stor_status }}">{{ stor_status | upper }}</span>
            <table>
                <thead><tr><th>Partition</th><th>Size</th><th>Used</th><th>Available</th><th>Usage</th></tr></thead>
                <tbody>
                {% for part in storage %}
                    <tr>
                        <td>{{ part.mounted_on }}</td>
                        <td>{{ part.size }}</td>
                        <td>{{ part.used }}</td>
                        <td>{{ part.available }}</td>
                        <td>
                            <div class="progress-container" style="height: 18px; min-width: 100px;">
                                {% set pct = part.use_percent | replace('%', '') | int %}
                                {% if pct > 90 %}{% set scolor = "bar-red" %}
                                {% elif pct > 75 %}{% set scolor = "bar-yellow" %}
                                {% else %}{% set scolor = "bar-green" %}{% endif %}
                                <div class="progress-bar {{ scolor }}" style="width: {{ pct }}%">{{ part.use_percent }}</div>
                            </div>
                        </td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
            <div style="margin-top: 0.5rem; color: #94a3b8; font-size: 0.9rem;">{{ analysis.storage_analysis.detail }}</div>
        </div>

        <div class="two-col">
            <!-- Memory -->
            <div class="card">
                <h2>🧠 Memory</h2>
                {% set mem_status = analysis.memory_analysis.status %}
                <span class="status-badge badge-{{ mem_status }}">{{ mem_status | upper }}</span>
                <div style="margin-top: 1rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>RAM Usage</span><span>{{ memory.used_percent }}%</span>
                    </div>
                    <div class="progress-container">
                        {% if memory.used_percent > 90 %}{% set mcolor = "bar-red" %}
                        {% elif memory.used_percent > 75 %}{% set mcolor = "bar-yellow" %}
                        {% else %}{% set mcolor = "bar-green" %}{% endif %}
                        <div class="progress-bar {{ mcolor }}" style="width: {{ memory.used_percent }}%">{{ memory.used_percent }}%</div>
                    </div>
                    <div class="info-grid" style="margin-top: 0.5rem;">
                        <div class="info-item"><span class="info-label">Total</span><span class="info-value">{{ memory.total_mb }} MB</span></div>
                        <div class="info-item"><span class="info-label">Available</span><span class="info-value">{{ memory.available_mb }} MB</span></div>
                    </div>
                </div>
                <div style="margin-top: 0.8rem;">
                    <strong style="font-size: 0.85rem; color: #64748b;">Top Consumers</strong>
                    {% for c in memory.top_consumers[:5] %}
                    <div class="info-item">
                        <span class="info-label">{{ c.process }}</span>
                        <span class="info-value">{{ (c.memory_kb / 1024) | round(1) }} MB</span>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- CPU -->
            <div class="card">
                <h2>⚡ CPU</h2>
                <div class="info-grid" style="margin-top: 0.5rem;">
                    <div class="info-item"><span class="info-label">Load 1m</span><span class="info-value">{{ cpu.load_1min }}</span></div>
                    <div class="info-item"><span class="info-label">Load 5m</span><span class="info-value">{{ cpu.load_5min }}</span></div>
                    <div class="info-item"><span class="info-label">Load 15m</span><span class="info-value">{{ cpu.load_15min }}</span></div>
                </div>
                <div style="margin-top: 0.8rem;">
                    <strong style="font-size: 0.85rem; color: #64748b;">Top Consumers</strong>
                    {% for c in cpu.top_consumers[:5] %}
                    <div class="info-item">
                        <span class="info-label">{{ c.process }}</span>
                        <span class="info-value">{{ c.cpu_percent }}%</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Apps -->
        <div class="card">
            <h2>📱 Apps</h2>
            <div class="info-grid">
                <div class="info-item"><span class="info-label">Total Packages</span><span class="info-value">{{ apps.total_packages }}</span></div>
                <div class="info-item"><span class="info-label">System Apps</span><span class="info-value">{{ apps.system_count }}</span></div>
                <div class="info-item"><span class="info-label">Third-Party Apps</span><span class="info-value">{{ apps.third_party_count }}</span></div>
            </div>
        </div>

        <!-- Issues -->
        {% if analysis.critical_issues %}
        <div class="card">
            <h2>⚠️ Issues</h2>
            {% for issue in analysis.critical_issues %}
            <div class="issue-row issue-{{ issue.severity }}" style="margin-top: 0.5rem;">
                <div class="issue-title">
                    <span class="status-badge badge-{{ issue.severity }}">{{ issue.severity | upper }}</span>
                    {{ issue.category | upper }} — {{ issue.description }}
                </div>
                <div class="issue-rec">💡 {{ issue.recommendation }}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Recommendations -->
        {% if analysis.recommendations %}
        <div class="card">
            <h2>🤖 AI Recommendations</h2>
            <ul class="rec-list">
                {% for rec in analysis.recommendations %}
                <li><span class="rec-number">{{ loop.index }}.</span> {{ rec }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <!-- Security -->
        {% if analysis.security_findings %}
        <div class="card">
            <h2>🔒 Security Findings</h2>
            {% for finding in analysis.security_findings %}
            <div style="padding: 0.4rem 0; color: #94a3b8;">• {{ finding }}</div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="footer">
            Generated by <strong>DroidPulse</strong> — AI-Powered Android Device Health Dashboard<br>
            Report generated on {{ device.timestamp }} | Serial: {{ device.serial }}
        </div>
    </div>
</body>
</html>"""


def generate_report(device_data, analysis):
    """Generate HTML report and save to reports/ directory."""
    print("[DroidPulse] Generating HTML report...")

    template = Template(REPORT_TEMPLATE)
    html = template.render(
        device=device_data.get("device_info", {}),
        battery=device_data.get("battery", {}),
        storage=device_data.get("storage", []),
        memory=device_data.get("memory", {}),
        cpu=device_data.get("cpu", {}),
        network=device_data.get("network", {}),
        apps=device_data.get("apps", {}),
        analysis=analysis
    )

    # Save report
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    device_name = device_data.get("device_info", {}).get("device", "unknown")
    filename = f"droidpulse_{device_name}_{timestamp}.html"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, "w") as f:
        f.write(html)

    print(f"[DroidPulse] Report saved: {filepath}")
    return filepath


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
        path = generate_report(data, analysis)
        print(f"\nOpen in browser: file://{os.path.abspath(path)}")
