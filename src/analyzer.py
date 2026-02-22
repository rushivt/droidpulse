"""
DroidPulse - AI-Powered Device Health Analyzer
Sends collected device data to Google Gemini for intelligent health analysis.
"""

import os
import json
from groq import Groq


def configure_groq():
    """Configure Groq API client with the API key."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Try loading from .env file
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        break

    if not api_key:
        print("[ERROR] GROQ_API_KEY not found. Set it in .env or environment.")
        return None

    return Groq(api_key=api_key)


def build_prompt(device_data):
    """Build the analysis prompt from collected device data."""
    # Remove verbose logs to keep prompt focused
    data = device_data.copy()
    if "error_logs" in data:
        data["error_logs"] = {
            "total_errors": data["error_logs"]["total_errors"],
            "recent_errors": data["error_logs"]["recent_errors"][:10]
        }

    prompt = f"""You are DroidPulse, an expert Android device health analyst.
Analyze the following device health data and provide a comprehensive report.

DEVICE DATA:
{json.dumps(data, indent=2)}

Respond ONLY in the following JSON format, no markdown, no backticks:
{{
    "health_score": <1-10 integer, 10 being perfect health>,
    "summary": "<2-3 sentence overall health summary>",
    "critical_issues": [
        {{
            "category": "<battery|storage|memory|cpu|network|security>",
            "severity": "<critical|warning|info>",
            "description": "<what the issue is>",
            "recommendation": "<what to do about it>"
        }}
    ],
    "battery_analysis": {{
        "status": "<good|degraded|critical>",
        "detail": "<battery health assessment>"
    }},
    "storage_analysis": {{
        "status": "<good|warning|critical>",
        "detail": "<storage usage assessment>"
    }},
    "memory_analysis": {{
        "status": "<good|warning|critical>",
        "detail": "<memory usage assessment with top consumers>"
    }},
    "network_analysis": {{
        "status": "<good|warning|critical>",
        "detail": "<network and WiFi assessment>"
    }},
    "security_findings": [
        "<any security concerns from installed apps or error logs>"
    ],
    "recommendations": [
        "<actionable recommendation 1>",
        "<actionable recommendation 2>",
        "<actionable recommendation 3>"
    ]
}}"""

    return prompt


def analyze(device_data):
    """Send device data to Gemini and get AI analysis."""
    print("[DroidPulse] Running AI health analysis...")

    client = configure_groq()
    if not client:
        print("[DroidPulse] AI unavailable, falling back to basic analysis.")
        return basic_analysis(device_data)

    prompt = build_prompt(device_data)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        text = response.choices[0].message.content.strip()

        # Clean up response if wrapped in markdown
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        analysis = json.loads(text)
        print("[DroidPulse] AI analysis complete.")
        return analysis

    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse AI response: {e}")
        print(f"[DEBUG] Raw response: {text[:500]}")
        return basic_analysis(device_data)
    except Exception as e:
        print(f"[ERROR] Groq API error: {e}")
        return basic_analysis(device_data)


def basic_analysis(device_data):
    """Fallback rule-based analysis when AI is unavailable."""
    print("[DroidPulse] Running basic rule-based analysis...")

    issues = []
    score = 10

    # Battery checks
    bat = device_data.get("battery", {})
    level = bat.get("level", 100)
    health = bat.get("health_text", "Unknown")

    if level < 20:
        issues.append({
            "category": "battery",
            "severity": "warning",
            "description": f"Battery level is low at {level}%",
            "recommendation": "Charge the device soon"
        })
        score -= 1

    if health != "Good":
        issues.append({
            "category": "battery",
            "severity": "critical",
            "description": f"Battery health is {health}",
            "recommendation": "Consider battery replacement"
        })
        score -= 2

    # Storage checks
    for part in device_data.get("storage", []):
        pct = part.get("use_percent", "0%").replace("%", "")
        if pct.isdigit() and int(pct) > 90:
            issues.append({
                "category": "storage",
                "severity": "critical",
                "description": f"{part['mounted_on']} is {pct}% full",
                "recommendation": "Free up space or move data to external storage"
            })
            score -= 2
        elif pct.isdigit() and int(pct) > 75:
            issues.append({
                "category": "storage",
                "severity": "warning",
                "description": f"{part['mounted_on']} is {pct}% full",
                "recommendation": "Monitor storage usage and clean unnecessary files"
            })
            score -= 1

    # Memory checks
    mem = device_data.get("memory", {})
    used_pct = mem.get("used_percent", 0)

    if used_pct > 90:
        issues.append({
            "category": "memory",
            "severity": "critical",
            "description": f"Memory usage is very high at {used_pct}%",
            "recommendation": "Close background apps to free memory"
        })
        score -= 2
    elif used_pct > 75:
        issues.append({
            "category": "memory",
            "severity": "warning",
            "description": f"Memory usage is elevated at {used_pct}%",
            "recommendation": "Monitor memory-heavy apps"
        })
        score -= 1

    # Network checks
    net = device_data.get("network", {})
    rssi = net.get("rssi", 0)
    signal = net.get("signal_quality", "Unknown")

    if signal == "Poor":
        issues.append({
            "category": "network",
            "severity": "warning",
            "description": f"WiFi signal is poor (RSSI: {rssi}dBm)",
            "recommendation": "Move closer to the router or check for interference"
        })
        score -= 1

    # Ensure score stays in range
    score = max(1, min(10, score))

    bat_status = "good" if health == "Good" and level > 20 else "warning"
    stor_status = "good"
    for part in device_data.get("storage", []):
        pct = part.get("use_percent", "0%").replace("%", "")
        if pct.isdigit() and int(pct) > 90:
            stor_status = "critical"
        elif pct.isdigit() and int(pct) > 75:
            stor_status = "warning"

    mem_status = "critical" if used_pct > 90 else "warning" if used_pct > 75 else "good"
    net_status = "good" if signal in ("Excellent", "Good") else "warning"

    return {
        "health_score": score,
        "summary": f"Device health score is {score}/10. Found {len(issues)} issue(s) requiring attention.",
        "critical_issues": issues,
        "battery_analysis": {
            "status": bat_status,
            "detail": f"Battery at {level}%, health: {health}, temp: {bat.get('temperature_celsius', 'N/A')}°C"
        },
        "storage_analysis": {
            "status": stor_status,
            "detail": f"User storage (/data) usage needs monitoring"
        },
        "memory_analysis": {
            "status": mem_status,
            "detail": f"RAM usage at {used_pct}% ({mem.get('used_mb', 'N/A')}MB / {mem.get('total_mb', 'N/A')}MB)"
        },
        "network_analysis": {
            "status": net_status,
            "detail": f"Connected to {net.get('ssid', 'Unknown')} on {net.get('band', 'Unknown')} band, signal: {signal}"
        },
        "security_findings": ["Basic analysis - no deep security scan performed"],
        "recommendations": [r["recommendation"] for r in issues] if issues else ["No immediate action required"]
    }


# Run standalone for testing
if __name__ == "__main__":
    from collector import collect_all, get_connected_devices

    devices = get_connected_devices()
    if not devices:
        print("[ERROR] No devices found.")
    else:
        data = collect_all(devices[0])
        analysis = analyze(data)
        print(json.dumps(analysis, indent=2))
