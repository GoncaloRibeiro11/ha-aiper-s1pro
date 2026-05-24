# ha-aiper-s1pro

Unofficial Home Assistant integration for the **Aiper Scuba S1 Pro** robotic pool cleaner.

> ⚠️ **Work in progress** — The Aiper cloud API endpoints are reverse-engineered from app traffic. If something doesn't work, please open an issue with your logs.

---

## Features

| Entity | Type | Description |
|---|---|---|
| `vacuum.aiper_scuba_s1_pro` | Vacuum | Start/stop/pause, return to dock, locate, cleaning mode |
| `sensor.battery` | Sensor | Battery level (%) |
| `sensor.last_clean_area` | Sensor | Area cleaned in last session (m²) |
| `sensor.last_clean_duration` | Sensor | Duration of last session (min) |
| `sensor.error_code` | Sensor | Current error code (if any) |

### Cleaning modes (via Fan Speed)

| Mode | Description |
|---|---|
| `auto` | Full clean: floor + walls + waterline |
| `floor` | Floor only |
| `wall` | Walls only |
| `waterline` | Waterline only |
| `floor_wall` | Floor + walls |

---

## Installation

### Via HACS (recommended)

1. In HACS → **⋮ → Custom repositories**
2. URL: `https://github.com/YOUR_USERNAME/ha-aiper-s1pro`  
   Type: **Integration**
3. Click **Add** → search "Aiper S1 Pro" → Install
4. Restart Home Assistant

### Manual

```bash
cp -r custom_components/aiper_s1pro \
  /config/custom_components/aiper_s1pro
```

Restart Home Assistant.

---

## Configuration

1. **Settings → Devices & Services → Add Integration**
2. Search for **Aiper Scuba S1 Pro**
3. Enter your Aiper app **email** and **password**
4. Select your device (if multiple)

---

## Discovering the API (help wanted)

The API endpoints in `api.py` are based on traffic captured from the Aiper Android app (`com.aiper.develop`). If commands aren't working on your device, you can help by capturing your own app traffic:

### How to capture Aiper app traffic with mitmproxy

```bash
# Install mitmproxy on your PC
pip install mitmproxy

# Start the proxy
mitmproxy --listen-port 8080

# On your Android phone:
# Settings → WiFi → your network → Proxy → Manual
# Host: <your PC IP>   Port: 8080
# Install mitmproxy CA cert (visit mitm.it on the phone)
```

Then open the Aiper app and start/stop a cleaning cycle. Copy the captured requests into a GitHub issue.

---

## Known issues / limitations

- The **Hydrocomm** buoy (sold separately) is required for real-time status during cleaning. Without it, status updates only happen when the robot surfaces.
- Error code descriptions are not yet mapped to human-readable messages.

---

## Contributing

Pull requests welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT — see [LICENSE](LICENSE)
