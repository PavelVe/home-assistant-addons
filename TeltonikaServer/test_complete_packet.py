#!/usr/bin/env python3
"""Test script with properly sized complete packet"""

import socket
import time
import binascii
import struct

def test_complete_packet(host="localhost", port=3030):
    """Test s kompletním packetem s upravenou délkou"""
    
    imei = "350317176700155"
    
    print(f"🛰️ Testing Complete Packet")
    print(f"Target: {host}:{port}")
    print(f"IMEI: {imei}")
    print("-" * 50)
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        print(f"✅ Connected to {host}:{port}")
        
        # Step 1: Send IMEI handshake
        imei_hex = "000F333530333137313736373030313535"
        imei_data = bytes.fromhex(imei_hex)
        
        print(f"\\n📡 Sending IMEI handshake...")
        client.send(imei_data)
        
        # Receive IMEI response
        response = client.recv(1)
        print(f"Response: {binascii.hexlify(response).decode().upper()}")
        
        if response == b'\x01':
            print("✅ IMEI accepted!")
            
            # Original data (fragment)
            original_hex = "00000000000004C88E0B00000197C9CEA2E00000000000000000000000000000000000000013000700EF0100F00100150400C800004502000100007157000A00B5000000B600000042516500CD049D00CE405000430FEF004400790011000000120029001303CE000200F1000059D90010000000000000000000000197C9CF18100000000000000000000000000000000000000013000700EF0100F00100150400C800004502000100007158000A00B5000000B600000042516500CD049D00CE405000430FF100440077001100000012002A001303CF000200F1000059D90010000000000000000000000197C9CF8D400000000000000000000000000000000000000013000700EF0100F00100150400C800004502000100007158000A00B5000000B600000042516500CD049D00CE405000430FF2004400750011000900120031001303CC000200F1000059D90010000000000000000000000197C9D002700000000000000000000000000000000000000013000700EF0100F00100150500C800004502000100007159000A00B5000000B600000042516500CD049D00CE405000430FF5004400730011000900120010001303D7000200F1000059D90010000000000000000000000197C9D077A00000000000000000000000000000000000000013000700EF0100F00100150300C80000450200010000715A000A00B5000000B600000042516500CD049D00CE405000430FFA00440072001100000012000F001303D9000200F1000059D90010000000000000000000000197C9D0ECD00000000000000000000000000000000000000013000700EF0100F00100150400C80000450200010000715A000A00B5000000B600000042516700CD049D00CE405000430FFC0044006F0011FFF70012000F001303CC000200F1000059D90010000000000000000000000197C9D162000000000000000000000000000000000000000013000700EF0100F00100150400C80000450200010000715B000A00B5000000B600000042516500CD049D00CE405000430FFF0044006E0011000000120019001303CF000200F1000059D90010000000000000000000000197C9D1D7300000000000000000000000000000000000000013000700EF0100F00100150400C80000450200010000715C000A00B5000000B600000042516500CD049D00CE4050004310030044006C0011FFF20012000A001303CF000200F1000059D90010000000000000000000000197C9D24C600000000000000000000000000000000000000013000700EF0100F00100150400C80000450200010000715C000A00B5000000B600000042516500CD049D00CE4050004310040044006A001100000012000F001303C9000200F1000059D90010000000000000000000000197C9D2C19000000000000000"
            
            # Convert to bytes
            original_data = bytes.fromhex(original_hex)
            print(f"Original data length: {len(original_data)} bytes")
            
            # Fix the data length field to match actual data
            # Current: says 1224 bytes, but we have 1024
            # Calculate actual data length (total - preamble(4) - length_field(4) - crc(4))
            actual_data_length = len(original_data) - 12  # 1024 - 12 = 1012
            
            # Create new packet with corrected length
            corrected_packet = bytearray(original_data)
            corrected_packet[4:8] = struct.pack('>I', actual_data_length)
            
            print(f"\\n📦 Sending Corrected Complete Packet")
            print(f"Size: {len(corrected_packet)} bytes")
            print(f"Corrected data length: {actual_data_length} bytes")
            
            client.send(corrected_packet)
            
            # Receive ACK
            try:
                client.settimeout(5.0)
                ack = client.recv(4)
                if len(ack) == 4:
                    record_count = struct.unpack('>I', ack)[0]
                    print(f"✅ Server ACK: {record_count} records processed")
                    if record_count > 0:
                        print("🎯 Success! Records processed correctly")
                    else:
                        print("⚠️ No records processed - parsing issue")
                else:
                    print(f"⚠️ Unexpected ACK: {binascii.hexlify(ack).decode().upper()}")
            except socket.timeout:
                print("⚠️ No ACK received (timeout)")
            finally:
                client.settimeout(None)
                
        else:
            print("❌ IMEI rejected!")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            client.close()
        except:
            pass
        print("🔌 Connection closed")

if __name__ == "__main__":
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 3030
    
    print("🚀 Starting Complete Packet Test")
    print(f"Target server: {host}:{port}")
    print("=" * 60)
    
    test_complete_packet(host, port)
    
    print("\\n✨ Test completed!")