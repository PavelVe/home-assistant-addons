# SMS Gammu Gateway - Documentation

## 🚀 Quick Start

### Step 1: Connect GSM Modem
- Connect your USB GSM modem (SIM800L, Huawei, etc.)
- Verify detection: Settings → System → Hardware → Search for "ttyUSB" or "ttyACM"
- Supported device paths: `/dev/ttyUSB0-3`, `/dev/ttyACM0`, `/dev/ttyS0`

### Step 2: Basic Configuration
```yaml
device_path: "/dev/ttyUSB0"  # Path to modem
username: "admin"             # Change this!
password: "strong_password"   # Change this!
```

### Step 3: Enable MQTT (Recommended)
```yaml
mqtt_enabled: true
mqtt_host: "core-mosquitto"
```

### Step 4: Start the Add-on
- Click **START**
- Check the log for successful startup
- New device **SMS Gateway** will appear in HA

## 📱 How to Send SMS

### Method 1: UI Button (Easiest)
1. Go to **Devices** → **SMS Gateway**
2. Fill **Phone Number** (e.g., +420123456789)
3. Fill **Message Text**
4. Click **Send SMS**

### Method 2: Notify Service
```yaml
service: notify.sms_gateway
data:
  message: "Test message"
  target: "+420123456789"
```

### Method 3: MQTT
```yaml
service: mqtt.publish
data:
  topic: "homeassistant/sensor/sms_gateway/send"
  payload: '{"number": "+420123456789", "text": "Alert!"}'
```

### Method 4: REST API
```bash
curl -X POST http://192.168.1.x:5000/sms \
  -u admin:password \
  -d '{"text": "Test", "number": "+420123456789"}'
```

## 🔧 Configuration

### Basic Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `device_path` | `/dev/ttyUSB0` | Path to GSM modem (supported: ttyUSB0-3, ttyACM0, ttyS0) |
| `pin` | `""` | SIM card PIN (empty = no PIN) |
| `port` | `5000` | API port |
| `username` | `admin` | API username |
| `password` | `password` | **⚠️ CHANGE THIS!** |

### MQTT Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `mqtt_enabled` | `true` | Enable MQTT integration |
| `mqtt_host` | `core-mosquitto` | MQTT broker hostname |
| `mqtt_port` | `1883` | MQTT broker port |
| `mqtt_username` | `""` | MQTT username (empty for no auth) |
| `mqtt_password` | `""` | MQTT password (empty for no auth) |
| `sms_monitoring_enabled` | `true` | Detect incoming SMS automatically |
| `sms_check_interval` | `60` | SMS check interval (30-300 seconds) |

### SMS Management Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sms_cost_per_message` | `0.0` | Price per SMS (0 = cost tracking disabled) |
| `sms_cost_currency` | `CZK` | Currency code (EUR, USD, CZK, GBP, etc.) |
| `auto_delete_read_sms` | `false` | Auto-delete SMS after reading (frees SIM space) |

## 📊 MQTT Sensors

After enabling MQTT, these entities are automatically created:

### Status Sensors
| Entity | Type | Description |
|--------|------|-------------|
| `sensor.sms_gateway_modem_status` | Sensor | Modem connectivity status (online/offline) |
| `sensor.sms_gateway_signal_strength` | Sensor | GSM signal strength in % |
| `sensor.sms_gateway_network` | Sensor | Network operator name |
| `sensor.sms_gateway_last_sms_received` | Sensor | Last received SMS message |
| `sensor.sms_gateway_sms_send_status` | Sensor | SMS send operation status |

### Modem Information Sensors
| Entity | Type | Description |
|--------|------|-------------|
| `sensor.sms_gateway_modem_imei` | Sensor | Modem IMEI number |
| `sensor.sms_gateway_modem_model` | Sensor | Modem manufacturer and model |
| `sensor.sms_gateway_sim_imsi` | Sensor | SIM card IMSI number |
| `sensor.sms_gateway_sms_storage_used` | Sensor | Number of SMS on SIM card |

### SMS Counter & Cost Tracking
| Entity | Type | Description |
|--------|------|-------------|
| `sensor.sms_gateway_sms_sent_count` | Sensor | Total SMS sent through addon |
| `sensor.sms_gateway_total_cost` | Sensor | Total cost of sent SMS (if `sms_cost_per_message > 0`) |

### Controls
| Entity | Type | Description |
|--------|------|-------------|
| `text.sms_gateway_phone_number` | Text input | Phone number input field |
| `text.sms_gateway_message_text` | Text input | Message text input field |
| `button.sms_gateway_send_button` | Button | Send SMS button |
| `button.sms_gateway_reset_counter` | Button | Reset SMS counter and costs |
| `button.sms_gateway_delete_all_sms` | Button | Delete all SMS from SIM card |

## 🎯 Automation Examples

### SMS on Door Open
```yaml
automation:
  - alias: "Security - Door Opened"
    trigger:
      platform: state
      entity_id: binary_sensor.front_door
      to: "on"
    action:
      service: notify.sms_gateway
      data:
        message: "ALERT: Front door opened!"
        target: "+420123456789"
```

### SMS on Low Temperature
```yaml
automation:
  - alias: "Freeze Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.outside_temperature
      below: 0
    action:
      service: notify.sms_gateway
      data:
        message: "Warning: Freezing temperature! Current: {{ states('sensor.outside_temperature') }}°C"
        target: "+420123456789"
```

### SMS on Power Failure (UPS)
```yaml
automation:
  - alias: "Power Failure Alert"
    trigger:
      platform: state
      entity_id: sensor.ups_status
      to: "on_battery"
    action:
      service: notify.sms_gateway
      data:
        message: "Power failure detected! UPS on battery."
        target: "+420123456789"
```

## 📡 REST API

### Swagger Documentation
Full API documentation: `http://your-ha-ip:5000/docs/`

### Main Endpoints

#### SMS Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sms` | Send SMS message |
| GET | `/sms` | Get all SMS messages |
| GET | `/sms/{id}` | Get specific SMS by ID |
| DELETE | `/sms/{id}` | Delete specific SMS |
| DELETE | `/sms/deleteall` | Delete all SMS from SIM card |

#### Status & Information
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status/signal` | GSM signal strength |
| GET | `/status/network` | Network operator info |
| GET | `/status/modem` | Modem hardware info (IMEI, model, manufacturer) |
| GET | `/status/sim` | SIM card information (IMSI) |
| GET | `/status/sms_capacity` | SMS storage capacity and usage |
| GET | `/status/reset` | Reset modem connection |

### API Examples (Python)

**Send SMS:**
```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.post(
    'http://192.168.1.x:5000/sms',
    auth=HTTPBasicAuth('admin', 'password'),
    json={
        'text': 'Test message from Python',
        'number': '+420123456789'
    }
)
print(response.json())
```

**Get Modem Information:**
```python
# Get IMEI, manufacturer, model
response = requests.get(
    'http://192.168.1.x:5000/status/modem',
    auth=HTTPBasicAuth('admin', 'password')
)
print(response.json())
```

**Check SMS Storage Capacity:**
```python
# Get SIM storage usage
response = requests.get(
    'http://192.168.1.x:5000/status/sms_capacity',
    auth=HTTPBasicAuth('admin', 'password')
)
capacity = response.json()
print(f"SMS on SIM: {capacity['SIMUsed']}/{capacity['SIMSize']}")
```

**Delete All SMS:**
```python
# Clear all SMS from SIM card
response = requests.delete(
    'http://192.168.1.x:5000/sms/deleteall',
    auth=HTTPBasicAuth('admin', 'password')
)
print(response.json())
```

## 🔴 Troubleshooting

### Modem Not Detected
```bash
# Check USB devices
ls -la /dev/ttyUSB*

# Check kernel messages
dmesg | grep ttyUSB

# Restart add-on after connecting modem
```

### SMS Not Sending
1. **Check signal**: Should be > 20%
2. **Verify credit**: SIM card must have credit
3. **PIN code**: Either correct or disabled
4. **Network**: Check registration status

### Code 69 Error (SMSC)
- Add-on automatically uses Location 1 fallback
- Works the same as REST API
- No SMSC configuration needed

### MQTT Not Working
1. Verify MQTT broker is running
2. Check credentials
3. Look for connection errors in log
4. Ensure topic prefix doesn't conflict

### Text Fields Not Synchronized
- Add-on uses `retain=True` for synchronization
- Wait 2 seconds after restart for sync
- Phone number persists, message clears

## 💡 Tips & Tricks

### SMS Counter & Cost Tracking
Enable cost tracking by setting a price per SMS:
```yaml
sms_cost_per_message: 2.5  # e.g., 2.5 CZK per SMS
sms_cost_currency: "CZK"
```
This creates a `sensor.sms_gateway_total_cost` showing cumulative costs. Reset anytime using the **Reset Counter** button.

### Automatic SIM Storage Management
Prevent "SIM full" errors by auto-deleting read SMS:
```yaml
auto_delete_read_sms: true
```
SMS messages are automatically deleted after being read and published to MQTT. Storage capacity is tracked in `sensor.sms_gateway_sms_storage_used`.

### Monitor Modem Health
New sensors provide detailed diagnostics:
- `sensor.sms_gateway_modem_status` - Real-time connectivity (online/offline)
- `sensor.sms_gateway_modem_imei` - Device identification
- `sensor.sms_gateway_sim_imsi` - SIM card identification
- `sensor.sms_gateway_sms_storage_used` - Track SIM capacity usage

### Multiple Recipients
```json
{
  "number": "+420111111111,+420222222222",
  "text": "Broadcast message"
}
```

### Unicode Support (Special Characters)

**MQTT Method (Automatic Detection):**
When sending SMS via MQTT, Unicode mode is automatically detected based on message content. If your message contains non-ASCII characters (háčky, čárky, emojis), Unicode encoding is automatically enabled.

```yaml
service: mqtt.publish
data:
  topic: "homeassistant/sensor/sms_gateway/send"
  payload: '{"number": "+420123456789", "text": "Příliš žluťoučký kůň"}'
  # Unicode automatically detected - no "unicode" parameter needed!
```

**REST API Method (Explicit Parameter):**
For REST API, you must explicitly set the `unicode` parameter:

```json
{
  "number": "+420123456789",
  "text": "Příliš žluťoučký kůň",
  "unicode": true
}
```

### Custom Notify Name
```yaml
notify:
  - name: Security_SMS
    platform: rest
    resource: http://192.168.1.x:5000/sms
    method: POST_JSON
    authentication: basic
    username: admin
    password: your_password
    target_param_name: number
    message_param_name: message
```

## 📝 Version History

See [CHANGELOG.md](./CHANGELOG.md) for complete version history and detailed changes.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/pavelve/home-assistant-addons/issues)
- **Swagger UI**: http://your-ha-ip:5000/docs/
- **Original Project**: [sms-gammu-gateway](https://github.com/pajikos/sms-gammu-gateway)