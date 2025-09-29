#!/usr/bin/env python3
"""CSV Logger for Teltonika GPS data"""

import csv
import os
from datetime import datetime
from collections import deque
import pytz


class CSVLogger:
    def __init__(self, base_dir='/share/teltonika'):
        self.base_dir = base_dir
        self.devices_dir = os.path.join(base_dir, 'devices')
        self.server_log = os.path.join(base_dir, 'server.log')
        self.csv_headers = ['timestamp', 'raw_data']
        
        # Nastavení časové zóny - zkus HA timezone, pak lokální
        self.timezone = self._get_timezone()
        
        # Vytvoř základní strukturu
        os.makedirs(self.devices_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.server_log), exist_ok=True)
    
    def _get_timezone(self):
        """Získej časovou zónu z HA prostředí"""
        tz_name = os.environ.get('TZ', 'Europe/Prague')
        return pytz.timezone(tz_name)
    
    def _get_local_time(self):
        """Vrátí aktuální čas v správné časové zóně"""
        if self.timezone:
            return datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def log_server_event(self, message):
        """Zaloguje událost do hlavního server logu"""
        timestamp = self._get_local_time()
        with open(self.server_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def log_raw_data(self, client_address, imei, hex_data):
        """Zaloguje RAW hex data do server logu"""
        # Ořež hex data pokud jsou moc dlouhá (zobrazí prvních 200 znaků)
        if len(hex_data) > 200:
            hex_data = hex_data[:200] + '...'
        
        message = f"RAW DATA from {client_address} (IMEI: {imei or 'unknown'}): {hex_data}"
        self.log_server_event(message)
    
    def log_raw_record(self, imei, hex_data):
        """Zaloguje RAW hex záznam do CSV souboru zařízení"""
        device_dir = os.path.join(self.devices_dir, imei)
        os.makedirs(device_dir, exist_ok=True)
        
        csv_file = os.path.join(device_dir, 'data.csv')
        
        # Zkontroluj jestli soubor existuje
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Přidej hlavičku pro nový soubor
            if not file_exists:
                writer.writerow(self.csv_headers)
            
            # Vytvoř timestamp
            timestamp = self._get_local_time()
            
            # Vytvoř CSV řádek - jen čas a raw data
            row = [timestamp, hex_data]
            writer.writerow(row)
    
    def read_last_records(self, imei, count=2000):
        """Načte posledních N záznamů z CSV"""
        csv_file = os.path.join(self.devices_dir, imei, 'data.csv')
        
        if not os.path.exists(csv_file):
            return []
        
        # Použij deque pro efektivní držení posledních N řádků
        last_records = deque(maxlen=count)
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    last_records.append(row)
        except Exception as e:
            print(f"Error reading CSV for {imei}: {e}")
            return []
        
        return list(last_records)
    
    def get_all_devices(self):
        """Vrátí seznam všech IMEI zařízení"""
        devices = []
        try:
            if os.path.exists(self.devices_dir):
                for dirname in os.listdir(self.devices_dir):
                    device_dir = os.path.join(self.devices_dir, dirname)
                    if os.path.isdir(device_dir) and dirname.isdigit():
                        # Zkontroluj jestli má CSV soubor
                        csv_file = os.path.join(device_dir, 'data.csv')
                        if os.path.exists(csv_file):
                            devices.append({
                                'imei': dirname,
                                'last_seen': self._get_last_seen(dirname),
                                'record_count': self._get_record_count(dirname)
                            })
        except Exception as e:
            print(f"Error getting devices: {e}")
        
        return sorted(devices, key=lambda x: x['imei'])
    
    def _get_last_seen(self, imei):
        """Získej čas posledního záznamu"""
        try:
            records = self.read_last_records(imei, 1)
            if records:
                return records[-1]['timestamp']
        except:
            pass
        return "Unknown"
    
    def _get_record_count(self, imei):
        """Spočítej celkový počet záznamů"""
        csv_file = os.path.join(self.devices_dir, imei, 'data.csv')
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Počítej řádky kromě hlavičky
                return sum(1 for line in f) - 1
        except:
            return 0
    
    def get_server_log_tail(self, lines=2000):
        """Načte posledních N řádků server logu"""
        if not os.path.exists(self.server_log):
            return "No server log available"
        
        try:
            with open(self.server_log, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                # Posledních N řádků
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
        except Exception as e:
            return f"Error reading server log: {e}"
    
    def create_device_info(self, imei):
        """Vytvoří info.json pro zařízení"""
        device_dir = os.path.join(self.devices_dir, imei)
        os.makedirs(device_dir, exist_ok=True)
        
        info_file = os.path.join(device_dir, 'info.json')
        if not os.path.exists(info_file):
            info = {
                'imei': imei,
                'first_seen': datetime.now().isoformat(),
                'device_name': f"Device {imei}",
                'notes': ""
            }
            
            import json
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2)