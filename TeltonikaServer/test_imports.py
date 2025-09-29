#!/usr/bin/env python3
"""Test script to diagnose import issues"""

print("TEST: Starting import test...")

try:
    print("TEST: Importing standard libraries...")
    import socket
    import threading
    import os
    import glob
    import binascii
    import struct
    import json
    from datetime import datetime
    from http.server import HTTPServer, BaseHTTPRequestHandler
    print("TEST: Standard libraries OK")
except Exception as e:
    print(f"TEST ERROR: Standard library import failed: {e}")
    exit(1)

try:
    print("TEST: Importing teltonika_protocol...")
    import teltonika_protocol
    print("TEST: teltonika_protocol OK")
except Exception as e:
    print(f"TEST ERROR: teltonika_protocol import failed: {e}")
    exit(1)

try:
    print("TEST: Importing imei_registry...")
    import imei_registry
    print("TEST: imei_registry OK")
except Exception as e:
    print(f"TEST ERROR: imei_registry import failed: {e}")
    exit(1)

try:
    print("TEST: Importing tcp_server...")
    import tcp_server
    print("TEST: tcp_server OK")
except Exception as e:
    print(f"TEST ERROR: tcp_server import failed: {e}")
    exit(1)

try:
    print("TEST: Importing web_server...")
    import web_server
    print("TEST: web_server OK")
except Exception as e:
    print(f"TEST ERROR: web_server import failed: {e}")
    exit(1)

print("TEST: All imports successful!")
print("TEST: Testing main.py import...")

try:
    import main
    print("TEST: main.py import OK")
except Exception as e:
    print(f"TEST ERROR: main.py import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("TEST: Complete - all modules can be imported")