#!/usr/bin/env python3
"""Buffer Manager for TCP packet fragmentation handling"""

import os
import struct
from typing import Optional, List, Tuple


class BufferManager:
    def __init__(self, base_dir='/share/teltonika'):
        self.base_dir = base_dir
        self.devices_dir = os.path.join(base_dir, 'devices')
        
        # Vytvoř složku pro zařízení
        os.makedirs(self.devices_dir, exist_ok=True)
    
    def _get_buffer_file(self, imei: str) -> str:
        """Vrátí cestu k buffer souboru pro dané IMEI"""
        device_dir = os.path.join(self.devices_dir, imei)
        os.makedirs(device_dir, exist_ok=True)
        return os.path.join(device_dir, 'buffer.tmp')
    
    def append_data(self, imei: str, data: bytes):
        """Připojí nová data do bufferu pro dané IMEI"""
        buffer_file = self._get_buffer_file(imei)
        
        with open(buffer_file, 'ab') as f:
            f.write(data)
    
    def get_complete_packets(self, imei: str) -> Tuple[List[bytes], bytes]:
        """
        Vrátí seznam kompletních AVL paketů a zbývající neúplná data
        Returns: (complete_packets, remaining_data)
        """
        buffer_file = self._get_buffer_file(imei)
        
        if not os.path.exists(buffer_file):
            return [], b''
        
        # Načti všechna data z bufferu
        with open(buffer_file, 'rb') as f:
            buffer_data = f.read()
        
        if len(buffer_data) == 0:
            return [], b''
        
        complete_packets = []
        offset = 0
        
        while offset < len(buffer_data):
            # Zkontroluj jestli máme dostatek dat pro header (8 bytes)
            if offset + 8 > len(buffer_data):
                # Nedostatek dat pro header
                remaining = buffer_data[offset:]
                break
            
            # Kontrola preamble (4 nulové bytes)
            preamble = buffer_data[offset:offset+4]
            if preamble != b'\x00\x00\x00\x00':
                # Hledej začátek dalšího packetu
                found = False
                for i in range(offset + 1, len(buffer_data) - 3):
                    if buffer_data[i:i+4] == b'\x00\x00\x00\x00':
                        offset = i
                        found = True
                        break
                if not found:
                    # Žádný validní packet nenalezen
                    remaining = b''
                    break
                continue
            
            # Načti délku dat
            try:
                data_length = struct.unpack('>I', buffer_data[offset+4:offset+8])[0]
            except:
                # Chyba při čtení délky
                offset += 4
                continue
            
            # Validace délky
            if data_length < 4 or data_length > 100000:
                # Nevalidní délka, posuň se
                offset += 4
                continue
            
            # Celková délka packetu: preamble(4) + length(4) + data + CRC(4)
            total_packet_length = 8 + data_length + 4
            
            # Zkontroluj jestli máme kompletní packet
            if offset + total_packet_length > len(buffer_data):
                # Neúplný packet
                remaining = buffer_data[offset:]
                break
            
            # Extrahuj kompletní packet
            packet = buffer_data[offset:offset + total_packet_length]
            complete_packets.append(packet)
            offset += total_packet_length
        else:
            # Všechna data byla zpracována
            remaining = b''
        
        # Přepiš buffer soubor se zbývajícími daty
        if remaining:
            with open(buffer_file, 'wb') as f:
                f.write(remaining)
        else:
            # Smaž prázdný buffer
            try:
                os.remove(buffer_file)
            except:
                pass
        
        return complete_packets, remaining
    
    def clear_buffer(self, imei: str):
        """Vyčistí buffer pro dané IMEI"""
        buffer_file = self._get_buffer_file(imei)
        try:
            os.remove(buffer_file)
        except:
            pass
    
    def get_buffer_size(self, imei: str) -> int:
        """Vrátí velikost bufferu pro dané IMEI v bytech"""
        buffer_file = self._get_buffer_file(imei)
        try:
            return os.path.getsize(buffer_file)
        except:
            return 0
    
    def get_all_buffered_imeis(self) -> List[str]:
        """Vrátí seznam všech IMEI s aktivními buffery"""
        imeis = []
        try:
            if os.path.exists(self.devices_dir):
                for dirname in os.listdir(self.devices_dir):
                    device_dir = os.path.join(self.devices_dir, dirname)
                    if os.path.isdir(device_dir):
                        buffer_file = os.path.join(device_dir, 'buffer.tmp')
                        if os.path.exists(buffer_file) and os.path.getsize(buffer_file) > 0:
                            imeis.append(dirname)
        except:
            pass
        return sorted(imeis)
    
    def cleanup_old_buffers(self, max_size_mb=10):
        """Smaže buffery větší než max_size_mb MB (ochrana proti zahlcení)"""
        max_size_bytes = max_size_mb * 1024 * 1024
        
        for imei in self.get_all_buffered_imeis():
            if self.get_buffer_size(imei) > max_size_bytes:
                print(f"⚠️ Buffer pro IMEI {imei} je příliš velký ({self.get_buffer_size(imei)} bytes), mažu...")
                self.clear_buffer(imei)