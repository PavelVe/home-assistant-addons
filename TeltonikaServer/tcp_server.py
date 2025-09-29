import socket
import threading
import os
import glob
import binascii
import struct
import pytz
from datetime import datetime, timezone, timedelta

from teltonika_protocol import parse_imei, parse_avl_packet, parse_avl_packet_with_length, format_record_for_log
from imei_registry import IMEIRegistry
from csv_logger import CSVLogger
from buffer_manager import BufferManager

def get_local_time():
    """Vrátí aktuální čas z Home Assistant timezone"""
    tz_name = os.environ.get('TZ', 'Europe/Prague')
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

def log_print(message):
    """Print s časovou značkou pro HA addon log"""
    timestamp = get_local_time()
    print(f"[{timestamp}] {message}", flush=True)

# Pro vývoj použij lokální složku, pro produkci /data
DATA_DIR = '/data' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './data'
# V HA addon prostředí použij /share/teltonika i když neexistuje (bude namountováno)
CONFIG_DIR = '/share/teltonika' if os.path.exists('/data') else './config'
LOG_FILE = os.path.join(DATA_DIR, 'tcp_data.log')

# Globální proměnné pro log rotaci, IMEI registry, CSV logger a buffer manager
current_log_file = None
log_to_config = False
imei_registry = None
csv_logger = None
buffer_manager = None

def ensure_data_dir():
    """Vytvoří data složku pokud neexistuje"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception as e:
        log_print(f"Failed to create data directory: {e}")
    
    # Vytvoř hlavní teltonika složku
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        log_print(f"Data directory ready: {CONFIG_DIR}")
    except Exception as e:
        log_print(f"Failed to create config directory: {e}")

def get_imei_registry():
    """Vrátí IMEI registry instanci"""
    global imei_registry
    if imei_registry is None:
        registry_dir = CONFIG_DIR
        # Zajistíme, že složka existuje
        os.makedirs(registry_dir, exist_ok=True)
        registry_path = os.path.join(registry_dir, 'imei_registry.json')
        imei_registry = IMEIRegistry(registry_path)
    return imei_registry

def get_csv_logger():
    """Vrátí CSV logger instanci"""
    global csv_logger
    if csv_logger is None:
        csv_logger = CSVLogger(CONFIG_DIR)
    return csv_logger

def get_buffer_manager():
    """Vrátí buffer manager instanci"""
    global buffer_manager
    if buffer_manager is None:
        buffer_manager = BufferManager(CONFIG_DIR)
    return buffer_manager

def get_log_file():
    """Vrátí cestu k aktuálnímu log souboru"""
    # Nyní používáme pouze server.log v hlavní složce
    return os.path.join(CONFIG_DIR, 'server.log')

def get_all_log_files():
    """Vrátí seznam všech log souborů seřazených podle data"""
    server_log = os.path.join(CONFIG_DIR, 'server.log')
    if os.path.exists(server_log):
        return [server_log]
    return []

def handle_client(client_socket, client_address, allowed_imeis=None):
    """Zpracuje komunikaci s jednotlivým klientem podle Teltonika AVL protokolu"""
    client_imei = None
    csv_logger = get_csv_logger()
    buffer_mgr = get_buffer_manager()
    
    csv_logger.log_server_event(f"New connection from {client_address}")
    
    with client_socket:
        while True:
            try:
                data = client_socket.recv(4096)  # Větší buffer
                if not data:
                    break
                
                # Log raw data
                hex_data = binascii.hexlify(data).decode('utf-8').upper()
                
                # Pokud máme IMEI, uložit raw data
                if client_imei:
                    csv_logger.log_raw_record(client_imei, hex_data)

                # Pokud ještě nemáme IMEI, pokus se ho parsovat
                if client_imei is None:
                    imei = parse_imei(data)
                    if imei:
                        client_imei = imei
                        client_ip = client_address[0]
                        
                        # Zkontroluj, zda je IMEI povoleno
                        registry = get_imei_registry()
                        if not registry.is_imei_allowed(client_imei, allowed_imeis or []):
                            client_socket.sendall(b"\x00")  # Reject
                            break
                        
                        # Zaregistruj IMEI v registru
                        is_new_device = registry.register_imei_connection(client_imei, client_ip)
                        
                        # Odpověz na IMEI handshake - 0x01 = accept
                        client_socket.sendall(b"\x01")
                        
                        # Zaloguj IMEI
                        status = "NEW DEVICE" if is_new_device else "KNOWN DEVICE"
                        csv_logger.log_server_event(f"IMEI {client_imei} connected from {client_address} ({status})")
                        
                        # Vytvoř device info pokud je nový
                        if is_new_device:
                            csv_logger.create_device_info(client_imei)
                        
                        continue
                    else:
                        csv_logger.log_server_event(f"Invalid IMEI handshake from {client_address}")
                        client_socket.sendall(b"\x00")  # Reject
                        break

                # Pokud máme IMEI, zpracuj data jednodušeji 
                if client_imei:
                    # Přidej data do bufferu (zachováváme buffer logiku)
                    buffer_mgr.append_data(client_imei, data)
                    
                    # Jednoduchá odpověď - ACK pro přijaté údaje
                    client_socket.sendall(b"\x00\x00\x00\x01")  # ACK pro 1 packet
                else:
                    # Nemáme ještě IMEI - čekáme na handshake
                    pass
                    
            except Exception as e:
                csv_logger.log_server_event(f"Error processing data from {client_address}: {e}")
                break
        
        # Cleanup při ukončení spojení
        if client_imei:
            csv_logger.log_server_event(f"IMEI {client_imei} disconnected from {client_address}")

def start_tcp_server(host='0.0.0.0', port=3030, allowed_imeis=None, config_logging=False):
    """Spustí TCP server pro příjem dat od Teltonika zařízení"""
    global log_to_config
    log_to_config = config_logging
    
    # Inicializuj CSV logger a buffer manager (vytvoří potřebné složky)
    csv_logger = get_csv_logger()
    buffer_mgr = get_buffer_manager()
    csv_logger.log_server_event("TCP server starting up...")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    
    log_location = CONFIG_DIR
    if allowed_imeis:
        log_print(f"TCP server listening on {host}:{port} with IMEI filter: {allowed_imeis}")
        csv_logger.log_server_event(f"Server started with IMEI filter: {allowed_imeis}")
    else:
        log_print(f"TCP server listening on {host}:{port} (all IMEIs allowed)")
        csv_logger.log_server_event("Server started - all IMEIs allowed")
    
    log_print(f"Data saved to: {log_location}")
    csv_logger.log_server_event(f"Data directory: {log_location}")

    try:
        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, allowed_imeis))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        log_print("TCP server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    ensure_data_dir()
    start_tcp_server()