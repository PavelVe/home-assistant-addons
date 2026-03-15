ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base:3.19
FROM $BUILD_FROM

RUN apk add --no-cache minidlna wget

RUN mkdir -p /data/db

COPY run.sh /
RUN chmod +x /run.sh

COPY icons/lrg.png /usr/share/minidlna/icons/lrg.png
COPY icons/sm.png /usr/share/minidlna/icons/sm.png
COPY icons/lrg.jpg /usr/share/minidlna/icons/lrg.jpg
COPY icons/sm.jpg /usr/share/minidlna/icons/sm.jpg

EXPOSE 8200

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://localhost:8200 || exit 1

LABEL \
    io.hass.name="MiniDLNA" \
    io.hass.description="DLNA/UPnP media server (ReadyMedia)" \
    io.hass.type="addon" \
    io.hass.version="1.0.0" \
    maintainer="PavelVe"

CMD ["/run.sh"]
