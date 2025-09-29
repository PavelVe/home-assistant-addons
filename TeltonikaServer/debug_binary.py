#!/usr/bin/env python3
"""
Debug binary struktury AVL packetu
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
    
    print(f"\nHEX DUMP první 128 bytes:")
    hex_dump(binary_data, 0, 128)
    
    print(f"\nANALÝZA TELTONIKA STRUKTURY:")
    print("-" * 50)
    
    # Preamble (4 bytes)
    if len(binary_data) >= 4:
        preamble = struct.unpack('>I', binary_data[0:4])[0]
        print(f"Preamble (0-3): {preamble:08X} ({'OK' if preamble == 0 else 'CHYBA'})")
    
    # Data length (4 bytes)  
    if len(binary_data) >= 8:
        data_length = struct.unpack('>I', binary_data[4:8])[0]
        print(f"Data length (4-7): {data_length} bytes")
    
    # Codec ID (1 byte)
    if len(binary_data) >= 9:
        codec_id = binary_data[8]
        print(f"Codec ID (8): {codec_id:02X} ({'Codec8' if codec_id == 0x08 else 'Codec8E' if codec_id == 0x8E else 'Neznámý'})")
    
    # Records count (1 byte)
    if len(binary_data) >= 10:
        records_count = binary_data[9]
        print(f"Records count (9): {records_count}")
    
    # První record - začíná na pozici 10
    if len(binary_data) >= 18:
        print(f"\nPRVNÍ RECORD (offset 10):")
        
        # Timestamp (8 bytes)
        timestamp_ms = struct.unpack('>Q', binary_data[10:18])[0]
        print(f"Timestamp (10-17): {timestamp_ms} ms")
        try:
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
            print(f"  -> Datum: {dt}")
        except:
            print(f"  -> INVALID timestamp!")
        
        # Priority (1 byte)
        if len(binary_data) >= 19:
            priority = binary_data[18]
            print(f"Priority (18): {priority}")
        
        # GPS data (15 bytes: 19-33)
        if len(binary_data) >= 34:
            print(f"GPS data (19-33):")
            gps_raw = binary_data[19:34]
            print(f"  Raw bytes: {' '.join(f'{b:02X}' for b in gps_raw)}")
            
            # Parsuj GPS podle Teltonika formátu
            try:
                # Longitude (4 bytes), Latitude (4 bytes), Altitude (2 bytes), Angle (2 bytes), Satellites (1 byte), Speed (2 bytes)
                gps_data = struct.unpack('>iiHHBH', gps_raw)
                print(f"  Longitude raw: {gps_data[0]:08X} ({gps_data[0]}) -> {gps_data[0] / 10000000.0:.7f}°")
                print(f"  Latitude raw: {gps_data[1]:08X} ({gps_data[1]}) -> {gps_data[1] / 10000000.0:.7f}°")
                print(f"  Altitude: {gps_data[2]} m")
                print(f"  Angle: {gps_data[3]}°")
                print(f"  Satellites: {gps_data[4]}")
                print(f"  Speed: {gps_data[5]} km/h")
            except Exception as e:
                print(f"  CHYBA při parsování GPS: {e}")

if __name__ == "__main__":
    main()