#!/usr/bin/env python3
"""
Debug Codec8 Extended struktura
Codec8E má jiné IO elementy s variable-length ID
"""

import json
import struct
import binascii

def hex_dump(data, start=0, length=64):
    """Zobraz hex dump s offsety"""
    for i in range(0, min(length, len(data) - start), 16):
        offset = start + i
        hex_part = ' '.join(f"{data[offset+j]:02X}" if offset+j < len(data) else "  " for j in range(16))
        ascii_part = ''.join(chr(data[offset+j]) if 32 <= data[offset+j] <= 126 else '.' 
                           for j in range(16) if offset+j < len(data))
        print(f"{offset:04X}: {hex_part:<48} |{ascii_part}|")

def parse_codec8e_record(data, offset):
    """Parse single Codec8E record"""
    print(f"\n=== PARSOVÁNÍ RECORD NA OFFSET {offset} ===")
    
    if offset + 34 > len(data):
        print(f"Nedostatek dat pro record na offset {offset}")
        return None, offset
    
    start_offset = offset
    
    # Timestamp (8 bytes)
    timestamp_ms = struct.unpack('>Q', data[offset:offset+8])[0]
    print(f"Timestamp: {timestamp_ms} ms")
    try:
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
        print(f"  -> Datum: {dt}")
    except:
        print(f"  -> INVALID timestamp!")
    offset += 8
    
    # Priority (1 byte)
    priority = struct.unpack('>B', data[offset:offset+1])[0]
    print(f"Priority: {priority}")
    offset += 1
    
    # GPS Data (15 bytes)
    print(f"GPS data ({offset}-{offset+14}):")
    gps_data = struct.unpack('>iiHHBH', data[offset:offset+15])
    print(f"  Longitude: {gps_data[0]} -> {gps_data[0] / 10000000.0:.7f}°")
    print(f"  Latitude: {gps_data[1]} -> {gps_data[1] / 10000000.0:.7f}°")
    print(f"  Altitude: {gps_data[2]} m")
    print(f"  Angle: {gps_data[3]}°")
    print(f"  Satellites: {gps_data[4]}")
    print(f"  Speed: {gps_data[5]} km/h")
    offset += 15
    
    # IO Event ID (2 bytes pro Codec8E!)
    io_event_id = struct.unpack('>H', data[offset:offset+2])[0]
    print(f"IO Event ID: {io_event_id}")
    offset += 2
    
    # Total IO elements (2 bytes pro Codec8E!)
    io_total = struct.unpack('>H', data[offset:offset+2])[0]
    print(f"Total IO elements: {io_total}")
    offset += 2
    
    # Pro Codec8E - IO struktura je složitější
    print(f"IO data struktura začíná na offset {offset}")
    
    # Zobraz zbytek jako hex pro analýzu
    remaining_data = data[offset:offset+100]
    print(f"Dalších 100 bytes od offset {offset}:")
    hex_dump(remaining_data, 0, 100)
    
    # Vrat nějaký rozumný offset (přeskočíme zbytek tohoto recordu)
    # Pro debugging přeskočíme 200 bytes
    new_offset = start_offset + 200
    return {"timestamp": timestamp_ms, "priority": priority, "gps": gps_data}, new_offset

def main():
    # Načti testovací data
    with open('test/simple_packets.json', 'r') as f:
        test_packets = json.load(f)
    
    # Vyberu paket #1
    selected_packet = test_packets[1]
    hex_data = selected_packet.get('data', '')
    imei = selected_packet.get('imei')
    
    print(f"IMEI: {imei}")
    print(f"Hex data length: {len(hex_data)} characters ({len(hex_data)//2} bytes)")
    
    # Převeď hex string na bytes
    binary_data = bytes.fromhex(hex_data)
    
    print(f"\nTELTONIKA CODEC8E ANALÝZA:")
    print("-" * 50)
    
    # Header analýza
    preamble = struct.unpack('>I', binary_data[0:4])[0]
    data_length = struct.unpack('>I', binary_data[4:8])[0]
    codec_id = binary_data[8]
    records_count = binary_data[9]
    
    print(f"Preamble: {preamble:08X}")
    print(f"Data length: {data_length} bytes")
    print(f"Codec ID: {codec_id:02X} ({'Codec8E' if codec_id == 0x8E else 'Jiný'})")
    print(f"Records count: {records_count}")
    
    # Parsuj první 3 recordy pro debugging
    offset = 10  # Po headeru
    
    for i in range(min(3, records_count)):
        record, new_offset = parse_codec8e_record(binary_data, offset)
        if record is None:
            break
        offset = new_offset

if __name__ == "__main__":
    main()