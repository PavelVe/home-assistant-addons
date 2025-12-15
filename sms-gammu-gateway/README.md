# SMS Gammu Gateway Add-on

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

REST API SMS Gateway using python-gammu for USB GSM modems (SIM800L, Huawei, etc.)

## About

This add-on provides a complete SMS gateway solution for Home Assistant, replacing the deprecated "SMS notifications via GSM-modem" integration. It offers both REST API and MQTT interfaces for sending and receiving SMS messages through USB GSM modems.

**Based on** [pajikos/sms-gammu-gateway](https://github.com/pajikos/sms-gammu-gateway) (Apache License 2.0).

## 🌟 Key Features

### 📱 SMS Management
- **Send SMS** via REST API, MQTT, or Home Assistant UI
- **Flash SMS Support** ⚡ - Send urgent alerts that display on screen without saving to inbox (Class 0)
- **Receive SMS** with automatic MQTT notifications
- **Text Input Fields** directly in Home Assistant device
- **Smart Buttons** for easy SMS sending from UI (normal + flash)
- **Phone Number Persistence** - keeps number for multiple messages
- **Automatic Unicode Detection** - Czech/special characters handled automatically
- **Delete All SMS Button** - Clear SIM card storage with one click
- **Auto-delete SMS** - Optional automatic deletion after reading
- **Reset Counter Button** - Reset SMS statistics
- **Message Length Limit** - 255 characters max (longer messages split automatically by modem)

### 📊 Device Monitoring
- **Signal Strength** sensor with percentage display
- **Network Info** showing operator name and status
- **Last SMS Received** sensor with full message details
- **SMS Send Status** tracking success/error states
- **SMS Counter** with persistent storage (survives restarts)
- **SMS Cost Tracking** (optional, configurable price per SMS)
- **Modem Info** sensors (IMEI, Model, Manufacturer)
- **SIM Card Info** (IMSI identification)
- **SMS Storage Capacity** monitoring (used/total on SIM)
- **Modem Status** tracking device connectivity
- **Real-time Updates** via MQTT with auto-discovery

### 🔧 Integration Options
- **REST API** with Swagger documentation at `/docs/`
- **MQTT Integration** with Home Assistant auto-discovery
- **Native HA Service** `send_sms` for automations
- **Notify Platform** support for alerts
- **Web UI** accessible through Ingress

## Prerequisites

- USB GSM modem supporting AT commands (SIM800L, Huawei E1750, etc.)
- Modem must appear as `/dev/ttyUSB*` device
- SIM card with SMS capability
- Optional: MQTT broker for full integration

## Installation

1. Add repository to your Home Assistant:
   ```
   https://github.com/pavelve/home-assistant-addons
   ```
2. Find **SMS Gammu Gateway** in add-on store
3. Click Install
4. Configure the add-on (see below)
5. Start the add-on

## Configuration

### Basic Settings

| Option | Default | Description |
|--------|---------|-------------|
| `device_path` | `/dev/ttyUSB0` | Path to your GSM modem device (see Device Path Options below) |
| `pin` | `""` | SIM card PIN (leave empty if no PIN) |
| `port` | `5000` | API port |
| `ssl` | `false` | Enable HTTPS |
| `username` | `admin` | API username |
| `password` | `password` | API password (change this!) |

#### Device Path Options

You can specify the modem path in two ways:

**Option 1: By device name (simple, but may change)**
```
/dev/ttyUSB0
```
⚠️ **Warning:** This path can change if you disconnect/reconnect the modem or add other USB devices.

**Option 2: By device ID (recommended, stable)**
```
/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
```
✅ **Recommended:** This path is unique and persistent across reboots and reconnections.

To find your modem's stable ID, run in Home Assistant terminal:
```bash
ls -la /dev/serial/by-id/
```

### MQTT Settings (Optional)

| Option | Default | Description |
|--------|---------|-------------|
| `mqtt_enabled` | `false` | Enable MQTT integration |
| `mqtt_host` | `core-mosquitto` | MQTT broker hostname |
| `mqtt_port` | `1883` | MQTT broker port |
| `mqtt_username` | `""` | MQTT username |
| `mqtt_password` | `""` | MQTT password |
| `mqtt_topic_prefix` | `homeassistant/sensor/sms_gateway` | Topic prefix |
| `sms_monitoring_enabled` | `true` | Auto-detect incoming SMS |
| `sms_check_interval` | `60` | SMS check interval (seconds) |

### Advanced Settings

| Option | Default | Description |
|--------|---------|-------------|
| `sms_cost_per_message` | `0.0` | Cost per SMS (set to 0 to disable cost tracking sensor) |
| `auto_delete_read_sms` | `true` | Automatically delete SMS after reading |

### Example Configuration

```yaml
# Recommended: Use stable device ID
device_path: "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
# Or simple path (may change on reconnect):
# device_path: "/dev/ttyUSB0"

pin: ""
port: 5000
ssl: false
username: "admin"
password: "your_secure_password"
mqtt_enabled: true
mqtt_host: "core-mosquitto"
mqtt_port: 1883
mqtt_username: ""
mqtt_password: ""
sms_monitoring_enabled: true
sms_check_interval: 60
```

## 🏠 Home Assistant Integration

### Method 1: MQTT with Auto-Discovery (Recommended)

Enable MQTT in configuration and the add-on will automatically create:
- 📊 **GSM Signal Strength** sensor
- 🌐 **GSM Network** sensor
- 💬 **Last SMS Received** sensor
- ✅ **SMS Send Status** sensor
- 📱 **Phone Number** text input
- 💬 **Message Text** text input
- 🔘 **Send SMS** button
- ⚡ **Send Flash SMS** button (urgent alerts - displays on screen without saving)

All entities appear under device **"SMS Gateway"** in Home Assistant.

![MQTT Device Overview](https://raw.githubusercontent.com/pavelve/home-assistant-addons/main/sms-gammu-gateway/images/mqtt-device.png)

### Method 2: RESTful Notify

Add to your `configuration.yaml`:

```yaml
notify:
  - name: SMS Gateway
    platform: rest
    resource: http://192.168.1.x:5000/sms
    method: POST_JSON
    authentication: basic
    username: admin
    password: your_password
    target_param_name: number
    message_param_name: message
```

![Actions Notify Example](https://raw.githubusercontent.com/pavelve/home-assistant-addons/main/sms-gammu-gateway/images/actions-notify.png)

### Method 3: Direct Service Calls

Use in automations:

```yaml
# Normal SMS
service: mqtt.publish
data:
  topic: "homeassistant/sensor/sms_gateway/send"
  payload: '{"number": "+420123456789", "text": "Alert!"}'

# Flash SMS (displays on screen, not saved to inbox)
service: mqtt.publish
data:
  topic: "homeassistant/sensor/sms_gateway/send"
  payload: '{"number": "+420123456789", "text": "URGENT ALERT!", "flash": true}'
```

## 📝 Usage Examples

### Send SMS via Button
1. Go to **SMS Gateway** device in Home Assistant
2. Fill **Phone Number** field (e.g., +420123456789)
3. Fill **Message Text** field (max 255 characters)
4. Click **Send SMS** button
5. Message field auto-clears, number stays for next message

**Note:** Messages are limited to 255 characters due to MQTT message size constraints. Longer messages will be automatically split into multiple SMS parts by the GSM modem.

### Automation Example

```yaml
automation:
  - alias: Door Alert SMS
    trigger:
      platform: state
      entity_id: binary_sensor.door
      to: 'on'
    action:
      service: notify.sms_gateway
      data:
        message: 'Door opened!'
        target: '+420123456789'
```

### REST API Examples

```bash
# Normal SMS
curl -X POST http://192.168.1.x:5000/sms \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{"text": "Test SMS", "number": "+420123456789"}'

# Flash SMS (urgent alert - displays on screen without saving)
curl -X POST http://192.168.1.x:5000/sms \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{"text": "URGENT!", "number": "+420123456789", "flash": true}'
```

**Flash SMS Notes:**
- Flash SMS displays immediately on phone screen
- Message is NOT saved to inbox
- Ideal for urgent alerts and notifications
- Not all phones/carriers support Flash SMS (fallback to normal SMS)
- Some carriers may charge differently for Flash SMS

## 🔧 API Documentation

### Swagger UI
Access full API documentation at: `http://your-ha-ip:5000/docs/`

![Swagger UI Documentation](https://raw.githubusercontent.com/pavelve/home-assistant-addons/main/sms-gammu-gateway/images/swagger-ui.png)

### Main Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/sms` | Send SMS | Yes |
| GET | `/sms` | Get all SMS | Yes |
| GET | `/sms/{id}` | Get specific SMS | Yes |
| DELETE | `/sms/{id}` | Delete SMS | Yes |
| GET | `/status/signal` | Signal strength | No |
| GET | `/status/network` | Network info | No |
| GET | `/status/reset` | Reset modem | No |

## 🚨 Troubleshooting

### Device Not Found
- Check USB connection: `ls /dev/ttyUSB*`
- **Recommended:** Use stable device ID instead of `/dev/ttyUSB0`:
  ```bash
  ls -la /dev/serial/by-id/
  ```
- Verify device permissions
- Try different USB ports
- Check `dmesg | grep tty` for device detection

### SMS Not Sending
- Check signal strength (should be > 20%)
- Verify SIM card has credit
- Ensure PIN is correct or disabled
- Check network registration status

### MQTT Not Working
- Verify MQTT broker is running
- Check MQTT credentials
- Look for connection errors in add-on logs
- Ensure topic prefix doesn't conflict

### Code 69 Error
- This is SMSC (SMS Center) issue
- Add-on automatically uses Location 1 fallback
- Works same as REST API

## 📋 Version History

See [CHANGELOG.md](./CHANGELOG.md) for detailed version history.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/pavelve/home-assistant-addons/issues)
- **Documentation**: This page and Swagger UI at `/docs/`
- **Source**: Based on [sms-gammu-gateway](https://github.com/pajikos/sms-gammu-gateway)

## 📜 License

Based on pajikos/sms-gammu-gateway, licensed under Apache License 2.0.

---

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg