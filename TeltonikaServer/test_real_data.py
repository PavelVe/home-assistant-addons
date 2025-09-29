#!/usr/bin/env python3
"""Test script to simulate real Teltonika GPS data with TCP fragmentation"""

import socket
import time
import binascii
import struct
from datetime import datetime

def send_real_teltonika_data(host="192.168.1.16", port=3030):
    """Send real Teltonika data from log with fragmentation simulation"""
    
    imei = "350317176700155"
    
    print(f"🛰️ Teltonika Real Data Test")
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
        
        print(f"\n📡 Sending IMEI handshake...")
        print(f"Raw: {imei_hex}")
        client.send(imei_data)
        
        # Receive IMEI response
        response = client.recv(1)
        print(f"Response: {binascii.hexlify(response).decode().upper()}")
        
        if response == b'\x01':
            print("✅ IMEI accepted!")
            
            # Test data packets from your log
            test_packets = [
                # Packet 1: Complete packet with 11 records
                {
                    "name": "Packet 1 (11 records)",
                    "hex": "00000000000004C88E0B00000197C9BF35A80000000000000000000000000000000000000013000700EF0000F00000150000C800004502000100007158000A00B5000000B60000004232FC00CD000000CE000000430F60004400030011FFF700120000001303CB000200F1000000000010000000000000000000000197C9C0EB280000000000000000000000000000000000EF0013000700EF0100F00100150400C800004502000100007159000A00B5000000B600000042000000CD049D00CE405000430F0D004400000011FF7D0012036A0013024B000200F1000059D90010000000000000000000000197C9C0EB320000000000000000000000000000000000F00013000700EF0100F00100150400C800004502000100007159000A00B5000000B600000042000000CD049D00CE405000430F0D004400000011FF7D0012036A0013024B000200F1000059D90010000000000000000000000197C9C160580000000000000000000000000000000000000013000700EF0100F00100150400C800004502000100007158000A00B5000000B600000042000000CD049D00CE405000430F20004400000011018F0012018F00130319000200F1000059D90010000000000000000000000197C9C1D5880000000000000000000000000000000000000013000700EF0100F00100150400C800004502000100007158000A00B5000000B600000042000000CD049D00CE405000430F1A004400000011FFCC001200BC001303BA000200F1000059D90010000000000000000000000197C9C24AB80000000000000000000000000000000000000013000700EF0100F00100150300C800004502000100007158000A00B5000000B600000042000000CD049D00CE405000430F18004400000011FFD0001200AF001303B9000200F1000059D90010000000000000000000000197C9C2BFE80000000000000000000000000000000000000013000700EF0100F00100150300C800004502000100007157000A00B5000000B600000042000000CD049D00CE405000430F02004400000011FFD1001200AA001303B9000200F1000059D90010000000000000000000000197C9C335180000000000000000000000000000000000000013000700EF0100F00100150300C800004502000100007157000A00B5000000B600000042000000CD049D00CE405000430EFE004400000011FFE0001200AD001303BB000200F1000059D90010000000000000000000000197C9C3AA480000000000000000000000000000000000000013000700EF0100F00100150300C800004502000100007157000A00B5000000B600000042000000CD049D00CE405000430EFC004400000011FFD1001200AF001303C7000200F1000059D90010000000000000000000000197C9C41F7800000000000000",
                    "fragment": False
                },
                
                # Packet 2: Fragmented packet (first part)
                {
                    "name": "Packet 2 Fragment 1",
                    "hex": "00000000000000000000000013000700EF0100F00100150300C800004502000100007157000A00B5000000B600000042000000CD049D00CE405000430EFA004400000011FFF0001200DB001303A9000200F1000059D90010000000000000000000000197C9C494A80000000000000000000000000000000000000013000700EF0100F00100150300C800004502000100007156000A00B5000000B600000042000000CD049D00CE405000430EE3004400000011FFE5001200DB001303AA000200F1000059D9001000000000000000000B0000C3AA",
                    "fragment": "first",
                    "delay": 0.1  # Small delay before second fragment
                },
                
                # Packet 2: Fragmented packet (second part) 
                {
                    "name": "Packet 2 Fragment 2",
                    "hex": "00000000000004C88E0B00000197C9C4CB580000000000000000000000000000000000EF0013000700EF0000F00000150300C800004502000100007155000A00B5000000B600000042000000CD049D00CE405000430EF1004400000011FFEC001200D0001303B9000200F1000059D90010000000000000000000000197C9C4CB620000000000000000000000000000000000F00013000700EF0000F00000150300C800004502000100007155000A00B5000000B600000042000000CD049D00CE405000430EF1004400000011FFEA001200CF001303B8000200F1000059D90010000000000000000000000197C9C6A0180000000000000000000000000000000000000013000700EF0000F00000150300C800004502000100007153000A00B5000000B600000042000000CD049F00CE405000430EFA004400000011FFAB001200B5001303B9000200F1000059D90010000000000000000000000197C9CBE3C00000000000000000000000000000000000000013000700EF0000F00000150000C800004502000100007152000A00B5000000B600000042501800CD000000CE000000430F37004400000011FFD0001200B9001303BF000200F1000059D90010000000000000000000000197C9CBE3D40000000000000000000000000000000000EF0013000700EF0100F00100150000C800004502000100007152000A00B5000000B600000042517700CD000000CE000000430F56004400290011FF860012FF4A001303F0000200F1000059D90010000000000000000000000197C9CBE3DE0000000000000000000000000000000000F00013000700EF0100F00100150000C800004502000100007152000A00B5000000B600000042517700CD000000CE000000430F56004400290011FF860012FF4A001303F0000200F1000059D90010000000000000000000000197C9CC58F00000000000000000000000000000000000000013000700EF0100F00100150300C800004502000100007152000A00B5000000B600000042516900CD049F00CE405000430FD40044008B0011000000120039001303CB000200F1000059D90010000000000000000000000197C9CCCE200000000000000000000000000000000000000013000700EF0100F00100150300C800004502000100007153000A00B5000000B600000042516400CD049F00CE405000430FD800440084001100090012002C001303D8000200F1000059D90010000000000000000000000197C9CD43500000000000000000000000000000000000000013000700EF0100F00100150300C800004502000100007154000A00B5000000B600000042516500CD049D00CE405000430FE400440080001100000012002A001303CE000200F1000059D90010000000000000000000000197C9CDB88000000000000000",
                    "fragment": "second"
                }
            ]
            
            for i, packet_info in enumerate(test_packets):
                print(f"\n📦 Sending {packet_info['name']}")
                
                # Add delay if specified
                if 'delay' in packet_info:
                    print(f"⏱️ Waiting {packet_info['delay']}s before sending...")
                    time.sleep(packet_info['delay'])
                
                packet_data = bytes.fromhex(packet_info['hex'])
                print(f"Size: {len(packet_data)} bytes")
                print(f"Raw: {packet_info['hex'][:100]}...")
                
                client.send(packet_data)
                
                # Only expect ACK for complete packets or last fragment
                if not packet_info.get('fragment') or packet_info.get('fragment') == 'second':
                    try:
                        client.settimeout(2.0)  # 2 second timeout
                        ack = client.recv(4)
                        if len(ack) == 4:
                            record_count = struct.unpack('>I', ack)[0]
                            print(f"✅ Server ACK: {record_count} records processed")
                        else:
                            print(f"⚠️ Unexpected ACK: {binascii.hexlify(ack).decode().upper()}")
                    except socket.timeout:
                        print("⚠️ No ACK received (timeout)")
                    finally:
                        client.settimeout(None)
                else:
                    print("📤 Fragment sent (no ACK expected)")
                
                time.sleep(1)  # Wait between packets
            
            print(f"\n🎯 Test completed! All packets sent.")
            
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

def test_simple_packet(host="192.168.1.16", port=3030):
    """Test s jednoduchým packetem s reálným timestampem"""
    
    print(f"\n🔧 Simple packet test")
    print(f"Target: {host}:{port}")
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        
        # IMEI handshake
        imei_hex = "000F333530333137313736373030313535"
        client.send(bytes.fromhex(imei_hex))
        response = client.recv(1)
        
        if response == b'\x01':
            print("✅ IMEI OK")
            
            # Vytvoř packet s reálným timestampem
            current_time_ms = int(time.time() * 1000)
            print(f"Using timestamp: {current_time_ms} ({datetime.fromtimestamp(current_time_ms/1000)})")
            
            # Build simple AVL packet
            packet = bytearray()
            packet.extend(b'\x00\x00\x00\x00')  # Preamble
            
            # Data part (will be filled)
            data_start = len(packet)
            packet.extend(b'\x00\x00\x00\x00')  # Data length placeholder
            
            packet.append(0x08)  # Codec 8
            packet.append(0x01)  # 1 record
            
            # AVL Record
            packet.extend(struct.pack('>Q', current_time_ms))  # Timestamp
            packet.append(0x01)  # Priority
            packet.extend(struct.pack('>i', 491520000))  # Longitude (49.1520000 * 10^7) 
            packet.extend(struct.pack('>i', 164230000))  # Latitude (16.4230000 * 10^7)
            packet.extend(struct.pack('>H', 142))        # Altitude
            packet.extend(struct.pack('>H', 90))         # Angle  
            packet.append(8)                             # Satellites
            packet.extend(struct.pack('>H', 60))         # Speed km/h
            
            # I/O data
            packet.append(0x01)  # Event IO ID
            packet.append(0x02)  # Total IO elements
            
            # 1-byte values
            packet.append(0x01)  # Count
            packet.append(0x15)  # GSM signal
            packet.append(0x04)  # Value
            
            # 2-byte values
            packet.append(0x01)  # Count  
            packet.append(0x42)  # External voltage
            packet.extend(struct.pack('>H', 12500))  # 12.5V
            
            # No 4-byte and 8-byte values
            packet.append(0x00)
            packet.append(0x00)
            
            packet.append(0x01)  # Record count at end
            
            # CRC (simplified)
            packet.extend(b'\x00\x00\x00\x00')
            
            # Update data length
            data_length = len(packet) - data_start - 8  # Exclude preamble, length, and CRC
            packet[data_start:data_start+4] = struct.pack('>I', data_length)
            
            print(f"Sending realistic packet ({len(packet)} bytes)")
            client.send(packet)
            
            ack = client.recv(4)
            if len(ack) == 4:
                count = struct.unpack('>I', ack)[0]
                print(f"✅ ACK: {count} record(s)")
            
        client.close()
        
    except Exception as e:
        print(f"Error in simple test: {e}")

if __name__ == "__main__":
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.16"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 3030
    
    print("🚀 Starting Teltonika Real Data Test")
    print(f"Target server: {host}:{port}")
    print("=" * 60)
    
    # Test 1: Simple packet
    test_simple_packet(host, port)
    
    time.sleep(2)
    
    # Test 2: Complex fragmented data
    send_real_teltonika_data(host, port)
    
    print("\n✨ All tests completed!")