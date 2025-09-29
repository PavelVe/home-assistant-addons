# Teltonika Server Add-on

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

Professional GPS tracking server for Teltonika devices with proper AVL protocol implementation, IMEI-based security, and comprehensive logging.

## Features

### 🔌 **Proper Teltonika AVL Protocol**
- **IMEI Handshake**: Correct authentication sequence with accept/reject responses
- **Codec8 & Codec8 Extended**: Full support for both AVL data formats
- **GPS Data Parsing**: Extracts coordinates, speed, altitude, satellites, I/O data
- **Protocol Compliance**: Server responds according to Teltonika specifications

### 🔒 **IMEI-Based Security**
- **IMEI Filtering**: Allow only specific devices (better than IP filtering)
- **Device Registry**: Automatic tracking of all connected devices
- **Connection History**: Monitor device activity and connection patterns
- **Fleet Management**: Perfect for managing multiple Teltonika devices

### 📊 **Advanced Logging & Monitoring**
- **Persistent Logs**: Stored in `/share/teltonika_logs/` (survives add-on updates)
- **Log Rotation**: New log file for each add-on restart with timestamp
- **Parsed Data**: Human-readable GPS coordinates, speed, I/O status
- **Raw Data**: Hex dumps for debugging and protocol analysis

### 🌐 **Enhanced Web Interface**
- **Real-time Log Viewing**: Last 500 lines with 10s auto-refresh
- **Multi-Log Support**: Displays data from all log files
- **Clean Interface**: Focused on essential log information
- **Responsive Design**: Works on desktop and mobile devices

### ⚙️ **Professional Configuration**
- **Multi-threading**: Concurrent connections from multiple devices
- **Configurable Ports**: Independent TCP and web server ports
- **Architecture Support**: amd64, aarch64, armv7, i386, armhf
- **Home Assistant Integration**: Full Ingress support with custom icon

## Configuration

### Required Settings

#### TCP Port
Port for receiving AVL data from Teltonika GPS devices (default: 3030)

#### Web Port  
Port for accessing the web interface (default: 3031)

### Security Settings

#### IMEI Filtering
Specify which devices are allowed to connect:

```json
{
  "allowed_imeis": []                    // Empty = all devices allowed
}
```

```json
{
  "allowed_imeis": [                     // Only these IMEIs allowed
    "356307042441013",
    "356307042441014"
  ]
}
```

#### Persistent Logging
Store logs permanently in Home Assistant config:

```json
{
  "log_to_config": true                  // Logs survive add-on updates
}
```

## Usage

### Setup
1. Install the add-on from this repository
2. Configure TCP port (match your Teltonika device settings)
3. Set IMEI filtering if needed (recommended for security)
4. Enable persistent logging to `/share/`
5. Start the add-on

### Device Configuration
Configure your Teltonika devices to send data to:
- **Server IP**: Your Home Assistant IP address
- **Server Port**: Your configured TCP port (default 3030)
- **Protocol**: TCP
- **Codec**: Codec8 or Codec8 Extended

### Monitoring
- **Web Interface**: Access via Home Assistant Ingress
- **IMEI Registry**: Available in `/share/teltonika_logs/imei_registry.json`
- **Real-time Logs**: View parsed GPS data and device activity

## Data Access

### Web Interface
- **Main Dashboard**: Available through Home Assistant Ingress
- **Direct Access**: `http://[HA-IP]:[web-port]/` (if Ingress disabled)
- **Real-time Logs**: Automatic refresh every 10 seconds

### File Access
- **Persistent Logs**: `/share/teltonika_logs/teltonika_YYYYMMDD_HHMMSS.log`
- **IMEI Registry**: `/share/teltonika_logs/imei_registry.json`
- **Current Log**: `/data/tcp_data.log` (if persistent logging disabled)

### Log Format
```
[2025-09-03 15:44:52] IMEI: 356307042441013 connected from ('192.168.1.100', 1234) (NEW DEVICE)
[2025-09-03 15:44:52] IMEI: 356307042441013 | Time: 2025-09-03 15:44:52 | GPS: 54.000000,24.000000 | Speed: 60km/h | Altitude: 100m | Angle: 0° | Sats: 8 | Priority: 1 | IO: 1 elements [239=1]
```

## Troubleshooting

### Device Not Connecting
1. Check IMEI filtering configuration
2. Verify TCP port accessibility
3. Review logs for connection attempts
4. Ensure device uses correct server IP/port

### Incomplete Data
1. Check if proper AVL protocol is configured on device
2. Verify Codec8/8E support in device firmware
3. Review raw data logs for protocol issues

### Log Access Issues
1. Enable `log_to_config: true` for persistent storage
2. Use Home Assistant File Editor to access `/share/teltonika_logs/`
3. Check IMEI Registry for device connection history

## Support

For issues, feature requests, and documentation:
- **GitHub Issues**: [repository](https://github.com/pavelve/home-assistant-addons)
- **Discussions**: Use GitHub Discussions for questions and tips

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg