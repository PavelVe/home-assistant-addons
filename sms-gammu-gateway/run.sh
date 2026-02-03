#!/usr/bin/with-contenv bashio

set -e

bashio::log.info "Starting SMS Gammu Gateway..."

# Check if device exists
DEVICE_PATH=$(bashio::config 'device_path')
if [ ! -c "${DEVICE_PATH}" ]; then
    bashio::log.warning "Device ${DEVICE_PATH} not found. Please check your GSM modem connection."
    bashio::log.info "Available tty devices:"
    ls -la /dev/tty* || true
fi

# Change to app directory
cd /app

# Start the application (unbuffered output for real-time logs)
exec python3 -u run.py