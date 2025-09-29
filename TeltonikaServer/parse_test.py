#!/usr/bin/env python3
"""
Test parsování Teltonika AVL dat
Vezme jeden paket z simple_packets.json a rozparsuje ho pomocí existujícího parsovacího kódu
"""

import json
import struct
from datetime import datetime

def parse_avl_data(data):
    """Parsuje AVL data podle Teltonika protokolu"""
    print(f"Raw hex data ({len(data)} bytes): {data.hex().upper()}")
    print("=" * 80)
    
    offset = 0
    
    # Přeskoč první 4 bajty (preamble)
    preamble = struct.unpack('>I', data[offset:offset+4])[0]
    print(f"Preamble: {preamble:08X}")
    offset += 4
    
    # Data Length
    data_length = struct.unpack('>I', data[offset:offset+4])[0]
    print(f"Data Length: {data_length} bytes")
    offset += 4
    
    # Codec ID
    codec_id = data[offset]
    print(f"Codec ID: {codec_id} ({hex(codec_id)})")
    offset += 1
    
    # Number of records
    num_records = data[offset]
    print(f"Number of records: {num_records}")
    offset += 1
    
    records = []
    for i in range(num_records):
        print(f"\n--- Record {i+1}/{num_records} ---")
        
        # Timestamp (8 bytes)
        timestamp = struct.unpack('>Q', data[offset:offset+8])[0]
        print(f"Timestamp raw: {timestamp}")
        
        # Převod timestamp na datum
        if timestamp > 9999999999999:  # Příliš velký timestamp
            print(f"Invalid timestamp {timestamp}, using current time")
            readable_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            try:
                readable_time = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
            except:
                print(f"Invalid timestamp {timestamp}, using current time")
                readable_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Timestamp: {readable_time}")
        offset += 8
        
        # Priority
        priority = data[offset]
        print(f"Priority: {priority}")
        offset += 1
        
        # GPS Element
        print("\nGPS Data:")
        longitude = struct.unpack('>i', data[offset:offset+4])[0]
        print(f"  Longitude raw: {longitude}")
        print(f"  Longitude: {longitude / 10000000.0:.6f}")
        offset += 4
        
        latitude = struct.unpack('>i', data[offset:offset+4])[0]
        print(f"  Latitude raw: {latitude}")
        print(f"  Latitude: {latitude / 10000000.0:.6f}")
        offset += 4
        
        altitude = struct.unpack('>H', data[offset:offset+2])[0]
        print(f"  Altitude: {altitude} m")
        offset += 2
        
        angle = struct.unpack('>H', data[offset:offset+2])[0]
        print(f"  Angle: {angle}°")
        offset += 2
        
        satellites = data[offset]
        print(f"  Satellites: {satellites}")
        offset += 1
        
        speed = struct.unpack('>H', data[offset:offset+2])[0]
        print(f"  Speed: {speed} km/h")
        offset += 2
        
        # IO Element
        print("\nIO Data:")
        
        if codec_id == 0x8E:  # Codec 8 Extended
            # Event IO ID (2 bytes)
            event_io_id = struct.unpack('>H', data[offset:offset+2])[0]
            print(f"  Event IO ID: {event_io_id}")
            offset += 2
            
            # Total IO count (2 bytes)
            total_io_count = struct.unpack('>H', data[offset:offset+2])[0]
            print(f"  Total IO count: {total_io_count}")
            offset += 2
        else:  # Codec 8
            # Event IO ID (1 byte)
            event_io_id = data[offset]
            print(f"  Event IO ID: {event_io_id}")
            offset += 1
            
            # Total IO count (1 byte)
            total_io_count = data[offset]
            print(f"  Total IO count: {total_io_count}")
            offset += 1
        
        io_data = {}
        
        # Parse IO elements by size (1, 2, 4, 8 bytes)
        for io_size in [1, 2, 4, 8]:
            if codec_id == 0x8E:
                count = struct.unpack('>H', data[offset:offset+2])[0]
                offset += 2
            else:
                count = data[offset]
                offset += 1
            
            print(f"  {io_size}-byte IO elements: {count}")
            
            for _ in range(count):
                if codec_id == 0x8E:
                    io_id = struct.unpack('>H', data[offset:offset+2])[0]
                    offset += 2
                else:
                    io_id = data[offset]
                    offset += 1
                
                if io_size == 1:
                    value = data[offset]
                    offset += 1
                elif io_size == 2:
                    value = struct.unpack('>H', data[offset:offset+2])[0]
                    offset += 2
                elif io_size == 4:
                    value = struct.unpack('>I', data[offset:offset+4])[0]
                    offset += 4
                elif io_size == 8:
                    value = struct.unpack('>Q', data[offset:offset+8])[0]
                    offset += 8
                
                io_data[f'io{io_id}'] = value
                print(f"    IO{io_id} = {value}")
        
        record = {
            'timestamp': readable_time,
            'latitude': latitude / 10000000.0,
            'longitude': longitude / 10000000.0,
            'altitude': altitude,
            'angle': angle,
            'satellites': satellites,
            'speed': speed,
            'io_data': io_data
        }
        records.append(record)
    
    # Number of records na konci
    final_records = data[offset]
    print(f"\nFinal record count: {final_records}")
    offset += 1
    
    # CRC (4 bytes)
    if offset + 4 <= len(data):
        crc = struct.unpack('>I', data[offset:offset+4])[0]
        print(f"CRC: {crc:08X}")
        offset += 4
    
    print(f"\nParsed {len(records)} records successfully")
    print(f"Total bytes processed: {offset}/{len(data)}")
    
    return records

def main():
    # Načti testovací data
    with open('test/simple_packets.json', 'r') as f:
        test_packets = json.load(f)
    
    print("Dostupné pakety:")
    for i, packet in enumerate(test_packets):
        hex_data = packet.get('data', '')
        imei = packet.get('imei', 'unknown')
        print(f"{i}: IMEI {imei}, {len(hex_data)//2} bytes, starts with {hex_data[:20]}...")
    
    print("\nVyberu paket #2 (kratší AVL data paket):")
    selected_packet = test_packets[2]  # Kratší AVL data paket
    hex_data = selected_packet.get('data', '')
    
    print(f"IMEI: {selected_packet.get('imei')}")
    print(f"Hex data length: {len(hex_data)} characters ({len(hex_data)//2} bytes)")
    
    # Převeď hex string na bytes
    binary_data = bytes.fromhex(hex_data)
    
    try:
        records = parse_avl_data(binary_data)
        print("\n" + "="*80)
        print("SHRNUTÍ ROZPARSOVANÝCH DAT:")
        print("="*80)
        
        for i, record in enumerate(records, 1):
            print(f"\nRecord {i}:")
            print(f"  Čas: {record['timestamp']}")
            print(f"  GPS: {record['latitude']:.6f}, {record['longitude']:.6f}")
            print(f"  Výška: {record['altitude']} m")
            print(f"  Rychlost: {record['speed']} km/h")
            print(f"  Satelity: {record['satellites']}")
            print(f"  Směr: {record['angle']}°")
            print(f"  IO prvky: {len(record['io_data'])}")
            
            # Zobraz prvních 10 IO prvků
            io_items = list(record['io_data'].items())[:10]
            for io_id, value in io_items:
                print(f"    {io_id} = {value}")
            if len(record['io_data']) > 10:
                print(f"    ... a {len(record['io_data']) - 10} dalších IO prvků")
    
    except Exception as e:
        print(f"Chyba při parsování: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()