#!/usr/bin/env python3
"""Test script to send Teltonika AVL data"""

import socket
import time
import struct
import binascii
from datetime import datetime

def send_teltonika_data(host, port, imei="352093081452251"):
    """Send test Teltonika AVL data to server"""
    
    print(f"Connecting to {host}:{port}")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((host, port))
        print(f"Connected to {host}:{port}")
        
        # Step 1: Send IMEI
        imei_data = b'\x00\x0F' + imei.encode('ascii')
        print(f"Sending IMEI: {imei}")
        print(f"Raw data: {binascii.hexlify(imei_data).decode().upper()}")
        client.send(imei_data)
        
        # Receive IMEI response
        response = client.recv(1)
        print(f"IMEI Response: {binascii.hexlify(response).decode().upper()}")
        
        if response == b'\x01':
            print("✅ IMEI accepted!")
            
            # Step 2: Send AVL data packet (Codec8)
            # Simplified packet with 2 GPS records
            timestamp = int(datetime.now().timestamp() * 1000)
            
            # Build AVL packet
            packet = bytearray()
            
            # Preamble (4 bytes - always zeros)
            packet.extend(b'\x00\x00\x00\x00')
            
            # Data field length (will be filled later)
            packet.extend(b'\x00\x00\x00\x00')
            
            # Codec ID
            packet.append(0x08)  # Codec8
            
            # Number of records
            packet.append(0x02)  # 2 records
            
            # Record 1
            packet.extend(struct.pack('>Q', timestamp))  # Timestamp
            packet.append(0x00)  # Priority
            packet.extend(struct.pack('>i', 253286750))  # Longitude (25.3286750)
            packet.extend(struct.pack('>i', 545735500))  # Latitude (54.5735500)
            packet.extend(struct.pack('>H', 123))  # Altitude
            packet.extend(struct.pack('>H', 180))  # Angle
            packet.append(0x05)  # Satellites
            packet.extend(struct.pack('>H', 42))  # Speed
            
            # I/O data for Record 1
            packet.append(0x01)  # Event IO ID
            packet.append(0x04)  # Total IO elements
            
            # 1-byte IOs
            packet.append(0x02)  # Count of 1-byte values
            packet.append(0x15)  # IO ID 21 (GSM Signal)
            packet.append(0x04)  # Value 4
            packet.append(0x01)  # IO ID 1 (Digital Input 1)  
            packet.append(0x01)  # Value 1
            
            # 2-byte IOs
            packet.append(0x01)  # Count of 2-byte values
            packet.append(0x42)  # IO ID 66 (External Voltage)
            packet.extend(struct.pack('>H', 12543))  # Value
            
            # 4-byte IOs
            packet.append(0x01)  # Count of 4-byte values
            packet.append(0xF1)  # IO ID 241 (Odometer)
            packet.extend(struct.pack('>I', 159648))  # Value
            
            # 8-byte IOs
            packet.append(0x00)  # No 8-byte values
            
            # Record 2 (5 seconds later)
            packet.extend(struct.pack('>Q', timestamp + 5000))  # Timestamp
            packet.append(0x00)  # Priority
            packet.extend(struct.pack('>i', 253287000))  # Longitude (moved slightly)
            packet.extend(struct.pack('>i', 545736000))  # Latitude (moved slightly)
            packet.extend(struct.pack('>H', 125))  # Altitude
            packet.extend(struct.pack('>H', 185))  # Angle
            packet.append(0x06)  # Satellites
            packet.extend(struct.pack('>H', 45))  # Speed
            
            # I/O data for Record 2
            packet.append(0x01)  # Event IO ID
            packet.append(0x02)  # Total IO elements
            
            # 1-byte IOs
            packet.append(0x01)  # Count of 1-byte values
            packet.append(0x15)  # IO ID 21 (GSM Signal)
            packet.append(0x05)  # Value 5
            
            # 2-byte IOs
            packet.append(0x01)  # Count of 2-byte values
            packet.append(0x42)  # IO ID 66 (External Voltage)
            packet.extend(struct.pack('>H', 12550))  # Value
            
            # 4-byte IOs
            packet.append(0x00)  # No 4-byte values
            
            # 8-byte IOs
            packet.append(0x00)  # No 8-byte values
            
            # Number of records at end
            packet.append(0x02)  # 2 records
            
            # CRC16 (simplified - just zeros)
            packet.extend(b'\x00\x00\x00\x00')
            
            # Update data field length at position 4-7
            data_length = len(packet) - 12  # Exclude preamble, length field, and CRC
            packet[4:8] = struct.pack('>I', data_length)
            
            print(f"\nSending AVL packet with 2 GPS records")
            print(f"Packet size: {len(packet)} bytes")
            print(f"Raw data: {binascii.hexlify(packet).decode().upper()[:100]}...")
            
            client.send(packet)
            
            # Receive ACK
            ack = client.recv(4)
            if len(ack) == 4:
                record_count = struct.unpack('>I', ack)[0]
                print(f"✅ Server acknowledged {record_count} records")
            else:
                print(f"Unexpected ACK: {binascii.hexlify(ack).decode().upper()}")
                
        else:
            print("❌ IMEI rejected!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        print("Connection closed")

if __name__ == "__main__":
    import sys
    
    # Default to localhost for testing
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 3030
    imei = sys.argv[3] if len(sys.argv) > 3 else "352093081452251"
    
    print(f"Teltonika AVL Test Client")
    print(f"Target: {host}:{port}")
    print(f"IMEI: {imei}")
    print("-" * 40)
    
    send_teltonika_data(host, port, imei)