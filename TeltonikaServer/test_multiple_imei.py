#!/usr/bin/env python3
"""Test script with multiple different IMEI devices"""

import socket
import time
import binascii
import struct
from datetime import datetime

def create_gps_packet(imei, lat, lon, speed, altitude=200, angle=90):
    """Vytvoří AVL packet s GPS souřadnicemi"""
    
    # Převeď souřadnice
    latitude = int(lat * 10000000)
    longitude = int(lon * 10000000)
    
    # Současný čas
    current_time_ms = int(time.time() * 1000)
    
    print(f"Creating packet for IMEI {imei}:")
    print(f"  Latitude: {lat:.6f}° N")
    print(f"  Longitude: {lon:.6f}° E")
    print(f"  Speed: {speed} km/h")
    
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
    
    # AVL Record
    # Timestamp (8 bytes)
    packet.extend(struct.pack('>Q', current_time_ms))
    
    # Priority (1 byte)
    packet.append(0x01)
    
    # GPS Data (15 bytes)
    packet.extend(struct.pack('>i', longitude))  # Longitude (4 bytes)
    packet.extend(struct.pack('>i', latitude))   # Latitude (4 bytes)
    packet.extend(struct.pack('>H', altitude))   # Altitude (2 bytes)
    packet.extend(struct.pack('>H', angle))      # Angle (2 bytes)
    packet.append(8)                             # Satellites (1 byte)
    packet.extend(struct.pack('>H', speed))      # Speed (2 bytes)
    
    # I/O Elements
    packet.append(0x15)  # Event IO ID (GSM signal change)
    packet.append(0x03)  # Total I/O elements
    
    # 1-byte I/O elements
    packet.append(0x02)  # Count of 1-byte elements
    packet.append(0x15)  # GSM Signal
    packet.append(0x05)  # Value (5/5 signal strength)
    packet.append(0xEF)  # Ignition
    packet.append(0x01)  # Value (on)
    
    # 2-byte I/O elements  
    packet.append(0x01)  # Count of 2-byte elements
    packet.append(0x42)  # External voltage
    packet.extend(struct.pack('>H', 12800))  # 12.8V
    
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

def send_device_data(imei, lat, lon, speed, host="localhost", port=3030):
    """Pošle data z jednoho zařízení"""
    
    print(f"\n📱 Testing IMEI: {imei}")
    print(f"📍 Location: {lat:.6f}°N, {lon:.6f}°E")
    print(f"🏃 Speed: {speed} km/h")
    print("-" * 40)
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        print(f"✅ Connected to {host}:{port}")
        
        # IMEI handshake
        imei_hex = f"{len(imei):04X}{imei.encode('ascii').hex().upper()}"
        imei_data = bytes.fromhex(imei_hex)
        
        print(f"📡 Sending IMEI handshake: {imei}")
        client.send(imei_data)
        
        response = client.recv(1)
        if response == b'\x01':
            print("✅ IMEI accepted!")
            
            # Vytvoř a odešli GPS packet
            packet = create_gps_packet(imei, lat, lon, speed)
            
            print(f"📦 Sending GPS packet ({len(packet)} bytes)")
            client.send(packet)
            
            # Receive ACK
            try:
                client.settimeout(5.0)
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
            print("❌ IMEI rejected!")
            
    except Exception as e:
        print(f"💥 Error: {e}")
    finally:
        try:
            client.close()
        except:
            pass
        print("🔌 Connection closed")

def test_multiple_devices(host="localhost", port=3030):
    """Test s více různými zařízeními"""
    
    # Definice testovacích zařízení s různými lokacemi v ČR
    devices = [
        {
            "imei": "356307042441013",
            "location": "Brno", 
            "lat": 49.1951,
            "lon": 16.6068,
            "speed": 75
        },
        {
            "imei": "356307042441014", 
            "location": "Ostrava",
            "lat": 49.8209,
            "lon": 18.2625,
            "speed": 45
        },
        {
            "imei": "356307042441015",
            "location": "České Budějovice", 
            "lat": 48.9744,
            "lon": 14.4744,
            "speed": 60
        }
    ]
    
    print("🚗 Testing Multiple Teltonika Devices")
    print(f"🎯 Target server: {host}:{port}")
    print("=" * 60)
    
    for i, device in enumerate(devices, 1):
        print(f"\n🔄 Device {i}/{len(devices)}: {device['location']}")
        
        send_device_data(
            device['imei'],
            device['lat'], 
            device['lon'],
            device['speed'],
            host,
            port
        )
        
        # Krátká pauza mezi zařízeními
        if i < len(devices):
            print("\n⏳ Waiting 2 seconds before next device...")
            time.sleep(2)
    
    print(f"\n🎯 All {len(devices)} devices tested!")
    print("📊 Check web interface for new devices in device list")

if __name__ == "__main__":
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 3030
    
    test_multiple_devices(host, port)
    
    print("\n✨ Multi-device test completed!")