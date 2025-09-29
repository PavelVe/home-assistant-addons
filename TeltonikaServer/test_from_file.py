#!/usr/bin/env python3

# Test parser s hex daty ze souboru
from working_parse_debug_fixed import codec_8e_checker, codec_parser_trigger

def test_from_file(filename):
    try:
        with open(filename, 'r') as f:
            hex_data = f.read().strip().replace(' ', '').replace('\n', '')
        
        print(f"=== Testing from file: {filename} ===")
        print(f"Hex data length: {len(hex_data)} chars ({len(hex_data)//2} bytes)")
        print(f"First 50 chars: {hex_data[:50]}...")
        
        if codec_8e_checker(hex_data):
            print("✓ Packet validation passed")
            result = codec_parser_trigger(hex_data, f"device_from_{filename}", "USER_SILENT")
            print(f"✓ Parsing completed, result: {result}")
        else:
            print("✗ Packet validation failed")
            
    except FileNotFoundError:
        print(f"File {filename} not found!")
        print("Usage: python test_from_file.py")
        print("Create a text file with hex data (e.g., 'hex_data.txt') and run again")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_from_file(sys.argv[1])
    else:
        # Default test file
        test_from_file("hex_data.txt")