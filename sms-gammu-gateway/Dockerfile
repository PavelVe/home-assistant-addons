ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base:3.19
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install system dependencies required for gammu and python-gammu
RUN apk update \
    && apk add --no-cache \
        python3 \
        python3-dev \
        py3-pip \
        pkgconfig \
        gammu \
        gammu-dev \
        libffi-dev \
        gcc \
        musl-dev \
        linux-headers \
        usb-modeswitch \
        usb-modeswitch-udev \
    && rm -rf /var/cache/apk/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

# Copy application files
COPY run.py .
COPY support.py .
COPY mqtt_publisher.py .
COPY config.json .
COPY run.sh .
COPY icon.png .
COPY services.yaml .

# Make run script executable
RUN chmod +x run.sh

# Expose port
EXPOSE 5000

# Labels
LABEL \
    io.hass.name="SMS Gammu Gateway" \
    io.hass.description="REST API SMS Gateway using python-gammu for USB GSM modems" \
    io.hass.type="addon" \
    io.hass.version="1.2.9" \
    maintainer="PavelVe"

# Run
CMD [ "./run.sh" ]