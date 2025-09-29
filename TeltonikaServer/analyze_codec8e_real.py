#!/usr/bin/env python3
"""
Analýza reálné Codec8E struktury podle oficiální dokumentace
"""

import json
import struct

def main():
    # Načti testovací data
    with open('test/simple_packets.json', 'r') as f:
        test_packets = json.load(f)
    
    selected_packet = test_packets[1]
    hex_data = selected_packet.get('data', '')
    binary_data = bytes.fromhex(hex_data)
    
    print("CODEC8E - OFICIÁLNÍ STRUKTURA ANALÝZA:")
    print("=" * 60)
    
    offset = 10  # Po headeru
    
    print("PRVNÍ RECORD:")
    print("-" * 30)
    
    # Timestamp (8 bytes)
    timestamp = struct.unpack('>Q', binary_data[offset:offset+8])[0]
    print(f"Timestamp: {timestamp}")
    offset += 8
    
    # Priority (1 byte) 
    priority = binary_data[offset]
    print(f"Priority: {priority}")
    offset += 1
    
    # GPS (15 bytes)
    print(f"GPS na offset {offset}")
    offset += 15
    
    # *** CODEC8E SPECIFICKÉ ***
    # IO Event ID (2 bytes místo 1)
    io_event_id = struct.unpack('>H', binary_data[offset:offset+2])[0] 
    print(f"IO Event ID (2 bytes): {io_event_id}")
    offset += 2
    
    # Total IO count (2 bytes místo 1)
    total_io = struct.unpack('>H', binary_data[offset:offset+2])[0]
    print(f"Total IO count (2 bytes): {total_io}")
    offset += 2
    
    print(f"\nIO ELEMENTY začínají na offset {offset}:")
    
    # Pro Codec8E: struktura podle velikosti hodnot
    for value_size in [1, 2, 4, 8]:
        if offset + 1 > len(binary_data):
            break
            
        # POZOR: Pro Codec8E jsou IO IDs také různých velikostí!
        # Ale count je vždy 1 byte pro každou sekci
        count = binary_data[offset]
        print(f"\n{value_size}-byte hodnoty: {count} prvků na offset {offset}")
        offset += 1
        
        for i in range(count):
            if offset + 1 + value_size > len(binary_data):
                break
                
            # Pro Codec8E může být IO ID 1, 2 nebo 4 bytes podle kontextu
            # Ale v této sekci použijeme 1 byte ID (nejběžnější)
            io_id = binary_data[offset]
            offset += 1
            
            # Hodnota podle velikosti
            if value_size == 1:
                value = binary_data[offset]
            elif value_size == 2:
                value = struct.unpack('>H', binary_data[offset:offset+2])[0]
            elif value_size == 4:
                value = struct.unpack('>I', binary_data[offset:offset+4])[0]
            elif value_size == 8:
                value = struct.unpack('>Q', binary_data[offset:offset+8])[0]
                
            print(f"  IO{io_id} = {value}")
            offset += value_size
    
    print(f"\nKonec prvního recordu na offset {offset}")
    print(f"Velikost prvního recordu: {offset - 10} bytes")
    
    # Zobraz začátek druhého recordu
    print(f"\nDRUHÝ RECORD začíná na offset {offset}:")
    if offset + 8 < len(binary_data):
        timestamp2 = struct.unpack('>Q', binary_data[offset:offset+8])[0]
        print(f"Timestamp druhého recordu: {timestamp2}")
    
    # Zobraz hex data kolem tohoto místa
    print(f"\nHex data kolem offset {offset}:")
    start = max(0, offset - 16)
    end = min(len(binary_data), offset + 32)
    for i in range(start, end, 16):
        line = binary_data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in line)
        print(f"{i:04X}: {hex_str}")

if __name__ == "__main__":
    main()