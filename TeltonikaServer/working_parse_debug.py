#!/usr/bin/env python3
"""
FINÁLNÍ parsovací debug script
Používá přesný kód z teltonika_protocol.py
"""

import json
import sys
import os

# Přidej aktuální složku do sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importuj existující parsovací funkce
from teltonika_protocol import parse_avl_packet, format_record_for_log, get_io_description

def main():
    # Načti testovací data
    with open('test/simple_packets.json', 'r') as f:
        test_packets = json.load(f)
    
    print("Dostupné pakety:")
    for i, packet in enumerate(test_packets):
        hex_data = packet.get('data', '')
        imei = packet.get('imei', 'unknown')
        print(f"{i}: IMEI {imei}, {len(hex_data)//2} bytes, starts with {hex_data[:20]}...")
    
    # Použiju první AVL data paket (index 1) - ten velký 1024 byte
    print("\nVyberu paket #1 (velký AVL data paket - 1024 bytes):")
    selected_packet = test_packets[1]
    hex_data = selected_packet.get('data', '')
    imei = selected_packet.get('imei')
    
    print(f"IMEI: {imei}")
    print(f"Hex data length: {len(hex_data)} characters ({len(hex_data)//2} bytes)")
    print(f"Hex data (first 100 chars): {hex_data[:100]}...")
    
    # Převeď hex string na bytes
    binary_data = bytes.fromhex(hex_data)
    
    print("\n" + "="*80)
    print("PARSOVÁNÍ POMOCÍ parse_avl_packet():")
    print("="*80)
    
    try:
        # Použij existující parsovací funkci
        print("Parsování AVL dat...")
        records, records_count, codec_type = parse_avl_packet(binary_data)
        
        print(f"Codec type: {codec_type}")
        print(f"Records count: {records_count}")
        print(f"Úspěšně rozparsováno {len(records) if records else 0} záznamů:")
        
        if records:
            for i, record in enumerate(records, 1):
                print(f"\n" + "="*50)
                print(f"ZÁZNAM {i}/{len(records)}")
                print("="*50)
                
                # Základní info
                print(f"Timestamp: {record.get('timestamp', 'N/A')}")
                print(f"Priority: {record.get('priority', 'N/A')}")
                
                # GPS info z gps dictionary
                gps = record.get('gps', {})
                if gps:
                    print(f"Latitude: {gps.get('latitude', 'N/A')}")
                    print(f"Longitude: {gps.get('longitude', 'N/A')}")
                    print(f"Speed: {gps.get('speed', 'N/A')} km/h")
                    print(f"Altitude: {gps.get('altitude', 'N/A')} m")
                    print(f"Satellites: {gps.get('satellites', 'N/A')}")
                    print(f"Angle: {gps.get('angle', 'N/A')}°")
                else:
                    print("GPS data: Not available")
                
                # IO data s popisky
                io_data = record.get('io_data', {})
                if io_data:
                    print(f"\nIO ELEMENTS ({len(io_data)}):")
                    print("-" * 40)
                    
                    # Zobraz všechny IO prvky s popisky
                    for io_key, io_val in io_data.items():
                        if isinstance(io_key, str) and io_key.startswith('io'):
                            io_id = int(io_key[2:])  # Remove 'io' prefix
                            description = get_io_description(io_id)
                            if description != f"IO Element {io_id}":  # Má popis
                                print(f"  {io_key} = {io_val} ({description})")
                            else:
                                print(f"  {io_key} = {io_val}")
                        elif isinstance(io_key, int):
                            # IO key je přímo číslo
                            description = get_io_description(io_key)
                            if description != f"IO Element {io_key}":  # Má popis
                                print(f"  io{io_key} = {io_val} ({description})")
                            else:
                                print(f"  io{io_key} = {io_val}")
                        else:
                            print(f"  {io_key} = {io_val}")
                
                # Zobraz naformátovaný log záznam
                print(f"\nFORMÁTOVANÝ LOG:")
                print("-" * 40)
                formatted_log = format_record_for_log(record, imei)
                print(formatted_log)
                
        else:
            print("Žádné záznamy nebyly nalezeny nebo chyba při parsování.")
    
    except Exception as e:
        print(f"Chyba při parsování: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()