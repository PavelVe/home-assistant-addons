#!/usr/bin/env python3
"""Test script for fragmented packet handling with real data"""

import socket
import time
import binascii
import struct

def send_fragmented_real_data(host="localhost", port=3030):
    """Test fragmentace s reálnými daty"""
    
    imei = "350317176700155"
    
    print(f"🛰️ Testing Real Fragmented Data")
    print(f"Target: {host}:{port}")
    print(f"IMEI: {imei}")
    print("-" * 50)
    
    # Originální neúplná data (1024 bytes ale očekává 1224)
    original_hex = "00000000000004C88E0B00000197C9CEA2E00000000000000000000000000000000000000013000700EF0100F00100150400C800004502000100007157000A00B5000000B600000042516500CD049D00CE405000430FEF004400790011000000120029001303CE000200F1000059D90010000000000000000000000197C9CF18100000000000000000000000000000000000000013000700EF0100F00100150400C800004502000100007158000A00B5000000B600000042516500CD049D00CE405000430FF100440077001100000012002A001303CF000200F1000059D90010000000000000000000000197C9CF8D400000000000000000000000000000000000000013000700EF0100F00100150400C800004502000100007158000A00B5000000B600000042516500CD049D00CE405000430FF2004400750011000900120031001303CC000200F1000059D90010000000000000000000000197C9D002700000000000000000000000000000000000000013000700EF0100F00100150500C800004502000100007159000A00B5000000B600000042516500CD049D00CE405000430FF5004400730011000900120010001303D7000200F1000059D90010000000000000000000000197C9D077A00000000000000000000000000000000000000013000700EF0100F00100150300C80000450200010000715A000A00B5000000B600000042516500CD049D00CE405000430FFA00440072001100000012000F001303D9000200F1000059D90010000000000000000000000197C9D0ECD00000000000000000000000000000000000000013000700EF0100F00100150400C80000450200010000715A000A00B5000000B600000042516700CD049D00CE405000430FFC0044006F0011FFF70012000F001303CC000200F1000059D90010000000000000000000000197C9D162000000000000000000000000000000000000000013000700EF0100F00100150400C80000450200010000715B000A00B5000000B600000042516500CD049D00CE405000430FFF0044006E0011000000120019001303CF000200F1000059D90010000000000000000000000197C9D1D7300000000000000000000000000000000000000013000700EF0100F00100150400C80000450200010000715C000A00B5000000B600000042516500CD049D00CE4050004310030044006C0011FFF20012000A001303CF000200F1000059D90010000000000000000000000197C9D24C600000000000000000000000000000000000000013000700EF0100F00100150400C80000450200010000715C000A00B5000000B600000042516500CD049D00CE4050004310040044006A001100000012000F001303C9000200F1000059D90010000000000000000000000197C9D2C19000000000000000"
    
    # Vytvoř simulované chybějící data (200 bytů)
    missing_data = "0B00000197C9D33850000000000000000000000000000000000000000013000700EF0100F00100150400C80000450200010000715D000A00B5000000B600000042516500CD049D00CE405000430FF8004400680011000000120017001303CA000200F1000059D90010000000000000000000000197C9D3AD800000000000000000000000000000000000000013000700EF0100F00100150400C8000045020001000071000000"
    
    # Fragment 1: Původní neúplná data 
    fragment1 = bytes.fromhex(original_hex)
    
    # Fragment 2: Simulované chybějící data + CRC
    fragment2 = bytes.fromhex(missing_data + "00000000")  # + 4 bytes CRC
    
    print(f"Fragment 1: {len(fragment1)} bytes")
    print(f"Fragment 2: {len(fragment2)} bytes")
    print(f"Total: {len(fragment1) + len(fragment2)} bytes")
    
    try:
        # === ČÁST 1: Pošli první fragment ===
        print(f"\\n📦 Část 1: Posílám první fragment...")
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect((host, port))
        
        # IMEI handshake
        imei_hex = "000F333530333137313736373030313535"
        imei_data = bytes.fromhex(imei_hex)
        client1.send(imei_data)
        response = client1.recv(1)
        
        if response == b'\\x01':
            print("✅ IMEI accepted")
            
            # Pošli první fragment
            client1.send(fragment1)
            print(f"📤 Odesláno {len(fragment1)} bytů (neúplný packet)")
            
            # Krátká pauza a odpojení
            time.sleep(0.5)
            client1.close()
            print("🔌 První spojení ukončeno (buffer by měl zůstat)")
        else:
            print("❌ IMEI rejected")
            return
        
        # Pauza mezi spojníc
        time.sleep(2)
        
        # === ČÁST 2: Pošli druhý fragment ===
        print(f"\\n📦 Část 2: Posílám druhý fragment...")
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect((host, port))
        
        # IMEI handshake znovu
        client2.send(imei_data)
        response = client2.recv(1)
        
        if response == b'\\x01':
            print("✅ IMEI znovu accepted")
            
            # Pošli druhý fragment
            client2.send(fragment2)
            print(f"📤 Odesláno {len(fragment2)} bytů (dokončení packetu)")
            
            # Čekej na ACK
            try:
                client2.settimeout(5.0)
                ack = client2.recv(4)
                if len(ack) == 4:
                    record_count = struct.unpack('>I', ack)[0]
                    print(f"✅ Server ACK: {record_count} records processed")
                    if record_count > 0:
                        print("🎯 Úspěch! Fragmentovaný packet byl správně zpracován!")
                    else:
                        print("⚠️ Packet nebyl zpracován")
                else:
                    print(f"⚠️ Unexpected ACK: {binascii.hexlify(ack).decode().upper()}")
            except socket.timeout:
                print("⚠️ No ACK received")
            finally:
                client2.settimeout(None)
                client2.close()
        else:
            print("❌ IMEI rejected at second connection")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        
    print("🔌 Test completed")

if __name__ == "__main__":
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 3030
    
    print("🚀 Starting Fragmented Real Data Test")
    print(f"Target server: {host}:{port}")
    print("=" * 60)
    
    send_fragmented_real_data(host, port)
    
    print("\\n✨ All tests completed!")