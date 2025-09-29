#!/usr/bin/env python3
"""
Finální debug script pro parsování Teltonika AVL dat
Používá přesný kód z teltonika_protocol.py
"""

import json
import sys
import os

# Přidej aktuální složku do sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importuj existující parsovací funkce
from teltonika_protocol import TeltonikaParser

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
    print(f"Hex data (first 200 chars): {hex_data[:200]}...")
    
    # Převeď hex string na bytes
    binary_data = bytes.fromhex(hex_data)
    
    print("\n" + "="*80)
    print("PARSOVÁNÍ POMOCÍ TeltonikaParser:")
    print("="*80)
    
    try:
        parser = TeltonikaParser()
        
        # Použij existující parsovací funkci
        print("Parsování AVL dat...")
        records = parser.parse_avl_data(binary_data)
        
        print(f"\nÚspěšně rozparsováno {len(records)} záznamů:")
        
        for i, record in enumerate(records, 1):
            print(f"\n--- Záznam {i} ---")
            for key, value in record.items():
                if key == 'io_data' and isinstance(value, dict):
                    print(f"{key}: {len(value)} IO prvků")
                    # Zobraz prvních 5 IO prvků
                    for io_key, io_val in list(value.items())[:5]:
                        print(f"  {io_key}: {io_val}")
                    if len(value) > 5:
                        print(f"  ... a {len(value) - 5} dalších")
                else:
                    print(f"{key}: {value}")
    
    except Exception as e:
        print(f"Chyba při parsování: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()