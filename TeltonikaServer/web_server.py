#!/usr/bin/env python3
"""Web Server pro Teltonika GPS data s tabulkovým zobrazením CSV dat"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from csv_logger import CSVLogger
from buffer_manager import BufferManager

class TeltonikaWebHandler(BaseHTTPRequestHandler):
    # base_dir bude nastaven při vytvoření instance

    def do_GET(self):
        """Zpracuje GET požadavky"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Debug logging
        print(f"[DEBUG] Web server request: {self.path} from {self.client_address[0]}")
        print(f"[DEBUG] Parsed path: {path}")
        print(f"[DEBUG] Base dir: {getattr(self, 'base_dir', 'NOT SET')}")
        
        # Ingress detection and debugging
        headers = dict(self.headers)
        print(f"[DEBUG] All request headers: {headers}")
        
        # Check for Ingress-specific headers
        ingress_headers = ['x-ingress-path', 'x-forwarded-for', 'x-forwarded-proto', 'x-forwarded-host']
        is_ingress = False
        for header in ingress_headers:
            if header in headers:
                print(f"[DEBUG] Ingress header found: {header} = {headers[header]}")
                is_ingress = True
        
        if is_ingress:
            print(f"[DEBUG] INGRESS DETECTED - Request likely from Home Assistant Ingress")
        else:
            print(f"[DEBUG] DIRECT ACCESS - Request likely from direct IP access")
        
        try:
            if path == '/' or path == '/index.html':
                self._serve_main_page()
            elif path == '/api/devices':
                self._serve_devices_api()
            elif path == '/api/device_data':
                query = parse_qs(parsed_url.query)
                imei = query.get('imei', [None])[0]
                limit = int(query.get('limit', [2000])[0])
                self._serve_device_data_api(imei, limit)
            elif path == '/api/server_log':
                limit = int(parse_qs(parsed_url.query).get('limit', [2000])[0])
                self._serve_server_log_api(limit)
            elif path == '/api/download_csv':
                query = parse_qs(parsed_url.query)
                imei = query.get('imei', [None])[0]
                self._serve_csv_download(imei)
            else:
                print(f"[DEBUG] 404 - Path not found: {path}")
                self._serve_404()
        except Exception as e:
            print(f"[ERROR] Web server error in {path}: {e}")
            import traceback
            traceback.print_exc()
            self._serve_error(str(e))

    def _serve_main_page(self):
        """Služí hlavní HTML stránku s taby"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Teltonika GPS Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .tabs { display: flex; margin-bottom: 10px; }
        .tab { 
            padding: 10px 20px; 
            border: 1px solid #ccc; 
            background: #f0f0f0; 
            cursor: pointer; 
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }
        .tab.active { background: #007cba; color: white; }
        .tab-content { 
            border: 1px solid #ccc; 
            padding: 20px; 
            border-radius: 0 5px 5px 5px;
        }
        .device-list { margin-bottom: 20px; }
        .device-item { 
            display: inline-block; 
            margin: 5px; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px;
            cursor: pointer;
            background: #f9f9f9;
        }
        .device-item:hover { background: #e0e0e0; }
        .device-item.selected { background: #007cba; color: white; }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            font-size: 12px;
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 8px; 
            text-align: left; 
        }
        th { background-color: #f2f2f2; position: sticky; top: 0; }
        .log-container { 
            font-family: monospace; 
            background: #f5f5f5; 
            padding: 10px;
            border-radius: 5px;
        }
        .refresh-btn { 
            padding: 10px 20px; 
            background: #007cba; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer;
            margin-bottom: 20px;
        }
        .download-btn {
            display: inline-block;
            padding: 8px 16px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 14px;
            transition: background 0.3s;
        }
        .download-btn:hover {
            background: #218838;
            color: white;
            text-decoration: none;
        }
        .status-info { 
            background: #e8f4fd; 
            padding: 10px; 
            border-radius: 5px; 
            margin-bottom: 20px;
        }
        .coordinates { color: #2e8b57; font-weight: bold; }
        .speed { color: #ff6347; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🛰️ Teltonika GPS Server</h1>
    
    <div class="tabs">
        <div class="tab active" onclick="showTab('overview', this)">Přehled</div>
        <div class="tab" onclick="showTab('devices', this)">Zařízení</div>
        <div class="tab" onclick="showTab('server-log', this)">Server Log</div>
    </div>
    
    <div id="overview" class="tab-content">
        <h2>Přehled systému</h2>
        <div class="status-info">
            <p><strong>Server:</strong> Běží a přijímá data od Teltonika zařízení</p>
            <p><strong>Protokol:</strong> AVL Codec8/8E s IMEI autentifikací</p>
            <p><strong>Úložiště:</strong> CSV soubory pro každé zařízení + server log</p>
        </div>
        <div id="devices-overview"></div>
    </div>
    
    <div id="devices" class="tab-content" style="display: none;">
        <h2>GPS Data zařízení</h2>
        <div class="device-list" id="device-list"></div>
        <div id="device-data">
            <p>Vyberte zařízení pro zobrazení GPS dat...</p>
        </div>
    </div>
    
    <div id="server-log" class="tab-content" style="display: none;">
        <h2>Server Log</h2>
        <div class="log-container" id="server-log-content">Načítá se...</div>
    </div>
    

    <script>
        console.log('Script starting...');
        
        let currentDevice = null;
        let refreshInterval = null;
        
        function showTab(tabName, element) {
            console.log('showTab called with:', tabName, element);
            // Skryj všechny taby
            document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            
            // Zobraz vybraný tab
            document.getElementById(tabName).style.display = 'block';
            if (element) element.classList.add('active');
            
            // Zastavit automatické obnovování
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
            
            // Načti data podle tabu
            if (tabName === 'overview') {
                loadOverview();
            } else if (tabName === 'devices') {
                loadDevices();
            } else if (tabName === 'server-log') {
                loadServerLog();
                // Automatické obnovování server logu
                refreshInterval = setInterval(loadServerLog, 5000);
            }
        }
        
        async function loadOverview() {
            console.log('loadOverview called');
            try {
                console.log('Fetching devices from api/devices');
                const response = await fetch('api/devices');
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const responseText = await response.text();
                console.log('Raw response:', responseText);
                
                const devices = JSON.parse(responseText);
                
                let html = '<h3>Registrovaná zařízení (' + devices.length + ')</h3>';
                if (devices.length === 0) {
                    html += '<p>Zatím se nepřipojila žádná zařízení.</p>';
                } else {
                    html += '<table><tr><th>IMEI</th><th>Název</th><th>Poslední záznam</th><th>Počet záznamů</th></tr>';
                    devices.forEach(device => {
                        html += `<tr>
                            <td>$${device.imei}</td>
                            <td>Device $${device.imei}</td>
                            <td>$${device.last_seen}</td>
                            <td>$${device.record_count}</td>
                        </tr>`;
                    });
                    html += '</table>';
                }
                
                document.getElementById('devices-overview').innerHTML = html;
            } catch (error) {
                console.error('Error in loadOverview:', error);
                let errorMsg = 'Unknown error';
                if (error.message) {
                    errorMsg = error.message;
                } else if (error.toString) {
                    errorMsg = error.toString();
                }
                document.getElementById('devices-overview').innerHTML = '<p>Chyba při načítání: ' + errorMsg + '</p>';
            }
        }
        
        async function loadDevices() {
            console.log('loadDevices called');
            try {
                console.log('Fetching devices from api/devices');
                const response = await fetch('api/devices');
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const responseText = await response.text();
                console.log('Raw response:', responseText.substring(0, 200) + '...');
                
                const devices = JSON.parse(responseText);
                
                let html = '';
                devices.forEach(device => {
                    const isSelected = currentDevice === device.imei ? 'selected' : '';
                    html += `<div class="device-item $${isSelected}" onclick="selectDevice('$${device.imei}')">
                        <strong>$${device.imei}</strong><br>
                        <small>Záznamů: $${device.record_count}</small><br>
                        <small>Naposledy: $${device.last_seen}</small>
                    </div>`;
                });
                
                document.getElementById('device-list').innerHTML = html;
                
                // Pokud máme vybrané zařízení, načti jeho data
                if (currentDevice) {
                    loadDeviceData(currentDevice);
                }
            } catch (error) {
                console.error('Error in loadDevices:', error);
                let errorMsg = 'Unknown error';
                if (error.message) {
                    errorMsg = error.message;
                } else if (error.toString) {
                    errorMsg = error.toString();
                }
                document.getElementById('device-list').innerHTML = '<p>Chyba při načítání zařízení: ' + errorMsg + '</p>';
            }
        }
        
        function selectDevice(imei) {
            currentDevice = imei;
            loadDevices(); // Obnoví seznam s označeným zařízením
            loadDeviceData(imei);
        }
        
        async function loadDeviceData(imei) {
            console.log('loadDeviceData called for IMEI:', imei);
            try {
                const url = `api/device_data?imei=${imei}&limit=100`;
                console.log('Fetching device data from:', url);
                const response = await fetch(url);
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const responseText = await response.text();
                console.log('Raw response length:', responseText.length);
                
                const records = JSON.parse(responseText);
                
                if (records.length === 0) {
                    document.getElementById('device-data').innerHTML = '<p>Žádná GPS data pro toto zařízení.</p>';
                    return;
                }
                
                let html = `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3>GPS Data pro zařízení $${imei} (posledních $${records.length} záznamů)</h3>
                    <a href="api/download_csv?imei=$${imei}" class="download-btn">📥 Stáhnout CSV</a>
                </div>`;
                html += '<table><tr>';
                html += '<th>Čas</th><th>Souřadnice</th><th>Rychlost</th><th>Výška</th><th>Satelity</th><th>Směr</th><th>I/O Data</th>';
                html += '</tr>';
                
                records.forEach(record => {
                    const coords = `$${parseFloat(record.latitude).toFixed(6)}, $${parseFloat(record.longitude).toFixed(6)}`;
                    html += `<tr>
                        <td>$${record.timestamp}</td>
                        <td class="coordinates">$${coords}</td>
                        <td class="speed">$${record.speed} km/h</td>
                        <td>$${record.altitude} m</td>
                        <td>$${record.satellites}</td>
                        <td>$${record.angle}°</td>
                        <td><small>$${record.io_data}</small></td>
                    </tr>`;
                });
                
                html += '</table>';
                document.getElementById('device-data').innerHTML = html;
            } catch (error) {
                console.error('Error in loadDeviceData:', error);
                let errorMsg = 'Unknown error';
                if (error.message) {
                    errorMsg = error.message;
                } else if (error.toString) {
                    errorMsg = error.toString();
                }
                document.getElementById('device-data').innerHTML = '<p>Chyba při načítání dat zařízení: ' + errorMsg + '</p>';
            }
        }
        
        async function loadServerLog() {
            console.log('loadServerLog called');
            try {
                console.log('Fetching server log from api/server_log');
                const response = await fetch('api/server_log?limit=100');
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const text = await response.text();
                console.log('Server log response length:', text.length);
                
                document.getElementById('server-log-content').innerHTML = text.replace(/\\n/g, '<br>');
                
                // Scroll na konec
                const container = document.getElementById('server-log-content');
                container.scrollTop = container.scrollHeight;
            } catch (error) {
                console.error('Error in loadServerLog:', error);
                let errorMsg = 'Unknown error';
                if (error.message) {
                    errorMsg = error.message;
                } else if (error.toString) {
                    errorMsg = error.toString();
                }
                document.getElementById('server-log-content').innerHTML = 'Chyba při načítání server logu: ' + errorMsg;
            }
        }
        
        
        // Načti přehled při načtení stránky
        window.onload = function() {
            console.log('Page loaded, calling loadOverview...');
            loadOverview();
        };
        
        // Zastavit interval při zavření stránky
        window.onbeforeunload = function() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        };
        
        console.log('Script completed. showTab function:', typeof showTab);
    </script>
</body>
</html>"""
        
        # Nahradíme $$ za $ v JavaScript template literals (jen pro HTML)
        html = html.replace('$${', '${')
        self._send_response(200, html, 'text/html')

    def _serve_devices_api(self):
        """API endpoint pro seznam zařízení"""
        print(f"[DEBUG] _serve_devices_api called with base_dir: {self.base_dir}")
        try:
            # Ověř, že base_dir existuje
            if not os.path.exists(self.base_dir):
                print(f"[ERROR] Base directory does not exist: {self.base_dir}")
                self._send_json_response({"error": f"Base directory not found: {self.base_dir}"}, status=500)
                return
                
            csv_logger = CSVLogger(self.base_dir)
            devices = csv_logger.get_all_devices()
            print(f"[DEBUG] Found {len(devices)} devices")
            self._send_json_response(devices)
        except Exception as e:
            print(f"[ERROR] Error in _serve_devices_api: {e}")
            import traceback
            traceback.print_exc()
            self._send_json_response({"error": f"API Error: {str(e)}"}, status=500)

    def _serve_device_data_api(self, imei, limit):
        """API endpoint pro data konkrétního zařízení"""
        print(f"[DEBUG] _serve_device_data_api called: imei={imei}, limit={limit}")
        if not imei:
            print(f"[ERROR] Missing IMEI parameter")
            self._send_json_response({"error": "IMEI parameter required"}, status=400)
            return
        
        
        try:
            if not os.path.exists(self.base_dir):
                print(f"[ERROR] Base directory does not exist: {self.base_dir}")
                self._send_json_response({"error": f"Base directory not found: {self.base_dir}"}, status=500)
                return
                
            csv_logger = CSVLogger(self.base_dir)
            records = csv_logger.read_last_records(imei, limit)
            print(f"[DEBUG] Found {len(records)} records for IMEI {imei}")
            self._send_json_response(records)
        except Exception as e:
            print(f"[ERROR] Error in _serve_device_data_api: {e}")
            import traceback
            traceback.print_exc()
            self._send_json_response({"error": f"API Error: {str(e)}"}, status=500)

    def _serve_server_log_api(self, limit):
        """API endpoint pro server log"""
        print(f"[DEBUG] _serve_server_log_api called: limit={limit}")
        try:
            if not os.path.exists(self.base_dir):
                print(f"[ERROR] Base directory does not exist: {self.base_dir}")
                self._send_response(500, f"Base directory not found: {self.base_dir}", 'text/plain')
                return
                
            csv_logger = CSVLogger(self.base_dir)
            log_content = csv_logger.get_server_log_tail(limit)
            print(f"[DEBUG] Retrieved log content, length: {len(log_content)}")
            self._send_response(200, log_content, 'text/plain')
        except Exception as e:
            print(f"[ERROR] Error in _serve_server_log_api: {e}")
            import traceback
            traceback.print_exc()
            self._send_response(500, f"Server log API Error: {e}", 'text/plain')

    def _serve_csv_download(self, imei):
        """API endpoint pro stažení CSV souboru zařízení"""
        if not imei:
            self._send_response(400, "Missing IMEI parameter", 'text/plain')
            return
        
            
        try:
            import os
            from datetime import datetime
            
            # Cesta k CSV souboru
            csv_file = os.path.join(self.base_dir, 'devices', imei, 'data.csv')
            
            if not os.path.exists(csv_file):
                self._send_response(404, f"CSV file not found for IMEI {imei}", 'text/plain')
                return
            
            # Načti CSV content
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            # Generuj filename s datem
            today = datetime.now().strftime('%Y-%m-%d')
            filename = f"teltonika_{imei}_{today}.csv"
            
            # Pošli jako stažený soubor
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(csv_content.encode('utf-8'))
            
        except Exception as e:
            self._send_response(500, f"Error downloading CSV: {e}", 'text/plain')


    def _send_response(self, status_code, content, content_type):
        """Pošle HTTP odpověď"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _send_json_response(self, data, status=200):
        """Pošle JSON odpověď"""
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self._send_response(status, json_data, 'application/json')

    def _serve_404(self):
        """404 Not Found"""
        self._send_response(404, "404 - Page Not Found", 'text/plain')

    def _serve_error(self, error_msg):
        """500 Internal Server Error"""
        self._send_response(500, f"Internal Server Error: {error_msg}", 'text/plain')

    def log_message(self, format, *args):
        """Potlač výchozí HTTP server logy"""
        pass

def start_web_server(host='0.0.0.0', port=3031, base_dir=None):
    """Spustí web server"""
    
    # Pokud není base_dir specifikováno, použij stejnou logiku jako main.py
    if base_dir is None:
        base_dir = '/share/teltonika' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './config'
    
    print(f"[DEBUG] Starting web server with base_dir: {base_dir}")
    print(f"[DEBUG] Base dir exists: {os.path.exists(base_dir)}")
    print(f"[DEBUG] /data exists: {os.path.exists('/data')}")
    print(f"[DEBUG] HA_ADDON env var: {os.environ.get('HA_ADDON', 'Not set')}")
    
    # Vytvoř base_dir pokud neexistuje
    if not os.path.exists(base_dir):
        print(f"[DEBUG] Creating base directory: {base_dir}")
        os.makedirs(base_dir, exist_ok=True)
    
    # Vytvoříme handler s nastaveným base_dir
    class ConfiguredHandler(TeltonikaWebHandler):
        def __init__(self, *args, **kwargs):
            self.base_dir = base_dir
            super().__init__(*args, **kwargs)
    
    server = HTTPServer((host, port), ConfiguredHandler)
    print(f"[INFO] Web server listening on http://{host}:{port}")
    print(f"[INFO] Using base directory: {base_dir}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Web server shutting down...")
    finally:
        server.server_close()

if __name__ == "__main__":
    start_web_server()