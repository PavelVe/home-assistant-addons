#!/usr/bin/env python3
"""Test TCP fragmentation handling"""

import struct
from datetime import datetime

# První fragment (končí uprostřed packetu)
fragment1_hex = '00000000000004E98E0B00000198BBD9409A0108A6807F1DDB756400EA015E0B000000FC0014000800EF0100F00100150400C80000450100010000710300FC01000A00B5001400B6000A0042134800CD049D00CE405000430D5C0044004E0011FF890012FEC5001304C8000200F1000059D90010000196400000000000000198BD46F5A80108A6807F1DDB756400EA015E00000000FC0014000800EF0000F00000150300C80000450200010000710000FC00000A00B5000000B600000042516E00CD049D00CE405000430CDF00440000001103990012FFF10013FE7D000200F1000059D90010000196400000000000000198BD479DA00108A6807F1DDB756400EA015E00000000FC0014000800EF0000F00000150400C80000450200010000710000FC00000A00B5000000B600000042516E00CD049F00CE405000430CDF00440000001103D00012FFAE0013FF47000200F1000059D900100001964000000000000000F9CEBAFAC30108A6807F1DDB756400EA015E00000000F70014000800F70600EF0000F00000150000C800004502000100007100000A00B5000000B600000042512300CD000000CE000000430000004400000011FCD7001202AD001304FE000200F1000000000010000196400000000000000198C5D1E5200108A6807F1DDB756400EA015E00000000FC0014000800EF0100F00100150300C80000450200010000710000FC00000A00B5000000B600000042511900CD049F00CE405000430CCB004400000011F5770012FB400013040E000200F1000059D90010000196400000000000000198C714D9430108A6807F1DDB75640000000000000000F70014000800F70600EF0100F00100150300C800004502000100007121000A00B5000000B60000004250EB00CD049D00CE405000430E9E0044008C0011FF6B0012FD65001302ED000200F1000059D90010000196400000000000000198D009294B0108ACC1161DDD4F7A00F501350B000100F70014000800F70100EF0100F00100150400C80000450100010000715F000A00B5000B00B600080042506800CD228900CE40500043100E00440052001101320012017F0013F886000200F1000059D900100001C30E0000000000000198D017BBC30108ACC2741DDD4D6500F1008B0E000000F70014000800F70100EF0100F00100150400C800004501000100007162000A00B5000E00B600070042504100CD228900CE405000431025004400490011FC1F0012FFC90013FA75000200F1000059D900100001C30E0000000000000198D01A15530108ACC2741DDD4D6500F1008B0E000000F70014000800F70100EF0100F00100150500C800004501000100007164000A00B5000B00B600070042504200CD228900CE40500043102E004400440011FDE8001201E50013F6F4000200F10000'

# Druhý fragment (pokračování prvního packetu)
fragment2_hex = '59D900100001C30E0000000000000198D0299D880108ACC2951DDD4E4E00EF013C0E000000FC0014000800EF0100F00100150300C80000450100010000716400FC01000A00B5000A00B6000700420ED400CD228900CE405000430FB1004400000011FBEB0012FF840013FBE3000200F1000059D900100001C30E0000000000000198D029B1100108ACC2951DDD4E4E00EF013C0E000000FC0014000800EF0100F00100150300C80000450100010000716400FC00000A00B5000A00B6000700421C0C00CD228900CE405000430F78004400000011FC620012FEF00013FCC1000200F1000059D900100001C30E000000000B0000A713'

# Spojíme fragmenty
fragment1 = bytes.fromhex(fragment1_hex)
fragment2 = bytes.fromhex(fragment2_hex)

print("=== TEST TCP FRAGMENTACE ===")
print(f"Fragment 1: {len(fragment1)} bytes")
print(f"Fragment 2: {len(fragment2)} bytes")
print()

# Analýza prvního fragmentu
print("=== PRVNÍ FRAGMENT ===")
preamble = fragment1[0:4]
data_length = struct.unpack('>I', fragment1[4:8])[0]
codec = fragment1[8]
count = fragment1[9]

print(f"Preamble: {preamble.hex()}")
print(f"Data length: {data_length} bytes")
print(f"Codec: 0x{codec:02X}")
print(f"Record count: {count}")
print(f"Total packet size should be: {8 + data_length + 4} bytes")
print(f"Fragment 1 has: {len(fragment1)} bytes")
print(f"Missing: {8 + data_length + 4 - len(fragment1)} bytes")
print()

# Pokus o spojení
print("=== SPOJENÍ FRAGMENTŮ ===")
complete_data = fragment1 + fragment2
print(f"Combined size: {len(complete_data)} bytes")
print(f"Expected packet size: {8 + data_length + 4} bytes")

if len(complete_data) >= 8 + data_length + 4:
    print("✅ Máme kompletní packet!")
    
    # Ověř CRC na konci
    expected_end = 8 + data_length
    crc_bytes = complete_data[expected_end:expected_end+4]
    print(f"CRC bytes: {crc_bytes.hex()}")
    
    # Zkus parsovat
    print()
    print("=== PARSING KOMPLETNÍHO PACKETU ===")
    
    # Import parsing funkcí
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from teltonika_protocol import parse_avl_packet_with_length
    
    records, record_count, codec_type, packet_length = parse_avl_packet_with_length(complete_data)
    
    if records:
        print(f"✅ Úspěšně naparsováno {record_count} záznamů!")
        print(f"Codec: {codec_type}")
        print(f"Packet length: {packet_length}")
        
        # Ukáž první záznam
        if len(records) > 0:
            record = records[0]
            print(f"\nPrvní záznam:")
            print(f"  Timestamp: {record['timestamp']}")
            print(f"  GPS: {record['gps']['latitude']:.6f}, {record['gps']['longitude']:.6f}")
            print(f"  Speed: {record['gps']['speed']} km/h")
            
            # Je to v ČR?
            lat = record['gps']['latitude']
            lon = record['gps']['longitude']
            if 48.5 < lat < 51.1 and 12.0 < lon < 19.0:
                print(f"  ✅ GPS souřadnice jsou v České republice!")
    else:
        print("❌ Parsing selhal!")
        
    # Je tam ještě něco?
    if len(complete_data) > packet_length:
        print(f"\n⚠️ Data obsahují další packet!")
        print(f"Zbývá {len(complete_data) - packet_length} bytes")
        next_data = complete_data[packet_length:]
        print(f"Další data začínají: {next_data[:20].hex()}")
else:
    print("❌ Stále nemáme kompletní packet!")
    print(f"Chybí ještě {8 + data_length + 4 - len(complete_data)} bytes")