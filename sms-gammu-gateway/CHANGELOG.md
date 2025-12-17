# Changelog

All notable changes to this project will be documented in this file.

## [1.5.6] – 2025-12-17

### Fixed

* Proper error handling for SMS send failures
* `/sms` endpoint returns 503 on modem/connectivity errors
* Handled Timeout and Gammu error codes

## [1.5.5] - 2025-12-15

### Added
- Flash SMS (Class 0) support via REST API, MQTT and Home Assistant UI
- New `flash` boolean parameter for `/sms` endpoint and MQTT payload
- Raspberry Pi 5 serial port support (`/dev/ttyAMA0`, `/dev/ttyAMA1`)

### Fixed
- Phone Number field validation now allows comma for multiple recipients
- SMS sending timeouts on slow networks
- Increased Gammu and Python wrapper timeouts
- Added SMSC configuration logging on startup

## [1.5.4] - 2025-11-24

### Fixed
- **MQTT Multiple Recipients** - Fixed bug where MQTT SMS sending didn't support comma-separated phone numbers
- MQTT handler now properly splits phone numbers by comma (matching REST API behavior)
- Formats like `+420123456,+420789012` or `0412345,0478901` now work correctly via MQTT
- SMS counter now correctly increments for each recipient when sending to multiple numbers

## [1.5.3] - 2025-11-06

### Added
- **Extended Device Support** - Added ttyUSB4, ttyUSB5 for multi-port Huawei modems
- **Extended ACM Support** - Added ttyACM1, ttyACM2, ttyACM3 for cdc_acm driver modems

## [1.5.2] - 2025-11-04

### Fixed
- **Modem Communication Freezing** - Fixed hanging AT commands with Gammu commtimeout (10s) and Python-level timeout (15s)
- **Race Condition** - Added threading lock to serialize all Gammu operations and prevent parallel AT command execution
- **Buffer Overflow** - Added 0.3s delay between commands to prevent modem buffer issues (Huawei E1750)

### Enhanced
- **Automatic Recovery** - Modem soft reset after 2 consecutive failures
- **Offline Detection** - Increased timeout from 10 to 15 minutes

## [1.5.1] - 2025-10-29

### Enhanced
- **Improved Modem Status Monitoring** - Enhanced online/offline detection with better error handling and recovery
- **Extended Message Length** - Message Text field now supports up to 255 characters (MQTT text entity limit)
- Gammu automatically splits longer messages into multiple SMS parts during sending. Incoming message is also limited to 255 characters.
- **Persistent Device IDs** - Support for stable `/dev/serial/by-id/` paths that survive modem reconnections
- **Smart Availability** - Entities automatically become unavailable in Home Assistant when addon stops

## [1.5.0] - 2025-10-28

### 🚀 Major Feature Update - SMS Management & Tracking Suite

This release introduces comprehensive SMS management capabilities including automatic Unicode handling, persistent message tracking with cost monitoring, advanced SIM card management, and detailed modem diagnostics.

📱 **What's New in the SMS Gateway Addon**

Based on your feedback, I’ve implemented a bunch of new features! 🚀

* 🔤 Automatic Unicode detection – ensures correct delivery of messages with diacritics
* 📊 Persistent sent SMS counter + optional total cost sensor
* 🔘 Button to reset counters
* 🧹 Auto-delete of read SMS + button to delete all messages
* 🧠 New REST API endpoints for SMS management
* 📡 Extended modem diagnostics (IMEI, model, IMSI, manufacturer)
* 💾 SMS storage capacity sensor
* 🌍 Added new translations – now available in **10 languages**

💬 Update now and explore all the new features!


### Added

#### SMS Sending Enhancements (MQTT/REST)
- **Automatic Unicode Detection** - When sending SMS via MQTT, the addon now automatically detects whether the message contains non-ASCII characters (such as diacritics like háčky and čárky). When detected, Unicode mode is automatically enabled, ensuring proper delivery of messages with special characters.
- MQTT method intelligently switches encoding based on message content
- REST API remains unchanged with explicit `unicode` parameter control for backward compatibility

#### SMS Counter & Cost Tracking
- **Persistent SMS Sent Counter** - New sensor `sms_gateway_sent_count` tracks total number of SMS messages sent through the addon (via both MQTT and REST API)
- Counter state persists across addon restarts using JSON file storage at `/data/sms_counter.json`
- Counter increments automatically on every successful SMS send operation
- **Optional Cost Tracking Sensor** - New configuration option `sms_cost_per_message` (default: 0.0) enables SMS cost monitoring
- When set to non-zero value, creates `sms_gateway_total_cost` sensor displaying cumulative cost of all sent messages
- **Configurable Currency** - New `sms_cost_currency` configuration field for customizing cost display (EUR, USD, CZK, etc.)
- **Reset Counter Button** - New MQTT button `sms_gateway_reset_counter` for easy one-click reset of SMS counter and total costs back to zero

#### SIM Card SMS Management
- **Automatic SMS Deletion** - New configuration option `auto_delete_read_sms` (default: false) automatically deletes SMS messages from SIM card after they are read during monitoring cycle
- Helps prevent SIM card storage exhaustion on cards with limited SMS capacity
- **Delete All SMS Button** - New MQTT button `sms_gateway_delete_all_sms` for bulk deletion of all SMS messages stored on SIM card
- **New REST Endpoint** - Added `DELETE /sms/deleteall` endpoint for programmatic deletion of all SMS messages via REST API
- **Automatic Capacity Refresh** - SMS storage capacity sensor automatically updates after both manual deletion (via button) and automatic deletion operations

#### Modem Diagnostics & Information
- **Enhanced Modem Information Sensors** - New diagnostic sensors providing detailed hardware information:
  - **Modem IMEI** - International Mobile Equipment Identity number
  - **Modem Manufacturer** - Device manufacturer name
  - **Modem Model** - Specific device model identification
  - **SIM IMSI** - International Mobile Subscriber Identity from inserted SIM card
- **SMS Storage Capacity Sensor** - New sensor `sms_gateway_sms_storage_used` displaying number of SMS messages currently stored on SIM card
- Includes full capacity details in sensor attributes (SIMUsed, SIMSize, PhoneUsed, PhoneSize, TemplatesUsed)
- Displayed unit: "messages" with icon `mdi:email-multiple`
- **New REST Endpoints** for modem information:
  - `GET /status/modem` - Retrieve modem hardware information (IMEI, manufacturer, model, firmware version)
  - `GET /status/sim` - Get SIM card information (IMSI number)
  - `GET /status/sms_capacity` - Query SMS storage capacity and current usage statistics

### Enhanced
- **Counter Integration** - Both MQTT and REST API methods increment the SMS counter automatically on successful message transmission
- **MQTT Discovery** - Extended Home Assistant MQTT discovery with all new sensors and buttons for seamless integration
- **Persistent Storage** - SMS counter and cost data survives addon restarts and updates

### Configuration
- `sms_cost_per_message` (float, default: 0.0) - Price per SMS message for cost tracking (set to 0 to disable cost sensor)
- `sms_cost_currency` (string, default: "CZK") - Currency code for cost display (EUR, USD, CZK, GBP, etc.)
- `auto_delete_read_sms` (bool, default: false) - Enable automatic deletion of SMS after reading during monitoring

###  Extended Device Support
- Added `/dev/ttyUSB2`, `/dev/ttyUSB3`, and `/dev/ttyS0` to supported device paths for broader
  hardware compatibility

### Technical Details
- Added `detect_unicode_needed()` function using ASCII encoding check to determine if Unicode mode is required
- Created `SMSCounter` class with JSON-based persistent storage mechanism
- MQTT Unicode handling: uses explicit `unicode` parameter if provided, otherwise performs automatic detection
- SMS counter data published to `{topic_prefix}/sms_counter/state` as JSON: `{"count": N, "cost": X.XX}`
- Modem information published on addon startup and available via REST API endpoints
- Auto-delete functionality integrated into SMS monitoring loop when enabled
- SMS storage capacity automatically refreshed after deletion operations to reflect current state


## [1.3.2] - 2025-08-21

### Changed
- **Sensor Naming Improvement** - Renamed "USB Device Status" to "Modem Status" for better clarity
- Updated sensor icon from `mdi:usb` to `mdi:connection` for more appropriate representation
- Improved logging messages with better emoji indicators (📶 ONLINE, ❌ OFFLINE)
- Updated unique_id from `sms_gateway_device_status` to `sms_gateway_modem_status`

## [1.3.1] - 2025-08-21

### Added
- **USB Device Status Sensor** - New MQTT sensor monitoring GSM device connectivity
- Real-time tracking of device communication success/failure
- Detailed device status with attributes: last_seen, consecutive_failures, last_error
- Smart offline detection (10 minutes without successful communication)
- Status logging with emoji indicators (📱 ONLINE, 🚫 OFFLINE, ❓ UNKNOWN)

### Enhanced
- **Comprehensive Gammu Operation Tracking** - All gammu communications now monitored
- REST API endpoints, periodic status checks, SMS operations tracked
- Automatic device status updates on every communication attempt
- Home Assistant auto-discovery includes new USB Device Status sensor

### Technical Details
- Added `DeviceConnectivityTracker` class for communication monitoring
- Wrapped all gammu operations with connectivity tracking
- Device status published to MQTT topic: `{topic_prefix}/device_status/state`
- Status states: "online", "offline", "unknown" with detailed attributes

## [1.3.0] - 2025-08-21

### Fixed
- **MQTT Unicode Support** - Fixed MQTT SMS sending to properly handle Unicode messages
- MQTT method now respects `"unicode": true` parameter in JSON payload (was previously ignored)
- Unicode messages sent via MQTT now display correctly instead of showing ????

### Technical Details
- Updated `mqtt_publisher.py` to extract and use unicode parameter from MQTT JSON payload
- Modified `_send_sms_via_gammu()` method to accept unicode_mode parameter
- Fixed hard-coded `"Unicode": False` that prevented Unicode encoding in MQTT messages
- MQTT Unicode handling now matches REST API and Native HA Service behavior

## [1.2.9] - 2025-08-19

### Fixed
- **Signal Strength Sensor** - Removed invalid `device_class: "signal_strength"` to make sensor appear in Home Assistant
- **MQTT Discovery** - Signal strength sensor now properly discovered and displayed in HA

### Technical Details
- Signal strength sensor uses percentage (%) instead of dBm, so device_class was incompatible
- Removed device_class allows HA to treat it as generic sensor with % unit

## [1.2.8] - 2025-08-19

### Changed
- Renamed add-on directory from `GamuGatewaySMS` to `sms-gammu-gateway` for consistency

## [1.2.6] - 2025-08-19

### Changed
- **Smart Field Clearing** - Only message text clears after sending, phone number persists for convenience
- Phone number stays for sending multiple messages to same recipient

## [1.2.5] - 2025-08-19

### Fixed
- **REST API Notify Compatibility** - API now accepts both standard and Home Assistant notify parameters
- Supports `text`/`message` and `number`/`target` interchangeably for better compatibility

## [1.2.4] - 2025-08-19

### Fixed
- **UI/Backend Sync** - Text fields now properly synchronize between Home Assistant UI and backend state
- Enhanced MQTT synchronization with bidirectional state handling

## [1.2.3] - 2025-08-19

### Fixed
- **Text Field Clearing** - Both phone number and message fields now clear reliably after sending
- Enhanced field validation and UI synchronization

### Removed
- SMSC Number configuration field (no longer needed)

## [1.2.1] - 2025-08-19

### Added
- **SMSC Configuration** - New optional "SMSC Number" field in addon configuration
- Smart SMSC priority: configured SMSC → SIM SMSC → fallback

## [1.2.0] - 2025-08-19

### Fixed
- **Gammu Error Code 69** - Better handling of SMSC number issues with automatic detection
- Both text fields now clear after SMS send for consistency

### Changed
- **Breaking Change**: Both text fields now clear after SMS send (was keeping phone number)

## [1.1.9] - 2025-08-19

### Fixed
- **Empty Fields on Startup** - Text fields now start empty instead of showing "unknown"
- **Smart Field Clearing** - Only message text clears after send, phone number stays
- **Better Error Messages** - User-friendly SMS error messages instead of raw gammu codes

## [1.1.8] - 2025-08-19

### Added
- **Text Input Fields** - Phone Number and Message Text fields directly in SMS Gateway device
- **Smart Button Functionality** - Send SMS button now uses values from text input fields
- **Auto-clear Fields** - Text fields automatically clear after successful SMS send
- **Field Validation** - Shows error if trying to send without filling required fields

## [1.1.7] - 2025-08-19

### Added
- **SMS Send Button** - New button entity in Home Assistant device for easy SMS sending
- **SMS Send Status Sensor** - Shows status of SMS sending operations
- **Home Assistant Service** - Native `send_sms` service with phone number and message fields

## [1.1.5] - 2025-08-19

### Added
- **MQTT SMS Sending** - Send SMS messages via MQTT topic subscription
- **Command Topic** - Subscribe to MQTT commands for SMS sending
- **JSON Command Format** - Simple JSON payload: `{"number": "+420123456789", "text": "Hello!"}`

## [1.1.4] - 2025-08-19

### Added
- **Simple Status Page** - New user-friendly HTML page for Home Assistant Ingress
- **External Swagger Link** - Button to open full API documentation

## [1.1.0] - 2025-08-19

### Added
- **SMS Monitoring Toggle** - Configuration option to enable/disable automatic SMS detection
- **Configurable Check Interval** - Adjust SMS monitoring frequency (30-300 seconds)
- **Enhanced SMS Storage** - SMS messages stored in HA database with full history

## [1.0.9] - 2025-08-19

### Added
- **Automatic SMS Detection** - Background monitoring for incoming SMS messages
- **Real-time SMS Notifications** - New SMS automatically published to MQTT

## [1.0.8] - 2025-08-19

### Added
- **Initial MQTT State Publishing** - Publish sensor states immediately on startup
- **Retained MQTT Messages** - Values persist across Home Assistant restarts

## [1.0.5] - 2025-08-19

### Added
- **MQTT Bridge** - Optional MQTT integration with Home Assistant auto-discovery
- **3 Automatic Sensors** - GSM Signal Strength, Network Info, Last SMS Received
- **Periodic Status Updates** - Every 5 minutes to MQTT
- **Real-time SMS Notifications** - Instant MQTT publish on SMS receipt

## [1.0.4] - 2025-08-19

### Added
- **Swagger UI Documentation** - Professional API documentation at `/docs/`
- Interactive API testing interface with organized endpoints

## [1.0.0] - 2025-08-19

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