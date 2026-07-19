# Pawsync Home Assistant Integration

This custom integration allows you to connect your Pawsync pet feeder devices to Home Assistant. You can monitor device status, view sensor data, and trigger feeding actions directly from your smart home dashboard.

## Features

- **Sensor Entities:** Exposes device properties (e.g., food level) as Home Assistant sensors.
- **Feed Service:** Trigger manual feeding via Home Assistant services.

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Paste the URL of this repository (`https://github.com/asssaf/pawsync-hass`) into the **Repository** field.
4. Select **Integration** as the Category and click **Add**.
5. Click **Download** on the newly added integration card.
6. Restart Home Assistant.

### Method 2: Manual Installation

1. Create a directory named `pawsync` inside your Home Assistant `custom_components` folder.
2. Copy all the files from this repository (except for `tests`, `.github`, and `.venv` related files) into that `custom_components/pawsync/` folder.
3. Restart Home Assistant.

## Configuration

### UI Setup

1. Go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for "Pawsync".
3. Enter your Pawsync account credentials.

### YAML Setup (optional)

Add to your `configuration.yaml`:

```yaml
pawsync:
  username: your_email@example.com
  password: your_password
```

## Services

### Feed

Trigger a manual feeding for a device:

```yaml
service: pawsync.feed
data:
  entity_id: sensor.pawsync_device_id
  amount: 12
```

## Development

To set up the development environment, run the setup script:

```bash
./scripts/dev-setup.sh
```

This script uses `mise` to manage Python 3.14 and `uv`, creates a local virtual environment (`.venv`), and installs development dependencies from `requirements-dev.txt` using uv.

### Linting and Formatting

We use Ruff to maintain code quality. To run checks and format the codebase, activate the virtual environment first:

```bash
source .venv/bin/activate
ruff check .
ruff format .
```

Alternatively, you can run them directly without activating the virtual environment:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format .
```

### Running Tests

We use `pytest` to run tests. Activate the virtual environment first:

```bash
source .venv/bin/activate
pytest
```

Alternatively, you can run them directly without activating the virtual environment:

```bash
.venv/bin/pytest
```

## License

MIT

## Disclaimer

This integration is not affiliated with or endorsed by Pawsync.
