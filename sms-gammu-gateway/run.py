#!/usr/bin/env python3
"""
SMS Gammu Gateway - Home Assistant Add-on
REST API SMS Gateway using python-gammu for USB GSM modems

Based on: https://github.com/pajikos/sms-gammu-gateway
Licensed under Apache License 2.0
"""

import os
import json
import logging
import signal
import sys
from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from flask_restx import Api, Resource, fields, reqparse

from support import init_state_machine, retrieveAllSms, deleteSms, encodeSms
from mqtt_publisher import MQTTPublisher
from gammu import GSMNetworks

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
mqtt_logger = logging.getLogger('mqtt_publisher')
mqtt_logger.setLevel(logging.INFO)

# Suppress Flask development server warnings
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Monkey-patch click.echo to suppress Flask CLI startup messages
import click
_original_echo = click.echo
def _silent_echo(message=None, **kwargs):
    # Only suppress Flask's "Debug mode:" and "Serving Flask app" messages
    if message and isinstance(message, str):
        if 'Debug mode:' in message or 'Serving Flask app' in message:
            return
    _original_echo(message, **kwargs)
click.echo = _silent_echo

def load_version():
    """Load version from config.json"""
    try:
        # Try multiple possible locations
        possible_paths = [
            '/data/options.json',
            os.path.join(os.path.dirname(__file__), 'config.json'),
            '/config.json',
        ]

        # Try to read from addon info API first (most reliable in HA)
        try:
            import requests
            response = requests.get('http://supervisor/addons/self/info',
                                   headers={'Authorization': f'Bearer {os.environ.get("SUPERVISOR_TOKEN", "")}'},
                                   timeout=1)
            if response.status_code == 200:
                return response.json().get('data', {}).get('version', 'unknown')
        except:
            pass

        # Fallback: try to find config.json
        for config_path in possible_paths:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_json = json.load(f)
                    version = config_json.get('version')
                    if version:
                        return version

        return "unknown"
    except Exception as e:
        logging.warning(f"Could not read version: {e}")
        return "unknown"

def load_ha_config():
    """Load Home Assistant add-on configuration"""
    config_path = '/data/options.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # Default values for testing outside HA
        return {
            'device_path': '/dev/ttyUSB0',
            'pin': '',
            'port': 5000,
            'ssl': False,
            'username': 'admin',
            'password': 'password',
            'mqtt_enabled': True,
            'mqtt_host': 'localhost',
            'mqtt_port': 1883,
            'mqtt_username': '',
            'mqtt_password': '',
            'mqtt_topic_prefix': 'homeassistant/sensor/sms_gateway',
            'sms_monitoring_enabled': True,
            'sms_check_interval': 60,
            'sms_cost_per_message': 0.0,
            'sms_cost_currency': 'CZK',
            'auto_delete_read_sms': False
        }

# Load version and configuration
VERSION = load_version()
config = load_ha_config()
pin = config.get('pin') if config.get('pin') else None
ssl = config.get('ssl', False)
port = config.get('port', 5000)
username = config.get('username', 'admin')
password = config.get('password', 'password')
device_path = config.get('device_path', '/dev/ttyUSB0')

# Initialize MQTT publisher FIRST (before gammu)
mqtt_publisher = MQTTPublisher(config)

# Publish OFFLINE status immediately on startup (clears any stale "online" state)
if mqtt_publisher.connected:
    mqtt_publisher.device_tracker.initial_check_done = False  # Force offline
    mqtt_publisher.publish_device_status()
    logging.info("📡 Published initial OFFLINE status on startup")

# Now initialize gammu state machine (this may fail if modem not connected)
machine = init_state_machine(pin, device_path)

# Set gammu machine for MQTT SMS sending
mqtt_publisher.set_gammu_machine(machine)

# Setup signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals (SIGTERM, SIGINT)"""
    logging.info(f"🛑 Received shutdown signal {signum}, publishing offline status...")
    try:
        mqtt_publisher.disconnect()
        logging.info("✅ MQTT disconnected successfully")
    except Exception as e:
        logging.error(f"❌ Error during MQTT disconnect: {e}")
    finally:
        sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Register atexit handler as backup
import atexit
def cleanup():
    """Cleanup function called on normal exit"""
    logging.info("🧹 Cleanup: Publishing offline status...")
    try:
        mqtt_publisher.disconnect()
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")

atexit.register(cleanup)

app = Flask(__name__)

# Check if running under Ingress
import os
ingress_path = os.environ.get('INGRESS_PATH', '')

# Create simple HTML page for Ingress
@app.route('/')
def home():
    """Simple status page for Home Assistant Ingress"""
    from flask import Response, request
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SMS Gammu Gateway</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 40px 20px;
                background: #f5f5f5;
                text-align: center;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
                font-size: 2.2em;
            }
            .status {
                background: #e8f5e9;
                border: 2px solid #4caf50;
                padding: 20px;
                margin: 30px 0;
                border-radius: 10px;
                font-size: 1.2em;
            }
            .swagger-link {
                display: inline-block;
                padding: 15px 30px;
                background: #2196F3;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                margin: 20px 0;
                font-size: 1.1em;
                font-weight: bold;
            }
            .swagger-link:hover {
                background: #1976D2;
            }
            .info {
                background: #f0f8ff;
                border-left: 4px solid #2196F3;
                padding: 15px;
                margin: 20px 0;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📱 SMS Gammu Gateway</h1>
            
            <div class="status">
                <strong>✅ Gateway is running properly</strong><br>
                Version: {VERSION}
            </div>
            
            <a href="http://''' + request.host.split(':')[0] + ''':5000/docs/" 
               class="swagger-link" target="_blank">
                📋 Open Swagger API Documentation
            </a>
            
            <div class="info">
                <strong>REST API Endpoints:</strong><br>
                • GET /status/signal - Signal strength<br>
                • GET /status/network - Network information<br>
                • POST /sms - Send SMS (requires authentication)<br>
                • GET /sms - Get all SMS (requires authentication)<br>
                <br>
                <strong>Authentication in Swagger UI:</strong><br>
                1. Click the "Authorize" button 🔒 in the top right corner<br>
                2. Enter Username and Password from add-on configuration<br>
                3. Click "Authorize" - now you can test protected endpoints
            </div>
        </div>
    </body>
    </html>
    '''
    return Response(html.replace('{VERSION}', VERSION), mimetype='text/html')

# Swagger UI Configuration
# Put Swagger UI on /docs/ path for direct access via port 5000
api = Api(
    app,
    version=VERSION,
    title='SMS Gammu Gateway API',
    description='REST API for sending and receiving SMS messages via USB GSM modems (SIM800L, Huawei, etc.). Modern replacement for deprecated SMS notifications via GSM-modem integration.',
    doc='/docs/',  # Swagger UI on /docs/ path
    prefix='',
    authorizations={
        'basicAuth': {
            'type': 'basic',
            'in': 'header',
            'name': 'Authorization'
        }
    },
    security='basicAuth'
)

auth = HTTPBasicAuth()

@auth.verify_password
def verify(user, pwd):
    if not (user and pwd):
        return False
    return user == username and pwd == password

# API Models for Swagger documentation
sms_model = api.model('SMS', {
    'text': fields.String(required=True, description='SMS message text', example='Hello, how are you?'),
    'number': fields.String(required=True, description='Phone number (international format)', example='+420123456789'),
    'smsc': fields.String(required=False, description='SMS Center number (optional)', example='+420603052000'),
    'unicode': fields.Boolean(required=False, description='Use Unicode encoding', default=False),
    'flash': fields.Boolean(required=False, description='Send as Flash SMS (displays on screen, not saved)', default=False)
})

sms_response = api.model('SMS Response', {
    'Date': fields.String(description='Date and time received', example='2025-01-19 14:30:00'),
    'Number': fields.String(description='Sender phone number', example='+420123456789'),
    'State': fields.String(description='SMS state', example='UnRead'),
    'Text': fields.String(description='SMS message text', example='Hello World!')
})

signal_response = api.model('Signal Quality', {
    'SignalStrength': fields.Integer(description='Signal strength in dBm', example=-75),
    'SignalPercent': fields.Integer(description='Signal strength percentage', example=65),
    'BitErrorRate': fields.Integer(description='Bit error rate', example=-1)
})

network_response = api.model('Network Info', {
    'NetworkName': fields.String(description='Network operator name', example='T-Mobile'),
    'State': fields.String(description='Network registration state', example='HomeNetwork'),
    'NetworkCode': fields.String(description='Network operator code', example='230 01'),
    'CID': fields.String(description='Cell ID', example='0A1B2C3D'),
    'LAC': fields.String(description='Location Area Code', example='1234')
})

send_response = api.model('Send Response', {
    'status': fields.Integer(description='HTTP status code', example=200),
    'message': fields.String(description='Response message', example='[1]')
})

reset_response = api.model('Reset Response', {
    'status': fields.Integer(description='HTTP status code', example=200),
    'message': fields.String(description='Reset message', example='Reset done')
})

modem_info_response = api.model('Modem Info', {
    'IMEI': fields.String(description='Modem IMEI number', example='123456789012345'),
    'Manufacturer': fields.String(description='Modem manufacturer', example='Huawei'),
    'Model': fields.String(description='Modem model', example='E3372'),
    'Firmware': fields.String(description='Firmware version', example='22.323.62.00.143')
})

sim_info_response = api.model('SIM Info', {
    'IMSI': fields.String(description='SIM IMSI number', example='230011234567890')
})

sms_capacity_response = api.model('SMS Capacity', {
    'SIMUsed': fields.Integer(description='SMS count in SIM memory', example=5),
    'SIMSize': fields.Integer(description='SIM total capacity', example=50),
    'PhoneUsed': fields.Integer(description='SMS count in phone memory', example=0),
    'PhoneSize': fields.Integer(description='Phone memory capacity', example=100),
    'TemplatesUsed': fields.Integer(description='SMS templates used', example=0)
})

# API Namespaces
ns_sms = api.namespace('sms', description='SMS operations (requires authentication)')
ns_status = api.namespace('status', description='Device status and information (public)')

@ns_sms.route('')
@ns_sms.doc('sms_operations')
class SmsCollection(Resource):
    @ns_sms.doc('get_all_sms')
    @ns_sms.marshal_list_with(sms_response)
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def get(self):
        """Get all SMS messages from SIM/device memory"""
        allSms = mqtt_publisher.track_gammu_operation("retrieveAllSms", retrieveAllSms, machine)
        list(map(lambda sms: sms.pop("Locations", None), allSms))
        return allSms

    @ns_sms.doc('send_sms')
    @ns_sms.expect(sms_model)
    @ns_sms.marshal_with(send_response)
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def post(self):
        """Send SMS message(s)"""
        parser = reqparse.RequestParser()
        parser.add_argument('text', required=False, help='SMS message text')
        parser.add_argument('message', required=False, help='SMS message text (alias for text)')
        parser.add_argument('number', required=False, help='Phone number(s), comma separated')
        parser.add_argument('target', required=False, help='Phone number (alias for number)')
        parser.add_argument('smsc', required=False, help='SMS Center number (optional)')
        parser.add_argument('unicode', type=bool, required=False, default=False, help='Use Unicode encoding')
        parser.add_argument('flash', type=bool, required=False, default=False, help='Send as Flash SMS')
        
        args = parser.parse_args()
        
        # Support both 'text' and 'message' parameters
        sms_text = args.get('text') or args.get('message')
        if not sms_text:
            return {"status": 400, "message": "Missing required field: text or message"}, 400
        
        # Support both 'number' and 'target' parameters
        sms_number = args.get('number') or args.get('target')
        if not sms_number:
            return {"status": 400, "message": "Missing required field: number or target"}, 400

        # Determine SMS class based on flash parameter
        sms_class = 0 if args.get('flash', False) else -1

        smsinfo = {
            "Class": sms_class,
            "Unicode": args.get('unicode', False),
            "Entries": [
                {
                    "ID": "ConcatenatedTextLong",
                    "Buffer": sms_text,
                }
            ],
        }
        messages = []
        for number in sms_number.split(','):
            for message in encodeSms(smsinfo):
                message["SMSC"] = {'Number': args.get("smsc")} if args.get("smsc") else {'Location': 1}
                message["Number"] = number.strip()
                messages.append(message)

        try:
            result = [mqtt_publisher.track_gammu_operation("SendSMS", machine.SendSMS, message) for message in messages]

            # Increment SMS counter for each sent message
            for _ in messages:
                mqtt_publisher.sms_counter.increment()
            mqtt_publisher.publish_sms_counter()

            return {"status": 200, "message": str(result)}, 200

        except TimeoutError as e:
            # Modem timeout - service unavailable
            api.abort(503, f"Modem timeout: {str(e)}")

        except Exception as e:
            # Try to extract Gammu error details if available
            error_msg = str(e)

            # Parse Gammu error codes for user-friendly messages
            # Based on existing error handling pattern in mqtt_publisher.py
            if "Code': 49" in error_msg:
                # Can't access SIM card
                api.abort(503, "Cannot access SIM card - check SIM card status")
            elif "Code': 37" in error_msg:
                # ERR_BUG - protocol implementation error
                api.abort(503, "Modem protocol error - try again or restart modem")
            elif "Code': 27" in error_msg:
                # SMS sending failed
                api.abort(503, "SMS sending failed - check SIM card, network signal or device connection")
            elif "Code': 38" in error_msg:
                # Network registration failed
                api.abort(503, "Network registration failed - check SIM card and signal")
            elif "Code': 69" in error_msg:
                # SMSC number not found
                api.abort(503, "SMSC number not found - configure SMS center number in SIM settings")
            else:
                # Generic modem error
                api.abort(503, f"Failed to send SMS: {error_msg}")

@ns_sms.route('/<int:id>')
@ns_sms.doc('sms_by_id')
class SmsItem(Resource):
    @ns_sms.doc('get_sms_by_id')
    @ns_sms.marshal_with(sms_response)
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def get(self, id):
        """Get specific SMS by ID"""
        allSms = mqtt_publisher.track_gammu_operation("retrieveAllSms", retrieveAllSms, machine)
        if id < 0 or id >= len(allSms):
            api.abort(404, f"SMS with id '{id}' not found")
        sms = allSms[id]
        sms.pop("Locations", None)
        return sms

    @ns_sms.doc('delete_sms_by_id')
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def delete(self, id):
        """Delete SMS by ID"""
        allSms = mqtt_publisher.track_gammu_operation("retrieveAllSms", retrieveAllSms, machine)
        if id < 0 or id >= len(allSms):
            api.abort(404, f"SMS with id '{id}' not found")
        mqtt_publisher.track_gammu_operation("deleteSms", deleteSms, machine, allSms[id])
        return '', 204

@ns_sms.route('/getsms')
@ns_sms.doc('get_and_delete_first_sms')
class GetSms(Resource):
    @ns_sms.doc('pop_first_sms')
    @ns_sms.marshal_with(sms_response)
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def get(self):
        """Get first SMS and delete it from memory"""
        allSms = mqtt_publisher.track_gammu_operation("retrieveAllSms", retrieveAllSms, machine)
        sms = {"Date": "", "Number": "", "State": "", "Text": ""}
        if len(allSms) > 0:
            sms = allSms[0]
            mqtt_publisher.track_gammu_operation("deleteSms", deleteSms, machine, sms)
            sms.pop("Locations", None)
            # Publish to MQTT if enabled and SMS has content
            if sms.get("Text"):
                mqtt_publisher.publish_sms_received(sms)
        return sms

@ns_sms.route('/deleteall')
@ns_sms.doc('delete_all_sms')
class DeleteAllSms(Resource):
    @ns_sms.doc('delete_all_messages')
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def delete(self):
        """Delete all SMS messages from SIM/device memory"""
        allSms = mqtt_publisher.track_gammu_operation("retrieveAllSms", retrieveAllSms, machine)
        count = len(allSms)
        for sms in allSms:
            mqtt_publisher.track_gammu_operation("deleteSms", deleteSms, machine, sms)
        return {"status": 200, "message": f"Deleted {count} SMS messages"}, 200

@ns_status.route('/signal')
@ns_status.doc('get_signal_quality')
class Signal(Resource):
    @ns_status.doc('signal_strength')
    @ns_status.marshal_with(signal_response)
    def get(self):
        """Get GSM signal strength and quality"""
        signal_data = mqtt_publisher.track_gammu_operation("GetSignalQuality", machine.GetSignalQuality)
        # Publish to MQTT if enabled
        mqtt_publisher.publish_signal_strength(signal_data)
        return signal_data

@ns_status.route('/network')
@ns_status.doc('get_network_info')
class Network(Resource):
    @ns_status.doc('network_information')
    @ns_status.marshal_with(network_response)
    def get(self):
        """Get network operator and registration information"""
        network = mqtt_publisher.track_gammu_operation("GetNetworkInfo", machine.GetNetworkInfo)
        network["NetworkName"] = GSMNetworks.get(network.get("NetworkCode", ""), 'Unknown')
        # Publish to MQTT if enabled
        mqtt_publisher.publish_network_info(network)
        return network

@ns_status.route('/modem')
@ns_status.doc('get_modem_info')
class ModemInfo(Resource):
    @ns_status.doc('modem_information')
    @ns_status.marshal_with(modem_info_response)
    def get(self):
        """Get modem hardware information (IMEI, manufacturer, model, firmware)"""
        try:
            modem_info = {
                "IMEI": mqtt_publisher.track_gammu_operation("GetIMEI", machine.GetIMEI),
                "Manufacturer": mqtt_publisher.track_gammu_operation("GetManufacturer", machine.GetManufacturer),
                "Model": mqtt_publisher.track_gammu_operation("GetModel", machine.GetModel)
            }
            try:
                # Firmware can fail on some modems
                modem_info["Firmware"] = mqtt_publisher.track_gammu_operation("GetFirmware", machine.GetFirmware)[0]
            except:
                modem_info["Firmware"] = "Unknown"

            # Publish to MQTT if enabled
            mqtt_publisher.publish_modem_info(modem_info)
            return modem_info
        except Exception as e:
            api.abort(500, f"Failed to get modem info: {str(e)}")

@ns_status.route('/sim')
@ns_status.doc('get_sim_info')
class SimInfo(Resource):
    @ns_status.doc('sim_information')
    @ns_status.marshal_with(sim_info_response)
    def get(self):
        """Get SIM card information (IMSI)"""
        try:
            sim_info = {
                "IMSI": mqtt_publisher.track_gammu_operation("GetSIMIMSI", machine.GetSIMIMSI)
            }
            # Publish to MQTT if enabled
            mqtt_publisher.publish_sim_info(sim_info)
            return sim_info
        except Exception as e:
            api.abort(500, f"Failed to get SIM info: {str(e)}")

@ns_status.route('/sms_capacity')
@ns_status.doc('get_sms_capacity')
class SmsCapacity(Resource):
    @ns_status.doc('sms_storage_capacity')
    @ns_status.marshal_with(sms_capacity_response)
    def get(self):
        """Get SMS storage capacity and usage"""
        try:
            capacity = mqtt_publisher.track_gammu_operation("GetSMSStatus", machine.GetSMSStatus)
            # Publish to MQTT if enabled
            mqtt_publisher.publish_sms_capacity(capacity)
            return capacity
        except Exception as e:
            api.abort(500, f"Failed to get SMS capacity: {str(e)}")

@ns_status.route('/reset')
@ns_status.doc('reset_modem')
class Reset(Resource):
    @ns_status.doc('modem_reset')
    @ns_status.marshal_with(reset_response)
    def get(self):
        """Reset GSM modem (useful for stuck connections)"""
        mqtt_publisher.track_gammu_operation("Reset", machine.Reset, False)
        return {"status": 200, "message": "Reset done"}, 200

if __name__ == '__main__':
    print(f"🚀 SMS Gammu Gateway v{VERSION} started successfully!")
    print(f"📱 Device: {device_path}")
    print(f"🌐 API available on port {port}")
    print(f"🏠 Web UI: http://localhost:{port}/")
    print(f"🔒 SSL: {'Enabled' if ssl else 'Disabled'}")
    
    # MQTT info
    if config.get('mqtt_enabled', False):
        print(f"📡 MQTT: Enabled -> {config.get('mqtt_host')}:{config.get('mqtt_port')}")
        
        # Wait a moment for MQTT connection, then publish initial states
        import time
        time.sleep(2)
        mqtt_publisher.publish_initial_states_with_machine(machine)
        
        # Start periodic MQTT publishing
        mqtt_publisher.publish_status_periodic(machine, interval=300)  # 5 minutes
        
        # Start SMS monitoring if enabled
        if config.get('sms_monitoring_enabled', True):
            check_interval = config.get('sms_check_interval', 60)
            mqtt_publisher.start_sms_monitoring(machine, check_interval=check_interval)
            print(f"📱 SMS Monitoring: Enabled (check every {check_interval}s)")
        else:
            print(f"📱 SMS Monitoring: Disabled")
    else:
        print(f"📡 MQTT: Disabled")
    
    print(f"✅ Ready to send/receive SMS messages")

    try:
        if ssl:
            app.run(port=port, host="0.0.0.0", ssl_context=('/ssl/cert.pem', '/ssl/key.pem'),
                    debug=False, use_reloader=False)
        else:
            app.run(port=port, host="0.0.0.0", debug=False, use_reloader=False)
    finally:
        mqtt_publisher.disconnect()