ARG BUILD_FROM
FROM $BUILD_FROM

# Install pytz for timezone support
RUN apk add --no-cache py3-pip python3-dev && \
    pip3 install pytz

RUN mkdir -p /data

WORKDIR /app

COPY main.py tcp_server.py web_server.py teltonika_protocol.py imei_registry.py csv_logger.py buffer_manager.py run.sh ./

RUN chmod +x run.sh

CMD ["/app/run.sh"]
