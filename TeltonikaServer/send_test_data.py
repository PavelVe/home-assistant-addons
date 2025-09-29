#!/usr/bin/env python3
"""
Send test data from simple_packets.json to Teltonika server
Postupně odesílá testovací TCP pakety na server
"""

import socket
import json
import time
import sys
from datetime import datetime

def log_print(message):
    """Print s časovou značkou"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def send_hex_data(host, port, hex_data):
    """Pošle hex data na TCP server"""
    try:
        # Konverze hex stringu na bytes
        binary_data = bytes.fromhex(hex_data)
        
        # Vytvoř TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 sekund timeout
        
        # Připoj se k serveru
        log_print(f"Connecting to {host}:{port}")
        sock.connect((host, port))
        
        # Pošli data
        log_print(f"Sending {len(binary_data)} bytes of data: {hex_data[:50]}...")
        sock.send(binary_data)
        
        # Čekej na odpověď (pokud nějaká přijde)
        try:
            response = sock.recv(1024)
            if response:
                response_hex = response.hex().upper()
                log_print(f"Server response: {response_hex}")
            else:
                log_print("No response from server")
        except socket.timeout:
            log_print("No response from server (timeout)")
        
        sock.close()
        log_print("Connection closed")
        return True
        
    except Exception as e:
        log_print(f"Error sending data: {e}")
        return False

def send_teltonika_session(host, port, session_packets):
    """Pošle sekvenci paketů v jedné TCP session (IMEI + AVL data)"""
    try:
        # Vytvoř TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 sekund timeout
        
        # Připoj se k serveru
        log_print(f"Connecting to {host}:{port} for session with {len(session_packets)} packets")
        sock.connect((host, port))
        
        session_success = True
        
        # Pošli všechny pakety v této session
        for i, packet in enumerate(session_packets, 1):
            imei = packet.get('imei', 'unknown')
            hex_data = packet.get('data', '')
            
            # Konverze hex stringu na bytes
            binary_data = bytes.fromhex(hex_data)
            
            log_print(f"  Sending packet {i}/{len(session_packets)} (IMEI: {imei}): {hex_data[:50]}...")
            sock.send(binary_data)
            
            # Čekej na odpověď po každém paketu
            try:
                response = sock.recv(1024)
                if response:
                    response_hex = response.hex().upper()
                    log_print(f"  Server response: {response_hex}")
                else:
                    log_print(f"  No response from server for packet {i}")
            except socket.timeout:
                log_print(f"  No response from server (timeout) for packet {i}")
            
            # Krátká pauza mezi pakety v session
            if i < len(session_packets):
                time.sleep(0.5)
        
        sock.close()
        log_print(f"Session completed successfully with {len(session_packets)} packets")
        return True
        
    except Exception as e:
        log_print(f"Error in session: {e}")
        return False

def group_packets_by_session(packets):
    """Seskupí pakety do sessions podle Teltonika protokolu"""
    sessions = []
    current_session = []
    
    for packet in packets:
        hex_data = packet.get('data', '')
        
        # IMEI handshake pakety začínají s "000F" (15 bytes délka)
        # AVL data pakety začínají s "00000000" (codec8/8E header)
        if hex_data.startswith('000F'):
            # Začátek nové session s IMEI handshake
            if current_session:
                sessions.append(current_session)
            current_session = [packet]
        else:
            # AVL data paket - přidej do aktuální session
            if current_session:
                current_session.append(packet)
            else:
                log_print(f"Warning: AVL data packet without preceding IMEI handshake: {hex_data[:50]}")
    
    # Přidej poslední session
    if current_session:
        sessions.append(current_session)
    
    return sessions

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 send_test_data.py <host> <port>")
        print("Example: python3 send_test_data.py 192.168.1.16 3030")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    
    # Načti testovací data
    json_file = "test/simple_packets.json"
    try:
        with open(json_file, 'r') as f:
            test_packets = json.load(f)
    except Exception as e:
        log_print(f"Error reading {json_file}: {e}")
        sys.exit(1)
    
    log_print(f"Loaded {len(test_packets)} test packets from {json_file}")
    log_print(f"Target server: {host}:{port}")
    
    # Seskupí pakety do sessions
    sessions = group_packets_by_session(test_packets)
    log_print(f"Grouped into {len(sessions)} Teltonika sessions")
    
    log_print("Starting to send sessions...")
    
    # Pošli všechny sessions
    for i, session in enumerate(sessions, 1):
        log_print(f"--- Session {i}/{len(sessions)} ---")
        
        success = send_teltonika_session(host, port, session)
        
        if success:
            log_print(f"✅ Session {i} completed successfully")
        else:
            log_print(f"❌ Session {i} failed")
        
        # Pauza mezi sessions
        if i < len(sessions):
            log_print("Waiting 3 seconds before next session...")
            time.sleep(3)
    
    log_print("All sessions sent!")

if __name__ == "__main__":
    main()