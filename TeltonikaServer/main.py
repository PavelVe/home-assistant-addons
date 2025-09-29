#!/usr/bin/env python3
"""
Teltonika Server - hlavní entry point
Spouští jak TCP server pro přijím dat, tak webový server pro zobrazování logů
"""

import argparse
import threading
import json
import os
import pytz
from datetime import datetime, timezone, timedelta

from tcp_server import start_tcp_server, ensure_data_dir
from web_server import start_web_server

def get_local_time():
    """Vrátí aktuální čas z Home Assistant timezone"""
    tz_name = os.environ.get('TZ', 'Europe/Prague')
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

def log_print(message):
    """Print s časovou značkou pro HA addon log"""
    timestamp = get_local_time()
    print(f"[{timestamp}] {message}", flush=True)

def load_ha_config():
    """Načte konfiguraci z Home Assistant add-onu"""
    # Pro vývoj použij lokální složku, pro produkci /data
    config_path = '/data/options.json' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './data/options.json'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            log_print(f"Warning: Error reading HA config: {e}")
    return {}

def main():
    parser = argparse.ArgumentParser(description='Teltonika Server for HA Addon')
    parser.add_argument('--tcp-port', type=int, default=3030, help='TCP port to listen on')
    parser.add_argument('--web-port', type=int, default=3031, help='Web server port for logs')
    args = parser.parse_args()
    
    # Načti konfiguraci z HA add-onu
    ha_config = load_ha_config()
    
    # Použij porty z konfigurace pokud jsou dostupné
    tcp_port = ha_config.get('tcp_port', args.tcp_port)
    web_port = ha_config.get('web_port', args.web_port)
    allowed_imeis = ha_config.get('allowed_imeis', [])
    log_to_config = ha_config.get('log_to_config', False)
    
    # Pokud je seznam prázdný, žádné filtrování
    if not allowed_imeis:
        allowed_imeis = None
    
    # Nastavíme globální proměnnou před voláním ensure_data_dir
    import tcp_server
    tcp_server.log_to_config = log_to_config
    
    # Vytvoř složky
    ensure_data_dir()
    
    # Spusť TCP server v samostatném threadu
    tcp_thread = threading.Thread(target=start_tcp_server, args=('0.0.0.0', tcp_port, allowed_imeis, log_to_config))
    tcp_thread.daemon = True
    tcp_thread.start()
    
    log_print("TCP server started successfully")
    
    # Spusť web server v hlavním threadu
    log_print("Starting web server...")
    try:
        # Použij stejný CONFIG_DIR jako TCP server - musí být synchronizováno!
        # V HA addon prostředí se používá /share/teltonika
        config_dir = '/share/teltonika' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './config'
        log_print(f"Using config directory: {config_dir}")
        log_print(f"Config dir exists: {os.path.exists(config_dir)}")
        start_web_server(host='0.0.0.0', port=web_port, base_dir=config_dir)
    except KeyboardInterrupt:
        log_print("Shutting down all servers...")

if __name__ == "__main__":
    try:
        log_print("Starting Teltonika Server...")
        main()
    except Exception as e:
        log_print(f"FATAL ERROR in main(): {e}")
        import traceback
        traceback.print_exc()
        exit(1)