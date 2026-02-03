"""
SMS Gammu Gateway - Support functions
Gammu integration functions for SMS operations and state machine management

Based on: https://github.com/pajikos/sms-gammu-gateway
Licensed under Apache License 2.0
"""

import sys
import os
import logging
import gammu


def init_state_machine(pin, device_path='/dev/ttyUSB0'):
    """Initialize gammu state machine with HA add-on config"""
    sm = gammu.StateMachine()

    # Create gammu config dynamically
    config_content = f"""[gammu]
device = {device_path}
connection = at
commtimeout = 40
"""

    # Write config to temporary file
    config_file = '/tmp/gammu.config'
    with open(config_file, 'w') as f:
        f.write(config_content)

    sm.ReadConfig(Filename=config_file)
    
    try:
        sm.Init()
        logging.info(f"Successfully initialized gammu with device: {device_path}")

        # Try to check security status
        try:
            security_status = sm.GetSecurityStatus()
            logging.info(f"SIM security status: {security_status}")

            if security_status == 'PIN':
                if pin is None or pin == '':
                    logging.error("PIN is required but not provided.")
                    sys.exit(1)
                else:
                    sm.EnterSecurityCode('PIN', pin)
                    logging.info("PIN entered successfully")

        except Exception as e:
            logging.warning(f"Could not check SIM security status: {e}")

    except gammu.ERR_NOSIM:
        logging.warning("SIM card not accessible, but device is connected")
    except Exception as e:
        logging.error(f"Error initializing device: {e}")
        try:
            devices = [d for d in os.listdir('/dev/') if d.startswith('tty')]
            logging.info(f"Available devices: {', '.join([f'/dev/{d}' for d in sorted(devices)[:10]])}")
        except:
            pass
        raise
        
    return sm


def retrieveAllSms(machine):
    """Retrieve all SMS messages from SIM/device memory"""
    try:
        status = machine.GetSMSStatus()
        allMultiPartSmsCount = status['SIMUsed'] + status['PhoneUsed'] + status['TemplatesUsed']

        allMultiPartSms = []
        start = True

        while len(allMultiPartSms) < allMultiPartSmsCount:
            if start:
                currentMultiPartSms = machine.GetNextSMS(Start=True, Folder=0)
                start = False
            else:
                currentMultiPartSms = machine.GetNextSMS(Location=currentMultiPartSms[0]['Location'], Folder=0)
            allMultiPartSms.append(currentMultiPartSms)

        allSms = gammu.LinkSMS(allMultiPartSms)

        results = []
        for sms in allSms:
            smsPart = sms[0]

            result = {
                "Date": str(smsPart['DateTime']),
                "Number": smsPart['Number'],
                "State": smsPart['State'],
                "Locations": [smsPart['Location'] for smsPart in sms],
            }

            # Try to decode SMS - this may fail for MMS notifications or corrupted messages
            try:
                decodedSms = gammu.DecodeSMS(sms)
                if decodedSms == None:
                    # DecodeSMS returned None - use raw text from SMS part
                    result["Text"] = smsPart.get('Text', '')
                else:
                    # Successfully decoded - concatenate all text entries
                    text = ""
                    for entry in decodedSms['Entries']:
                        if entry.get('Buffer') is not None:
                            text += entry['Buffer']
                    result["Text"] = text if text else smsPart.get('Text', '')

            except UnicodeDecodeError as e:
                # MMS notification or binary message that can't be decoded as UTF-8
                logging.warning(f"Cannot decode SMS as UTF-8 (probably MMS notification): {e}")
                # Try to get raw text, but handle potential binary data safely
                try:
                    raw_text = smsPart.get('Text', '')
                    # If Text is bytes, try to decode with error handling
                    if isinstance(raw_text, bytes):
                        result["Text"] = raw_text.decode('utf-8', errors='replace')
                    else:
                        result["Text"] = str(raw_text) if raw_text else '[MMS or binary message]'
                except Exception:
                    result["Text"] = '[MMS or binary message - cannot display]'

            except Exception as e:
                # Any other decoding error (corrupted SMS, unknown format, etc.)
                logging.warning(f"Error decoding SMS: {e}")
                # Fallback to raw text with safe handling
                try:
                    raw_text = smsPart.get('Text', '')
                    if isinstance(raw_text, bytes):
                        result["Text"] = raw_text.decode('utf-8', errors='replace')
                    else:
                        result["Text"] = str(raw_text) if raw_text else '[Decoding error]'
                except Exception:
                    result["Text"] = '[Message decoding failed]'

            results.append(result)

        return results

    except Exception as e:
        logging.error(f"Error retrieving SMS: {e}")
        raise  # Re-raise exception so track_gammu_operation can detect failure


def deleteSms(machine, sms):
    """Delete SMS by location"""
    try:
        list(map(lambda location: machine.DeleteSMS(Folder=0, Location=location), sms["Locations"]))
    except Exception as e:
        logging.error(f"Error deleting SMS: {e}")


def encodeSms(smsinfo):
    """Encode SMS for sending"""
    return gammu.EncodeSMS(smsinfo)


def setupCallbacks(machine, unified_callback):
    """
    Nastaví callback pro příchozí hovory a SMS.
    Využívá Gammu SetIncomingCall, SetIncomingSMS a jeden společný SetIncomingCallback.

    Args:
        machine: Gammu state machine
        unified_callback: Callback funkce pro všechny události (sm, event_type, data)
                         event_type může být 'Call' nebo 'SMS'

    Returns: {'calls': bool, 'sms': bool} - co se podařilo nastavit
    """
    result = {'calls': False, 'sms': False}

    # Nastav společný callback pro všechny události
    try:
        machine.SetIncomingCallback(unified_callback)
        logging.info("📱 Unified callback: SetIncomingCallback registered")
    except Exception as e:
        logging.error(f"📱 SetIncomingCallback failed: {type(e).__name__}: {e}")
        return result

    # Povol Call notifikace (bez parametru podle dokumentace)
    try:
        machine.SetIncomingCall()
        result['calls'] = True
        logging.info("📞 Call notifications: ENABLED")
    except gammu.ERR_NOTSUPPORTED:
        logging.warning("📞 SetIncomingCall: Not supported by this modem")
    except Exception as e:
        logging.error(f"📞 SetIncomingCall failed: {type(e).__name__}: {e}")

    # Povol SMS notifikace (bez parametru podle dokumentace)
    try:
        machine.SetIncomingSMS()
        result['sms'] = True
        logging.info("📨 SMS notifications: ENABLED")
    except gammu.ERR_NOTSUPPORTED:
        logging.warning("📨 SetIncomingSMS: Not supported by this modem")
    except Exception as e:
        logging.error(f"📨 SetIncomingSMS failed: {type(e).__name__}: {e}")

    return result