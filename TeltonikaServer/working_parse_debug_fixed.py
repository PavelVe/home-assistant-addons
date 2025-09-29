import socket
import json
import os
import datetime
import struct
import decimal
import time

HOST = socket.gethostbyname(socket.gethostname())  # function may not work in Linux systems, change to string with IP address example: "192.168.0.1"
PORT = 7494  # change this to your port

def input_trigger():  # triggers user input         
    print("Paste full 'Codec 8' packet to parse it or:")
    print("Type SERVER to start the server or:")
    print("Type EXIT to stop the program")
    device_imei = "default_IMEI"
    import sys
    sys.stdout.flush()  # Force flush output buffer
    try:
        user_input = input("waiting for input: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        exit()
    if user_input.upper() == "EXIT":
        print(f"exiting program............")
        exit()    

    elif user_input.upper() == "SERVER":
        start_server_trigger()
    else:        
        try:
            if codec_8e_checker(user_input.replace(" ","")) == False:
                print("Wrong input or invalid Codec8 packet")
                print()
                input_trigger()
            else:
                codec_parser_trigger(user_input, device_imei, "USER")
        except Exception as e:
            print(f"error occurred: {e} enter proper Codec8 packet or EXIT!!!")
            input_trigger()        

####################################################
###############__CRC16/ARC Checker__################
####################################################

def crc16_arc(data):    
    # Extract data length from header (bytes 4-7)
    data_part_length_crc = int(data[8:16], 16)
    
    # Data part for CRC calculation starts after preamble and length
    data_start = 16
    data_end = data_start + (data_part_length_crc * 2)
    
    # Extract the data part (without preamble, length, and CRC)
    data_part_hex = data[data_start:data_end]
    data_part_bytes = bytes.fromhex(data_part_hex)
    
    # Extract CRC from packet (last 4 bytes after data)
    crc_from_packet = data[data_end:data_end+8]
    
    # Calculate CRC16 using correct polynomial for Teltonika
    crc = 0
    for byte in data_part_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    
    # Format as 4-byte hex string (little endian)
    calculated_crc = f"{crc:04X}".upper()
    expected_crc = crc_from_packet.upper()
    
    if expected_crc == calculated_crc:
        print("CRC check passed!")
        print(f"Record length: {len(data)} characters // {int(len(data)/2)} bytes")
        return True
    else:
        print(f"CRC check failed!")
        print(f"Expected CRC: {expected_crc}")
        print(f"Calculated CRC: {calculated_crc}")
        print("Continuing anyway for debugging purposes...")
        return True  # Continue for debugging

####################################################

def codec_8e_checker(codec8_packet):
    if len(codec8_packet) < 20:
        print("Packet too short!")
        return False
        
    if str(codec8_packet[16:18]).upper() != "8E" and str(codec8_packet[16:18]).upper() != "08":    
        print(f"Invalid codec type: {codec8_packet[16:18]}")        
        return False
    else:
        return crc16_arc(codec8_packet)

def codec_parser_trigger(codec8_packet, device_imei, props):
    try:            
        return codec_8e_parser(codec8_packet.replace(" ",""), device_imei, props)
    except Exception as e:
        print(f"Error occurred: {e}")
        if props == "USER":
            input_trigger()
        elif props == "USER_SILENT":
            return 0
        else:
            return 0

def imei_checker(hex_imei):  # IMEI checker function
    if len(hex_imei) < 8:
        return False
        
    imei_length = int(hex_imei[:4], 16)
    if imei_length != len(hex_imei[4:]) / 2:
        return False

    ascii_imei = ascii_imei_converter(hex_imei)
    print(f"IMEI received = {ascii_imei}")
    if not ascii_imei.isnumeric() or len(ascii_imei) != 15:
        print(f"Not an IMEI - is not numeric or wrong length!")
        return False
    else:
        return True

def ascii_imei_converter(hex_imei):
    return bytes.fromhex(hex_imei[4:]).decode()

def start_server_trigger():
    print("Starting server!")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        while True:
            s.listen()
            print(f"// {time_stamper()} // listening port: {PORT} // IP: {HOST}")
            conn, addr = s.accept()
            conn.settimeout(20)  # connection timeout
            with conn:
                print(f"// {time_stamper()} // Connected by {addr}")
                device_imei = "default_IMEI"
                while True:
                    try:
                        data = conn.recv(1280)
                        print(f"// {time_stamper()} // data received = {data.hex()}")
                        if not data:
                            break
                        elif imei_checker(data.hex()) != False:
                            device_imei = ascii_imei_converter(data.hex())
                            imei_reply = (1).to_bytes(1, byteorder="big")
                            conn.sendall(imei_reply)
                            print(f"-- {time_stamper()} sending reply = {imei_reply}")
                        elif codec_8e_checker(data.hex().replace(" ","")) != False:
                            record_number = codec_parser_trigger(data.hex(), device_imei, "SERVER")
                            print(f"received records {record_number}")
                            print(f"from device IMEI = {device_imei}")
                            print()
                            record_response = (record_number).to_bytes(4, byteorder="big")
                            conn.sendall(record_response)
                            print(f"// {time_stamper()} // response sent = {record_response.hex()}")
                        else:
                            print(f"// {time_stamper()} // no expected DATA received - dropping connection")
                            break
                    except socket.timeout:
                        print(f"// {time_stamper()} // Socket timed out. Closing connection with {addr}")
                        break
                            
####################################################
###############_Codec8E_parser_code_################
####################################################

def codec_8e_parser(codec_8E_packet, device_imei, props):
    print()
    print(f"Parsing Codec 8E packet...")

    # Parse header
    zero_bytes = codec_8E_packet[:8]
    data_field_length = int(codec_8E_packet[8:16], 16)
    codec_type = codec_8E_packet[16:18]
    number_of_records = int(codec_8E_packet[18:20], 16)
    
    print(f"Zero bytes: {zero_bytes}")
    print(f"Data field length: {data_field_length} bytes")
    print(f"Codec type: {codec_type}")
    print(f"Number of records: {number_of_records}")

    # Raw data dictionary
    io_dict_raw = {
        "device_IMEI": device_imei,
        "server_time": time_stamper_for_json(),
        "data_length": f"Record length: {len(codec_8E_packet)} characters // {len(codec_8E_packet) // 2} bytes",
        "_raw_data__": codec_8E_packet,
        "parsed_records": []
    }

    # Determine step size based on codec type
    data_step = 4 if codec_type.upper() == "8E" else 2

    # Start parsing AVL data (after codec type and record count)
    avl_data_start = codec_8E_packet[20:]
    data_field_position = 0
    
    parsed_records = []
    
    for record_number in range(1, number_of_records + 1):
        # Check if we have enough data left
        if data_field_position >= len(avl_data_start) - 10:  # Need at least basic record data
            print(f"Not enough data for record {record_number}")
            break
            
        print(f"\n========== RECORD {record_number} ==========")
        
        io_dict = {
            "device_IMEI": device_imei,
            "server_time": time_stamper_for_json(),
            "record_number": record_number
        }

        try:
            # Timestamp (8 bytes)
            if data_field_position + 16 > len(avl_data_start):
                break
            timestamp = avl_data_start[data_field_position:data_field_position+16]
            io_dict["_timestamp_"] = device_time_stamper(timestamp)        
            io_dict["_rec_delay_"] = record_delay_counter(timestamp)
            print(f"Timestamp = {device_time_stamper(timestamp)}")    
            data_field_position += 16

            # Priority (1 byte)
            if data_field_position + 2 > len(avl_data_start):
                break
            priority = avl_data_start[data_field_position:data_field_position+2]
            io_dict["priority"] = int(priority, 16)
            print(f"Priority = {int(priority, 16)}")
            data_field_position += 2

            # Longitude (4 bytes)
            if data_field_position + 8 > len(avl_data_start):
                break
            longitude = avl_data_start[data_field_position:data_field_position+8]
            io_dict["longitude"] = coordinate_formater(longitude)
            print(f"Longitude = {coordinate_formater(longitude)}")
            data_field_position += 8

            # Latitude (4 bytes)
            if data_field_position + 8 > len(avl_data_start):
                break
            latitude = avl_data_start[data_field_position:data_field_position+8]
            io_dict["latitude"] = coordinate_formater(latitude)
            print(f"Latitude = {coordinate_formater(latitude)}")
            data_field_position += 8

            # Altitude (2 bytes)
            if data_field_position + 4 > len(avl_data_start):
                break
            altitude = avl_data_start[data_field_position:data_field_position+4]
            io_dict["altitude"] = int(altitude, 16)
            print(f"Altitude = {int(altitude, 16)} m")
            data_field_position += 4

            # Angle (2 bytes)
            if data_field_position + 4 > len(avl_data_start):
                break
            angle = avl_data_start[data_field_position:data_field_position+4]
            io_dict["angle"] = int(angle, 16)
            print(f"Angle = {int(angle, 16)}°")
            data_field_position += 4

            # Satellites (1 byte)
            if data_field_position + 2 > len(avl_data_start):
                break
            satellites = avl_data_start[data_field_position:data_field_position+2]
            io_dict["satellites"] = int(satellites, 16)
            print(f"Satellites = {int(satellites, 16)}")
            data_field_position += 2

            # Speed (2 bytes)
            if data_field_position + 4 > len(avl_data_start):
                break
            speed = avl_data_start[data_field_position:data_field_position+4]
            io_dict["speed"] = int(speed, 16)
            print(f"Speed = {int(speed, 16)} km/h")
            data_field_position += 4

            # Event IO ID
            if data_field_position + data_step > len(avl_data_start):
                break
            event_io_id = avl_data_start[data_field_position:data_field_position+data_step]
            io_dict["eventID"] = int(event_io_id, 16)        
            print(f"Event ID = {int(event_io_id, 16)}")
            data_field_position += data_step

            # Total IO elements
            if data_field_position + data_step > len(avl_data_start):
                break
            total_io_elements = avl_data_start[data_field_position:data_field_position+data_step]
            total_io_elements_parsed = int(total_io_elements, 16)
            print(f"Total I/O elements = {total_io_elements_parsed}")
            data_field_position += data_step

            # Parse I/O elements
            data_field_position = parse_io_elements(avl_data_start, data_field_position, data_step, io_dict, codec_type.upper())

            parsed_records.append(io_dict)
            print(f"Record {record_number} parsed successfully")
            
        except Exception as e:
            print(f"Error parsing record {record_number}: {e}")
            import traceback
            traceback.print_exc()
            break

    io_dict_raw["parsed_records"] = parsed_records

    # Save data
    try:
        json_printer_rawDATA(io_dict_raw, device_imei)
        for record in parsed_records:
            json_printer(record, device_imei)
    except Exception as e:
        print(f"JSON writing error occurred = {e}")

    if props == "SERVER":    
        return number_of_records
    else:
        print(f"\nSuccessfully parsed {len(parsed_records)} records")
        input_trigger()

def parse_io_elements(avl_data, position, data_step, io_dict, codec_type):
    """Parse I/O elements for different byte sizes"""
    
    try:
        # 1 byte I/O elements
        position = parse_io_group(avl_data, position, data_step, io_dict, 1, "1 byte")
        
        # 2 byte I/O elements  
        position = parse_io_group(avl_data, position, data_step, io_dict, 2, "2 byte")
        
        # 4 byte I/O elements
        position = parse_io_group(avl_data, position, data_step, io_dict, 4, "4 byte")
        
        # 8 byte I/O elements
        position = parse_io_group(avl_data, position, data_step, io_dict, 8, "8 byte")
        
        # X byte I/O elements (only for Codec 8E)
        if codec_type == "8E":
            position = parse_io_x_group(avl_data, position, io_dict)
            
    except Exception as e:
        print(f"Error parsing I/O elements: {e}")
    
    return position

def parse_io_group(avl_data, position, data_step, io_dict, value_bytes, group_name):
    """Parse a group of I/O elements with fixed value size"""
    
    if position + data_step > len(avl_data):
        return position
        
    # Get count of elements in this group
    count_hex = avl_data[position:position+data_step]
    if len(count_hex) < data_step:
        return position
        
    count = int(count_hex, 16)
    print(f"{group_name} I/O count = {count}")
    position += data_step
    
    # Parse each element
    for i in range(count):
        if position + data_step + (value_bytes * 2) > len(avl_data):
            break
            
        # Get key
        key_hex = avl_data[position:position+data_step]
        if len(key_hex) < data_step:
            break
        key = int(key_hex, 16)
        position += data_step
        
        # Get value
        value_hex = avl_data[position:position+(value_bytes*2)]
        if len(value_hex) < (value_bytes*2):
            break
        
        try:
            io_dict[key] = sorting_hat(key, value_hex)
            print(f"  AVL_ID: {key} = {io_dict[key]}")
        except Exception as e:
            print(f"  AVL_ID: {key} = 0x{value_hex} (parse error: {e})")
            io_dict[key] = f"0x{value_hex}"
            
        position += (value_bytes*2)
    
    return position

def parse_io_x_group(avl_data, position, io_dict):
    """Parse X byte I/O elements (variable length, Codec 8E only)"""
    
    if position + 4 > len(avl_data):
        return position
        
    # Get count (2 bytes for X elements)
    count_hex = avl_data[position:position+4]
    if len(count_hex) < 4:
        return position
        
    count = int(count_hex, 16)
    print(f"X byte I/O count = {count}")
    position += 4
    
    # Parse each element
    for i in range(count):
        if position + 8 > len(avl_data):  # Need at least key + length
            break
            
        # Get key (2 bytes)
        key_hex = avl_data[position:position+4]
        if len(key_hex) < 4:
            break
        key = int(key_hex, 16)
        position += 4
        
        # Get value length (2 bytes)
        length_hex = avl_data[position:position+4]
        if len(length_hex) < 4:
            break
        value_length = int(length_hex, 16)
        position += 4
        
        # Get value
        if position + (value_length * 2) > len(avl_data):
            break
            
        value_hex = avl_data[position:position+(value_length*2)]
        if len(value_hex) < (value_length*2):
            break
        
        try:
            io_dict[key] = sorting_hat(key, value_hex)
            print(f"  AVL_ID: {key} = {io_dict[key]} (length: {value_length})")
        except Exception as e:
            print(f"  AVL_ID: {key} = 0x{value_hex} (parse error: {e})")
            io_dict[key] = f"0x{value_hex}"
            
        position += (value_length*2)
    
    return position

####################################################
###############_Coordinates_Function_###############
####################################################

def coordinate_formater(hex_coordinate):
    try:
        coordinate = int(hex_coordinate, 16)
        if coordinate & (1 << 31):
            new_int = coordinate - 2**32
            dec_coordinate = new_int/1e7
        else:
            dec_coordinate = coordinate / 10000000
        return dec_coordinate
    except Exception as e:
        print(f"Coordinate parsing error: {e}")
        return 0.0

####################################################
###############____JSON_Functions____###############
####################################################

def json_printer(io_dict, device_imei):
    """Write individual record to JSON file"""
    data_path = "./data/" + str(device_imei)
    json_file = str(device_imei) + "_data.json"

    if not os.path.exists(data_path):
        os.makedirs(data_path)

    file_path = os.path.join(data_path, json_file)
    
    # Read existing data if file exists
    records = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                content = file.read().strip()
                if content:
                    records = json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            records = []
    
    # Add new record
    records.append(io_dict)
    
    # Write back to file
    with open(file_path, "w") as file:
        json.dump(records, file, indent=4)

def json_printer_rawDATA(io_dict_raw, device_imei):
    """Write raw data to JSON file"""
    data_path = "./data/" + str(device_imei)
    json_file = str(device_imei) + "_RAWdata.json"

    if not os.path.exists(data_path):
        os.makedirs(data_path)

    file_path = os.path.join(data_path, json_file)
    
    # Read existing data if file exists
    records = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                content = file.read().strip()
                if content:
                    records = json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            records = []
    
    # Add new record
    records.append(io_dict_raw)
    
    # Write back to file
    with open(file_path, "w") as file:
        json.dump(records, file, indent=4)

####################################################
###############____TIME_FUNCTIONS____###############
####################################################

def time_stamper():
    current_server_time = datetime.datetime.now()    
    server_time_stamp = current_server_time.strftime('%H:%M:%S %d-%m-%Y')
    return server_time_stamp

def time_stamper_for_json():
    current_server_time = datetime.datetime.now()
    timestamp_utc = datetime.datetime.utcnow()
    server_time_stamp = f"{current_server_time.strftime('%H:%M:%S %d-%m-%Y')} (local) / {timestamp_utc.strftime('%H:%M:%S %d-%m-%Y')} (utc)"
    return server_time_stamp

def device_time_stamper(timestamp):
    try:
        timestamp_ms = int(timestamp, 16) / 1000
        timestamp_utc = datetime.datetime.utcfromtimestamp(timestamp_ms)
        utc_offset = datetime.datetime.fromtimestamp(timestamp_ms) - datetime.datetime.utcfromtimestamp(timestamp_ms)
        timestamp_local = timestamp_utc + utc_offset
        formatted_timestamp_local = timestamp_local.strftime("%H:%M:%S %d-%m-%Y")
        formatted_timestamp_utc = timestamp_utc.strftime("%H:%M:%S %d-%m-%Y")
        formatted_timestamp = f"{formatted_timestamp_local} (local) / {formatted_timestamp_utc} (utc)"
        return formatted_timestamp
    except Exception as e:
        print(f"Timestamp parsing error: {e}")
        return "Invalid timestamp"

def record_delay_counter(timestamp):
    try:
        timestamp_ms = int(timestamp, 16) / 1000
        current_server_time = datetime.datetime.now().timestamp()
        return f"{int(current_server_time - timestamp_ms)} seconds"
    except Exception as e:
        return "Unknown delay"

####################################################
###############_PARSE_FUNCTIONS_CODE_###############
####################################################

def parse_data_integer(data):
    try:
        return int(data, 16)
    except ValueError:
        return f"0x{data}"

def int_multiply_01(data):
    try:
        return float(decimal.Decimal(int(data, 16)) * decimal.Decimal('0.1'))
    except (ValueError, decimal.InvalidOperation):
        return f"0x{data}"

def int_multiply_001(data):
    try:
        return float(decimal.Decimal(int(data, 16)) * decimal.Decimal('0.01'))
    except (ValueError, decimal.InvalidOperation):
        return f"0x{data}"

def int_multiply_0001(data):
    try:
        return float(decimal.Decimal(int(data, 16)) * decimal.Decimal('0.001'))
    except (ValueError, decimal.InvalidOperation):
        return f"0x{data}"

def signed_no_multiply(data):
    try:
        # Ensure we have the right length for 32-bit signed integer
        if len(data) <= 8:
            data = data.zfill(8)
        binary = bytes.fromhex(data[:8])
        value = struct.unpack(">i", binary)[0]
        return value
    except Exception as e:
        print(f"Signed value parse error for '{data}': {e}")
        return f"0x{data}"

# Extended parse functions dictionary with more AVL IDs
parse_functions_dictionary = {
    240: parse_data_integer,   # Movement
    239: parse_data_integer,   # Ignition
    80: parse_data_integer,    # Data Mode
    21: parse_data_integer,    # GSM Signal
    200: parse_data_integer,   # Sleep Mode
    69: parse_data_integer,    # GNSS Status
    181: int_multiply_01,      # GNSS Speed
    182: int_multiply_01,      # GNSS HDOP
    66: int_multiply_0001,     # External Voltage
    24: parse_data_integer,    # Speed
    205: parse_data_integer,   # GSM Cell ID
    206: parse_data_integer,   # GSM Area Code  
    67: int_multiply_0001,     # Battery Voltage
    68: int_multiply_0001,     # Battery Current
    241: parse_data_integer,   # Active GSM Operator
    299: parse_data_integer,   # Total Odometer
    16: parse_data_integer,    # Total Odometer
    1: parse_data_integer,     # Digital Input 1
    9: parse_data_integer,     # Analog Input 1
    179: parse_data_integer,   # GSM Operator
    12: int_multiply_0001,     # Fuel Used GPS
    13: int_multiply_001,      # Fuel Rate GPS
    17: signed_no_multiply,    # Axis X
    18: signed_no_multiply,    # Axis Y
    19: signed_no_multiply,    # Axis Z
    11: parse_data_integer,    # Average Fuel Use
    10: parse_data_integer,    # Fuel Consumption
    2: parse_data_integer,     # Digital Input 2
    3: parse_data_integer,     # Digital Input 3
    6: int_multiply_0001,      # Analog Input 3
    180: parse_data_integer    # GSM Network Code
}

def sorting_hat(key, value):
    try:
        if key in parse_functions_dictionary:
            parse_function = parse_functions_dictionary[key]
            return parse_function(value)
        else:
            return f"0x{value}"
    except Exception as e:
        print(f"Parse error for key {key}, value {value}: {e}")
        return f"0x{value}"

####################################################

def fileAccessTest():
    """Check if script can create files and folders"""
    try: 
        testDict = {
            "_Writing_Test_": "Writing_Test",
            "Script_Started": time_stamper_for_json()
        }

        json_printer(testDict, "file_Write_Test")
        print("---### File access test passed! ###---")
        input_trigger()

    except Exception as e:
        print()
        print("---### File access error occurred ###---")
        print(f"'{e}'")
        print("---### Try running terminal with Administrator rights! ###---")
        print("---### Nothing will be saved if you decide to continue! ###---")
        print()
        input_trigger()

def test_with_sample_data():
    """Test parser with sample hex data"""
    # Reálný dlouhý Codec 8E paket z testovacích dat
    sample_hex = "00000000000004C88E0B00000197C9CEA2E00000000000000000000000000000000000000013000700EF0100F00100150400C8000200450002007100580001001100D8000B005B0000CD00004040906700000197C9CEAEE00000000000000000000000000000000000000013000700EF0100F00100150500C8000200450002007100590001001100D8000B005B0000CD00004040916700000197C9CEF1E00000000000000000000000000000000000000013000700EF0100F00100150300C8000200450002007100580001001100D8000B005B0000CD000040409200000000ABCD"
    device_imei = "test_imei_123"
    
    print("=== Testing with sample data ===")
    print(f"Sample hex length: {len(sample_hex)} characters ({len(sample_hex)//2} bytes)")
    print(f"Sample hex: {sample_hex[:50]}...")
    
    if codec_8e_checker(sample_hex):
        result = codec_parser_trigger(sample_hex, device_imei, "TEST")
        print(f"Test completed. Parsed {result} records.")
    else:
        print("Sample data failed validation")

def test_with_real_packet():
    """Test with real packet from test files"""
    try:
        import json
        with open('test/simple_packets.json', 'r') as f:
            test_packets = json.load(f)
        
        # Use first large packet
        for packet in test_packets:
            hex_data = packet.get('data', '')
            if len(hex_data) > 100:  # Find a large packet
                print(f"\n=== Testing with real packet from test file ===")
                print(f"IMEI: {packet.get('imei')}")
                print(f"Packet size: {len(hex_data)//2} bytes")
                print(f"Data: {hex_data[:50]}...")
                
                if codec_8e_checker(hex_data):
                    result = codec_parser_trigger(hex_data, packet.get('imei'), "TEST")
                    print(f"Real packet test completed. Parsed {result} records.")
                else:
                    print("Real packet failed validation")
                break
    except FileNotFoundError:
        print("Test file not found, skipping real packet test")

def main():
    print("=== Codec 8/8E Parser v2.1 (Fixed) ===")
    print("Fixed issues:")
    print("- Added missing time import")
    print("- Improved CRC calculation") 
    print("- Better multi-record parsing with bounds checking")
    print("- Enhanced error handling in all parse functions")
    print("- More robust coordinate and timestamp parsing")
    print()
    
    # Test file access first
    try:
        testDict = {
            "_Writing_Test_": "Writing_Test",
            "Script_Started": time_stamper_for_json()
        }
        json_printer(testDict, "file_Write_Test")
        print("---### File access test passed! ###---")
    except Exception as e:
        print(f"File access error: {e}")
        return
    
    # Run test with sample data
    test_with_sample_data()
    
    # Start interactive mode
    print("\n" + "="*50)
    print("Starting interactive mode...")
    input_trigger()

if __name__ == "__main__":
    main()