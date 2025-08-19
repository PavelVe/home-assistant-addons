# Changelog

All notable changes to this project will be documented in this file.

## [1.2.8] - 2025-01-19

### Changed
- Renamed add-on directory from `GamuGatewaySMS` to `sms-gammu-gateway` for consistency

## [1.2.6] - 2025-01-19

### Changed
- **Smart Field Clearing** - Only message text clears after sending, phone number persists for convenience
- Phone number stays for sending multiple messages to same recipient

## [1.2.5] - 2025-01-19

### Fixed
- **REST API Notify Compatibility** - API now accepts both standard and Home Assistant notify parameters
- Supports `text`/`message` and `number`/`target` interchangeably for better compatibility

## [1.2.4] - 2025-01-19

### Fixed
- **UI/Backend Sync** - Text fields now properly synchronize between Home Assistant UI and backend state
- Enhanced MQTT synchronization with bidirectional state handling

## [1.2.3] - 2025-01-19

### Fixed
- **Text Field Clearing** - Both phone number and message fields now clear reliably after sending
- Enhanced field validation and UI synchronization

### Removed
- SMSC Number configuration field (no longer needed)

## [1.2.1] - 2025-01-19

### Added
- **SMSC Configuration** - New optional "SMSC Number" field in addon configuration
- Smart SMSC priority: configured SMSC → SIM SMSC → fallback

## [1.2.0] - 2025-01-19

### Fixed
- **Gammu Error Code 69** - Better handling of SMSC number issues with automatic detection
- Both text fields now clear after SMS send for consistency

### Changed
- **Breaking Change**: Both text fields now clear after SMS send (was keeping phone number)

## [1.1.9] - 2025-01-19

### Fixed
- **Empty Fields on Startup** - Text fields now start empty instead of showing "unknown"
- **Smart Field Clearing** - Only message text clears after send, phone number stays
- **Better Error Messages** - User-friendly SMS error messages instead of raw gammu codes

## [1.1.8] - 2025-01-19

### Added
- **Text Input Fields** - Phone Number and Message Text fields directly in SMS Gateway device
- **Smart Button Functionality** - Send SMS button now uses values from text input fields
- **Auto-clear Fields** - Text fields automatically clear after successful SMS send
- **Field Validation** - Shows error if trying to send without filling required fields

## [1.1.7] - 2025-01-19

### Added
- **SMS Send Button** - New button entity in Home Assistant device for easy SMS sending
- **SMS Send Status Sensor** - Shows status of SMS sending operations
- **Home Assistant Service** - Native `send_sms` service with phone number and message fields

## [1.1.5] - 2025-01-19

### Added
- **MQTT SMS Sending** - Send SMS messages via MQTT topic subscription
- **Command Topic** - Subscribe to MQTT commands for SMS sending
- **JSON Command Format** - Simple JSON payload: `{"number": "+420123456789", "text": "Hello!"}`

## [1.1.4] - 2025-01-19

### Added
- **Simple Status Page** - New user-friendly HTML page for Home Assistant Ingress
- **External Swagger Link** - Button to open full API documentation

## [1.1.0] - 2025-01-19

### Added
- **SMS Monitoring Toggle** - Configuration option to enable/disable automatic SMS detection
- **Configurable Check Interval** - Adjust SMS monitoring frequency (30-300 seconds)
- **Enhanced SMS Storage** - SMS messages stored in HA database with full history

## [1.0.9] - 2025-01-19

### Added
- **Automatic SMS Detection** - Background monitoring for incoming SMS messages
- **Real-time SMS Notifications** - New SMS automatically published to MQTT

## [1.0.8] - 2025-01-19

### Added
- **Initial MQTT State Publishing** - Publish sensor states immediately on startup
- **Retained MQTT Messages** - Values persist across Home Assistant restarts

## [1.0.5] - 2025-01-19

### Added
- **MQTT Bridge** - Optional MQTT integration with Home Assistant auto-discovery
- **3 Automatic Sensors** - GSM Signal Strength, Network Info, Last SMS Received
- **Periodic Status Updates** - Every 5 minutes to MQTT
- **Real-time SMS Notifications** - Instant MQTT publish on SMS receipt

## [1.0.4] - 2025-01-19

### Added
- **Swagger UI Documentation** - Professional API documentation at `/docs/`
- Interactive API testing interface with organized endpoints

## [1.0.0] - 2025-01-19

### Added
- Initial release of SMS Gammu Gateway Home Assistant Add-on
- REST API for sending and receiving SMS messages
- Support for USB GSM modems with AT commands
- Basic authentication for SMS endpoints
- Multi-architecture support (amd64, i386, aarch64, armv7, armhf)

### Features
- Send SMS via POST /sms
- Retrieve all SMS via GET /sms
- Get specific SMS by ID via GET /sms/{id}
- Delete SMS by ID via DELETE /sms/{id}
- Check signal quality via GET /signal
- Get network information via GET /network
- Reset modem via GET /reset
- HTTP Basic Authentication for protected endpoints