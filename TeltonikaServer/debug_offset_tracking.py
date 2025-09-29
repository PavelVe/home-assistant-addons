#!/usr/bin/env python3
"""
Debug přesného offset trackingu pro Codec8E
"""

import json
import struct

def debug_parse_codec8e_record(data, offset, record_num):
    print(f"\n=== RECORD {record_num} na offset {offset} ===")
    start_offset = offset
    
    # Timestamp (8 bytes)
    if offset + 8 > len(data):
        print(f"ERROR: Not enough data for timestamp")
        return None, offset
    timestamp = struct.unpack('>Q', data[offset:offset+8])[0]
    print(f"  Timestamp: {timestamp} (offset {offset}-{offset+7})")
    offset += 8
    
    # Priority (1 byte)
    priority = data[offset]
    print(f"  Priority: {priority} (offset {offset})")
    offset += 1
    
    # GPS (15 bytes)
    print(f"  GPS data (offset {offset}-{offset+14})")
    offset += 15
    
    # IO Event ID (2 bytes pro Codec8E)
    if offset + 2 > len(data):
        print(f"ERROR: Not enough data for IO Event ID")
        return None, offset
    io_event = struct.unpack('>H', data[offset:offset+2])[0]
    print(f"  IO Event ID: {io_event} (offset {offset}-{offset+1})")
    offset += 2
    
    # Total IO count (2 bytes pro Codec8E) 
    if offset + 2 > len(data):
        print(f"ERROR: Not enough data for IO count")
        return None, offset
    total_io = struct.unpack('>H', data[offset:offset+2])[0]
    print(f"  Total IO: {total_io} (offset {offset}-{offset+1})")
    offset += 2
    
    print(f"  IO data začíná na offset {offset}")
    
    # Track IO parsing detailně
    total_parsed_io = 0
    
    # 1-byte values
    if offset >= len(data):
        print(f"  ERROR: Reached end of data at offset {offset}")
        return None, offset
        
    count_1b = data[offset]
    print(f"    1-byte values: {count_1b} prvků (count na offset {offset})")
    offset += 1
    
    for i in range(count_1b):
        if offset + 2 > len(data):
            print(f"    ERROR: Not enough data for 1-byte IO {i}")
            break
        io_id = data[offset]
        io_value = data[offset+1]
        print(f"      IO{io_id} = {io_value} (offset {offset}-{offset+1})")
        offset += 2
        total_parsed_io += 1
    
    # 2-byte values
    if offset >= len(data):
        print(f"  Reached end at offset {offset}")
        record_size = offset - start_offset
        print(f"  Record {record_num} velikost: {record_size} bytes")
        print(f"  Parsed IO elements: {total_parsed_io}/{total_io}")
        return {"parsed_io": total_parsed_io, "expected_io": total_io}, offset
        
    count_2b = data[offset]
    print(f"    2-byte values: {count_2b} prvků (count na offset {offset})")
    offset += 1
    
    for i in range(count_2b):
        if offset + 3 > len(data):
            print(f"    ERROR: Not enough data for 2-byte IO {i}")
            break
        io_id = data[offset]
        io_value = struct.unpack('>H', data[offset+1:offset+3])[0]
        print(f"      IO{io_id} = {io_value} (offset {offset}-{offset+2})")
        offset += 3
        total_parsed_io += 1
    
    # 4-byte values
    if offset >= len(data):
        print(f"  Reached end at offset {offset}")
        record_size = offset - start_offset
        print(f"  Record {record_num} velikost: {record_size} bytes")
        print(f"  Parsed IO elements: {total_parsed_io}/{total_io}")
        return {"parsed_io": total_parsed_io, "expected_io": total_io}, offset
        
    count_4b = data[offset]
    print(f"    4-byte values: {count_4b} prvků (count na offset {offset})")
    offset += 1
    
    for i in range(count_4b):
        if offset + 5 > len(data):
            print(f"    ERROR: Not enough data for 4-byte IO {i}")
            break
        io_id = data[offset]
        io_value = struct.unpack('>I', data[offset+1:offset+5])[0]
        print(f"      IO{io_id} = {io_value} (offset {offset}-{offset+4})")
        offset += 5
        total_parsed_io += 1
    
    # 8-byte values
    if offset >= len(data):
        print(f"  Reached end at offset {offset}")
        record_size = offset - start_offset
        print(f"  Record {record_num} velikost: {record_size} bytes")
        print(f"  Parsed IO elements: {total_parsed_io}/{total_io}")
        return {"parsed_io": total_parsed_io, "expected_io": total_io}, offset
        
    count_8b = data[offset]
    print(f"    8-byte values: {count_8b} prvků (count na offset {offset})")
    offset += 1
    
    for i in range(count_8b):
        if offset + 9 > len(data):
            print(f"    ERROR: Not enough data for 8-byte IO {i}")
            break
        io_id = data[offset]
        io_value = struct.unpack('>Q', data[offset+1:offset+9])[0]
        print(f"      IO{io_id} = {io_value} (offset {offset}-{offset+8})")
        offset += 9
        total_parsed_io += 1
    
    record_size = offset - start_offset
    print(f"  Record {record_num} velikost: {record_size} bytes")
    print(f"  Parsed IO elements: {total_parsed_io}/{total_io}")
    
    if total_parsed_io != total_io:
        print(f"  WARNING: IO count mismatch! Expected {total_io}, got {total_parsed_io}")
    
    return {"parsed_io": total_parsed_io, "expected_io": total_io}, offset

def main():
    # Načti testovací data
    with open('test/simple_packets.json', 'r') as f:
        test_packets = json.load(f)
    
    selected_packet = test_packets[1]
    hex_data = selected_packet.get('data', '')
    binary_data = bytes.fromhex(hex_data)
    
    print("DETAILNÍ DEBUG OFFSET TRACKING:")
    print("=" * 60)
    
    # Header
    records_count = binary_data[9]
    print(f"Expected records: {records_count}")
    
    offset = 10  # Po headeru
    
    # Parsuj první 3 recordy
    for i in range(min(3, records_count)):
        record_info, new_offset = debug_parse_codec8e_record(binary_data, offset, i+1)
        if record_info is None:
            print(f"Failed to parse record {i+1}")
            break
        offset = new_offset
        
        # Zobraz hex data kolem dalšího recordu
        if i < 2 and offset < len(binary_data):
            print(f"\nHex data kolem dalšího recordu (offset {offset}):")
            start = max(0, offset - 8)
            end = min(len(binary_data), offset + 24)
            line = binary_data[start:end]
            hex_str = ' '.join(f'{b:02X}' for b in line)
            print(f"{start:04X}: {hex_str}")

if __name__ == "__main__":
    main()