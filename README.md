# ha-aiper-s1pro

Unofficial Home Assistant integration for the Aiper Scuba S1 Pro robotic pool
cleaner.

Work in progress: the Aiper cloud API endpoints are reverse-engineered from app
traffic. If something does not work, please open an issue with your logs.

## Features

| Entity | Type | Description |
|---|---|---|
| `vacuum.aiper_scuba_s1_pro` | Vacuum | Start, stop, pause, return to dock, locate, cleaning mode |
| `sensor.battery` | Sensor | Battery level (%) |
| `sensor.last_clean_area` | Sensor | Area cleaned in last session |
| `sensor.last_clean_duration` | Sensor | Duration of last session (min) |
| `sensor.error_code` | Sensor | Current error code, if any |

## Cleaning Modes

Cleaning modes are exposed through the Home Assistant vacuum fan speed feature.

| Mode | Description |
|---|---|
| `auto` | Full clean: floor, walls, and waterline |
| `floor` | Floor only |
| `wall` | Walls only |
| `waterline` | Waterline only |
| `floor_wall` | Floor and walls |

## Installation

### HACS

1. In HACS, open custom repositories.
2. Add `https://github.com/GoncaloRibeiro11/ha-aiper-s1pro` as an integration.
3. Search for "Aiper S1 Pro" and install it.
4. Restart Home Assistant.

### Manual

Copy the integration folder into your Home Assistant config directory:

```bash
cp -r custom_components/aiper_s1pro /config/custom_components/aiper_s1pro
```

Restart Home Assistant.

## Configuration

1. Go to Settings > Devices & services > Add integration.
2. Search for "Aiper Scuba S1 Pro".
3. Enter your Aiper app email and password.
4. Select your device if the account has more than one.

## API Discovery

The API endpoints in `api.py` are based on traffic captured from the Aiper
Android app. If commands do not work on your device, capturing your own app
traffic can help improve the integration.

### Capture Aiper App Traffic With mitmproxy

```bash
pip install mitmproxy
mitmproxy --listen-port 8080
```

On your Android phone:

1. Open Wi-Fi settings for your network.
2. Set the proxy to manual.
3. Use your computer IP as the host and `8080` as the port.
4. Install the mitmproxy CA certificate from `mitm.it`.
5. Open the Aiper app and start or stop a cleaning cycle.

Copy relevant captured requests into a GitHub issue. Remove passwords, tokens,
email addresses, and any other private data before sharing logs.

## Known Limitations

- The Hydrocomm buoy may be required for real-time status during cleaning.
- Without real-time connectivity, status updates may only happen when the robot
  surfaces.
- Error code descriptions are not yet mapped to human-readable messages.
- The Aiper cloud API is not officially documented and may change.

## License

MIT. See [LICENSE](LICENSE).
