#!/usr/bin/env python3

# Jednoduché testování bez interaktivního vstupu
from working_parse_debug_fixed import codec_8e_checker, codec_parser_trigger

def test_parser():
    # Testovací hex paket
    test_hex = "00000000000004C88E0B00000197C9CEA2E00000000000000000000000000000000000000013000700EF0100F00100150400C8000200450002007100580001001100D8000B005B0000CD00004040906700000197C9CEAEE00000000000000000000000000000000000000013000700EF0100F00100150500C8000200450002007100590001001100D8000B005B0000CD00004040916700000197C9CEF1E00000000000000000000000000000000000000013000700EF0100F00100150300C8000200450002007100580001001100D8000B005B0000CD000040409200000000ABCD"
    
    print("=== Simple Parser Test ===")
    print(f"Testing hex packet ({len(test_hex)} chars, {len(test_hex)//2} bytes)")
    print(f"Hex: {test_hex[:50]}...")
    
    # Test validation
    if codec_8e_checker(test_hex):
        print("✓ Packet validation passed")
        
        # Test parsing
        result = codec_parser_trigger(test_hex, "test_device_123", "USER_SILENT")
        print(f"✓ Parsing completed, result: {result}")
    else:
        print("✗ Packet validation failed")

if __name__ == "__main__":
    test_parser()