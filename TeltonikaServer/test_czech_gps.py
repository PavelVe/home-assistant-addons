#!/usr/bin/env python3
"""Test script with realistic Czech GPS coordinates"""

import socket
import time
import binascii
import struct
from datetime import datetime

def create_czech_gps_packet():
    """Vytvoří AVL packet s GPS souřadnicemi pro ČR"""
    
    # Reálné souřadnice z ČR (Praha)
    # 50.0755° N, 14.4378° E
    latitude = int(50.0755 * 10000000)   # 500755000
    longitude = int(14.4378 * 10000000)  # 144378000
    
    # Současný čas
    current_time_ms = int(time.time() * 1000)
    
    print(f"Creating packet with Czech coordinates:")
    print(f"  Latitude: {latitude/10000000.0:.6f}° N (Praha)")
    print(f"  Longitude: {longitude/10000000.0:.6f}° E (Praha)")
    print(f"  Timestamp: {datetime.fromtimestamp(current_time_ms/1000)}")
    
    # Sestavení AVL packetu
    packet = bytearray()
    
    # Preamble (4 bytes)
    packet.extend(b'\x00\x00\x00\x00')
    
    # Data length placeholder (4 bytes) - vyplní se později
    data_start = len(packet)
    packet.extend(b'\x00\x00\x00\x00')
    
    # Codec 8 Extended
    packet.append(0x8E)
    
    # Počet záznamů
    packet.append(0x01)
    
    # AVL Record 1
    # Timestamp (8 bytes)
    packet.extend(struct.pack('>Q', current_time_ms))
    
    # Priority (1 byte)
    packet.append(0x01)
    
    # GPS Data (15 bytes)
    packet.extend(struct.pack('>i', longitude))  # Longitude (4 bytes)
    packet.extend(struct.pack('>i', latitude))   # Latitude (4 bytes)
    packet.extend(struct.pack('>H', 250))        # Altitude (2 bytes) - 250m
    packet.extend(struct.pack('>H', 45))         # Angle (2 bytes) - 45°
    packet.append(8)                             # Satellites (1 byte)
    packet.extend(struct.pack('>H', 50))         # Speed (2 bytes) - 50 km/h
    
    # I/O Elements
    packet.append(0x15)  # Event IO ID (GSM signal change)
    packet.append(0x03)  # Total I/O elements
    
    # 1-byte I/O elements
    packet.append(0x02)  # Count of 1-byte elements
    packet.append(0x15)  # GSM Signal
    packet.append(0x04)  # Value (4/5 signal strength)
    packet.append(0xEF)  # Ignition
    packet.append(0x01)  # Value (on)
    
    # 2-byte I/O elements  
    packet.append(0x01)  # Count of 2-byte elements
    packet.append(0x42)  # External voltage
    packet.extend(struct.pack('>H', 12500))  # 12.5V
    
    # 4-byte and 8-byte I/O elements
    packet.append(0x00)  # Count of 4-byte elements
    packet.append(0x00)  # Count of 8-byte elements
    
    # Number of records at end
    packet.append(0x01)
    
    # CRC-16 (4 bytes) - simplified, just add zeros
    packet.extend(b'\x00\x00\x00\x00')
    
    # Update data length
    data_length = len(packet) - data_start - 8  # Exclude preamble, length field, and CRC
    packet[data_start:data_start+4] = struct.pack('>I', data_length)
    
    return packet

def test_czech_gps(host="localhost", port=3030):
    """Test s českými GPS souřadnicemi"""
    
    imei = "350317176700155"
    
    print(f"🇨🇿 Testing Czech GPS Coordinates")
    print(f"Target: {host}:{port}")
    print(f"IMEI: {imei}")
    print("-" * 50)
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        print(f"✅ Connected to {host}:{port}")
        
        # IMEI handshake
        imei_hex = "000F333530333137313736373030313535"
        imei_data = bytes.fromhex(imei_hex)
        
        print(f"\\n📡 Sending IMEI handshake...")
        client.send(imei_data)
        
        response = client.recv(1)
        if response == b'\x01':
            print("✅ IMEI accepted!")
            
            # Vytvoř a odešli packet s českými GPS souřadnicemi
            packet = create_czech_gps_packet()
            
            print(f"\\n📦 Sending Czech GPS Packet")
            print(f"Size: {len(packet)} bytes")
            
            client.send(packet)
            
            # Receive ACK
            try:
                client.settimeout(5.0)
                ack = client.recv(4)
                if len(ack) == 4:
                    record_count = struct.unpack('>I', ack)[0]
                    print(f"✅ Server ACK: {record_count} records processed")
                    if record_count == 1:
                        print("🎯 Perfektní! Český GPS záznam byl zpracován!")
                        print("📍 Zkontrolujte CSV log - měly by tam být souřadnice Prahy")
                    else:
                        print(f"⚠️ Expected 1 record, got {record_count}")
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
    
    print("🚀 Starting Czech GPS Test")
    print(f"Target server: {host}:{port}")
    print("=" * 60)
    
    test_czech_gps(host, port)
    
    print("\\n✨ Test completed!")