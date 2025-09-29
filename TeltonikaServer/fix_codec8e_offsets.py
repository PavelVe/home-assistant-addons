#!/usr/bin/env python3
"""
Analýza přesných offsetů pro Codec8E
"""

import json
import struct
import binascii

def main():
    # Načti testovací data
    with open('test/simple_packets.json', 'r') as f:
        test_packets = json.load(f)
    
    selected_packet = test_packets[1]
    hex_data = selected_packet.get('data', '')
    binary_data = bytes.fromhex(hex_data)
    
    print("DETAILNÍ ANALÝZA CODEC8E STRUKTURY:")
    print("=" * 60)
    
    # Header
    print("HEADER:")
    preamble = struct.unpack('>I', binary_data[0:4])[0]
    data_length = struct.unpack('>I', binary_data[4:8])[0]
    codec_id = binary_data[8]
    records_count = binary_data[9]
    
    print(f"0-3:   Preamble = {preamble:08X}")
    print(f"4-7:   Data length = {data_length}")
    print(f"8:     Codec ID = {codec_id:02X}")
    print(f"9:     Records count = {records_count}")
    
    print(f"\nPRVNÍ RECORD (skutečné offsety):")
    print("-" * 40)
    
    offset = 10  # Po headeru
    
    # Timestamp (8 bytes)
    timestamp = struct.unpack('>Q', binary_data[offset:offset+8])[0]
    print(f"{offset}-{offset+7}: Timestamp = {timestamp}")
    from datetime import datetime
    try:
        dt = datetime.fromtimestamp(timestamp / 1000.0)
        print(f"                    -> {dt}")
    except:
        print(f"                    -> INVALID")
    offset += 8
    
    # Priority (1 byte)
    priority = binary_data[offset]
    print(f"{offset}:     Priority = {priority}")
    offset += 1
    
    # GPS data (15 bytes)
    print(f"{offset}-{offset+14}: GPS data:")
    gps_bytes = binary_data[offset:offset+15]
    print(f"              Raw: {' '.join(f'{b:02X}' for b in gps_bytes)}")
    
    # Parsuj GPS jako signed integers
    longitude_raw = struct.unpack('>i', gps_bytes[0:4])[0]
    latitude_raw = struct.unpack('>i', gps_bytes[4:8])[0]
    altitude = struct.unpack('>H', gps_bytes[8:10])[0]
    angle = struct.unpack('>H', gps_bytes[10:12])[0]
    satellites = gps_bytes[12]
    speed = struct.unpack('>H', gps_bytes[13:15])[0]
    
    print(f"              Longitude raw: {longitude_raw} -> {longitude_raw / 10000000.0:.7f}°")
    print(f"              Latitude raw: {latitude_raw} -> {latitude_raw / 10000000.0:.7f}°")
    print(f"              Altitude: {altitude} m")
    print(f"              Angle: {angle}°")
    print(f"              Satellites: {satellites}")
    print(f"              Speed: {speed} km/h")
    
    offset += 15
    
    # IO Event ID a Total IO (pro Codec8E 2+2 bytes)
    io_event = struct.unpack('>H', binary_data[offset:offset+2])[0]
    print(f"{offset}-{offset+1}: IO Event ID = {io_event}")
    offset += 2
    
    io_total = struct.unpack('>H', binary_data[offset:offset+2])[0]
    print(f"{offset}-{offset+1}: Total IO = {io_total}")
    offset += 2
    
    print(f"\nIO DATA začíná na offset {offset}")
    print(f"Dalších 32 bytes:")
    for i in range(0, 32, 16):
        line_data = binary_data[offset+i:offset+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in line_data)
        print(f"{offset+i:04X}: {hex_str}")

if __name__ == "__main__":
    main()