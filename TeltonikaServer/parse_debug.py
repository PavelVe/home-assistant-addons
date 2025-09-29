#!/usr/bin/env python3
"""
Debug parsování pomocí existujícího kódu z tcp_server.py
"""

import json
import sys
import os

# Přidej aktuální složku do sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importuj existující parsovací funkce
from tcp_server import parse_teltonika_avl
from csv_logger import CSVLogger

def main():
    # Načti testovací data
    with open('test/simple_packets.json', 'r') as f:
        test_packets = json.load(f)
    
    print("Dostupné pakety:")
    for i, packet in enumerate(test_packets):
        hex_data = packet.get('data', '')
        imei = packet.get('imei', 'unknown')
        print(f"{i}: IMEI {imei}, {len(hex_data)//2} bytes, starts with {hex_data[:20]}...")
    
    # Použiju první AVL data paket (index 1)
    print("\nVyberu paket #1 (první AVL data paket):")
    selected_packet = test_packets[1]
    hex_data = selected_packet.get('data', '')
    imei = selected_packet.get('imei')
    
    print(f"IMEI: {imei}")
    print(f"Hex data length: {len(hex_data)} characters ({len(hex_data)//2} bytes)")
    print(f"Hex data (first 100 chars): {hex_data[:100]}...")
    
    # Převeď hex string na bytes
    binary_data = bytes.fromhex(hex_data)
    
    print("\n" + "="*80)
    print("PARSOVÁNÍ POMOCÍ EXISTUJÍCÍHO KÓDU:")
    print("="*80)
    
    try:
        # Použij existující parsovací funkci
        print("Parsování AVL dat...")
        records = parse_teltonika_avl(binary_data, imei)
        
        print(f"\nÚspěšně rozparsováno {len(records)} záznamů:")
        
        for i, record in enumerate(records, 1):
            print(f"\n--- Záznam {i} ---")
            print(f"Timestamp: {record.get('timestamp', 'N/A')}")
            print(f"Latitude: {record.get('latitude', 'N/A')}")
            print(f"Longitude: {record.get('longitude', 'N/A')}")
            print(f"Speed: {record.get('speed', 'N/A')} km/h")
            print(f"Altitude: {record.get('altitude', 'N/A')} m")
            print(f"Satellites: {record.get('satellites', 'N/A')}")
            print(f"Angle: {record.get('angle', 'N/A')}°")
            
            # Zobraz IO data
            io_data = record.get('io_data', {})
            if io_data:
                print(f"IO elements ({len(io_data)}):")
                for key, value in list(io_data.items())[:10]:  # První 10
                    print(f"  {key}: {value}")
                if len(io_data) > 10:
                    print(f"  ... a {len(io_data) - 10} dalších")
    
    except Exception as e:
        print(f"Chyba při parsování: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()