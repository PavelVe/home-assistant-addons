# Changelog

## 1.5.1 🔧 WEB INTERFACE FIX

### 🐛 Bug Fixes
- **Fixed Tab Navigation**: Opraveny JavaScript chyby v webovém rozhraní
- **showTab Function**: Vyřešena chyba `showTab is not defined`
- **Regex Error**: Opravena chyba "Invalid regular expression" v server log zobrazování

### 🔧 Technical Fixes
- JavaScript `event.target` nahrazeno parametrem `element`
- Regulární výraz `replace(/\n/g, '<br>')` nahrazen `split('\\n').join('<br>')`
- Všechny tab odkazy nyní fungují správně

## 1.5.0 🕒 TIMESTAMPED LOGGING

### ✨ New Features
- **📅 Timestamped Console Logs**: Všechny výpisy v HA addon logu mají časové značky
- **🔍 Enhanced Debug Info**: Lepší debugging s časovými údaji pro každou událost

### 🔧 Improvements
- **Consistent Logging**: Unifikované logování s `log_print()` funkcí
- **Better Error Tracking**: Časové značky pro všechny error messages
- **HA Addon Visibility**: Jasné časové značky v Home Assistant addon log panelu

### 📊 Log Format
```
[2025-09-05 10:30:15] TCP server listening on 0.0.0.0:3030 (all IMEIs allowed)
[2025-09-05 10:30:16] Teltonika connection from ('192.168.1.100', 45123)
[2025-09-05 10:30:16] IMEI authenticated: 350317176700155 (KNOWN DEVICE)
[2025-09-05 10:30:17] Parsed 5 AVL records (codec8_extended) from IMEI 350317176700155
```

## 1.4.0 🚀 MAJOR ARCHITECTURE REDESIGN

### ✨ Revolutionary Features
- **🗂️ Per-Device CSV Logging**: Každé zařízení má vlastní CSV soubor s GPS historií
- **🔄 TCP Buffer Management**: Robustní řešení TCP fragmentace s file-based buffery  
- **📊 Modern Web Interface**: Nové tabové rozhraní s přehledem zařízení
- **📁 Structured Data Storage**: Organizovaná struktura složek `/share/teltonika/`
- **🛡️ Buffer Monitoring**: Real-time monitoring TCP bufferů a jejich velikostí

### 🏗️ Architecture Changes
- **CSV Logger System**: Kompletně nový systém pro strukturované ukládání GPS dat
- **Buffer Manager**: Inteligentní správa TCP packet fragmentů per-IMEI  
- **Unified Directory**: Vše pod `/share/teltonika/` pro konzistenci
- **Device Management**: Automatické vytváření device info a historie

### 🌐 Web Interface Overhaul
- **4 Tabs**: Přehled, Zařízení, Server Log, Buffery
- **Device Selection**: Kliknout na zařízení → zobraz GPS data  
- **Auto-refresh**: Automatické obnovování logů a bufferů
- **GPS Data Tables**: Formátované souřadnice, rychlost, I/O data
- **Buffer Status**: Monitoring velikosti a stavu TCP bufferů

### 🔧 Technical Improvements  
- **Zero Duplicates**: Vyřešena fragmentace TCP - žádné duplicitní záznamy
- **Proper Packet Assembly**: Správné spojování fragmentovaných TCP paketů
- **Enhanced Error Handling**: Komprehensivní error handling a logování
- **Per-IMEI Processing**: Separátní buffery a CSV soubory pro každé zařízení

### 📂 Simplified File Structure
```
/share/teltonika/
├── server.log                # Server události a raw data
├── imei_registry.json        # IMEI registry a statistiky
└── devices/
    └── {imei}/
        ├── data.csv          # GPS záznamy
        ├── info.json         # Device metadata
        └── buffer.tmp        # TCP buffer (dočasný)
```

### 🐛 Major Bug Fixes
- **TCP Fragmentation**: Kompletně vyřešeno - žádné ztracené/duplicitní packety
- **Parsing Errors**: Robustní parsing s buffer management
- **Memory Leaks**: Správné čištění bufferů při odpojení
- **Directory Issues**: Automatické vytváření všech potřebných složek

## 0.5.1

### 🚀 New Features
- **Production Ready**: Cleaned up all debug logging for production deployment
- **Improved Startup**: Streamlined startup messages with clear status indicators
- **Enhanced Error Reporting**: Raw data logging for failed parsing attempts with IMEI identification

### 🔧 Improvements  
- **Clean Logs**: Removed verbose debug output while maintaining essential operational information
- **Startup Feedback**: Clear confirmation messages for successful server initialization
- **Performance**: Removed unnecessary test imports and debug overhead

### 🐛 Bug Fixes
- **AVL Parsing**: Fixed incorrect record count parsing (was reading wrong packet structure)
- **Packet Structure**: Corrected Teltonika AVL packet format with proper preamble handling
- **Protocol Compliance**: Improved adherence to official Teltonika AVL protocol specification

### 🧹 Code Cleanup
- **Debug Removal**: Eliminated development debug logs and test utilities
- **Optimized Build**: Removed test files from Docker image for smaller size
- **Cleaner Output**: Reduced log verbosity while maintaining error visibility

## 0.3.6

### 🐛 Bug Fixes
- **Directory Access**: Fixed persistent logging by changing from `/config/` to `/share/` directory for better Docker container compatibility
- **Mount Point**: Resolved directory creation issues in Home Assistant add-on environment

## 0.3.5

### 🐛 Bug Fixes  
- **Directory Creation**: Added detailed debug logging for config directory creation
- **Permission Testing**: Added write permission tests for `/config/teltonika_logs/`
- **Timing Fix**: Fixed global variable timing issue in directory creation

## 0.3.4

### 🐛 Bug Fixes
- **Config Directory**: Fixed timing issue where log_to_config was not set before directory creation
- **Multiple Fallbacks**: Added directory creation at multiple points (startup, first log, first IMEI)

## 0.3.3

### 🔧 Improvements
- **Simplified Web Interface**: Removed navigation tabs, showing only logs (IMEI Registry accessible via file system)
- **Cleaner UI**: Streamlined interface focused on log viewing
- **Reduced Complexity**: Removed unnecessary URL routing and navigation elements

## 0.3.2

### 🔧 Improvements
- **Startup Logs**: Cleaned up verbose debugging output in startup script
- **Log Readability**: Reduced unnecessary debug information during add-on startup

## 0.3.1

### 🐛 Bug Fixes
- **Docker Build**: Fixed missing Python modules (teltonika_protocol.py, imei_registry.py) in Docker image
- **Module Import**: Resolved ModuleNotFoundError that prevented add-on startup

## 0.3.0

### 🚀 New Features
- **Proper Teltonika AVL Protocol**: IMEI handshake authentication with correct accept/reject responses
- **Codec8 & Codec8 Extended Support**: Full AVL data parsing with GPS coordinates, speed, altitude, satellites, I/O data
- **IMEI Registry**: Automatic device tracking with connection history and statistics
- **IMEI-Based Security**: Device filtering by IMEI (replaces IP filtering for better mobile device support)
- **Persistent Logging**: Log rotation with timestamps, stored in `/config/teltonika_logs/` (survives add-on updates)
- **Enhanced Web Interface**: Dual-tab interface with Logs and IMEI Registry views
- **Custom Icon Support**: Add-on now displays custom icon in Home Assistant

### 🔧 Improvements
- **Multi-Log Support**: Web interface displays data from all log files
- **Better Protocol Compliance**: Server responses follow Teltonika specifications
- **Real-time Device Monitoring**: Track device activity and connection patterns
- **Professional Log Format**: Human-readable GPS data with IMEI identification

### 🐛 Bug Fixes
- **Web Server Stability**: Fixed BrokenPipeError when clients disconnect unexpectedly
- **Connection Handling**: Improved TCP server reliability for concurrent connections

### ⚠️ Breaking Changes
- **Configuration**: `allowed_ips` parameter changed to `allowed_imeis`
- **Security Model**: Filtering now occurs after IMEI handshake instead of IP-based blocking

## 0.2.8

- Basic updates and improvements

## 0.1.0

- First stable public release
