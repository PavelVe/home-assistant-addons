"""
SMS Gammu Gateway - URC filter proxy

Některé GSM moduly (typicky SIMCOM SIM800/SIM800C) opakovaně chrlí
asynchronní URC zprávy o napájení (např. "OVER-VOLTAGE WARNNING").
Tyto řádky se mísí do odpovědí na AT příkazy a zasekávají parser
v libgammu (operace pak vyprší timeoutem a modem se jeví jako mrtvý).

Tento modul vkládá mezi reálný sériový port modemu a gammu tenkou
proxy postavenou na pseudo-terminálu (pty):

    modem (/dev/ttyUSB0)  <->  URCFilterProxy  <->  gammu (/dev/pts/N)

Proxy:
  * drží reálný port na PEVNĚ zvolené rychlosti (řeší i zásek z
    auto-detekce baudrate), takže gammu může jet s connection = at<rychlost>,
  * ze směru modem -> gammu zahazuje kompletní řádky odpovídající URC vzorům,
  * NIKDY nezadrží data, která nemohou být začátkem URC řádku (zejména
    prompt "> " při odesílání SMS, který nekončí CRLF) — jinak by se
    rozbilo odesílání.
"""

import os
import tty
import time
import logging
import threading

import serial

# Kompletní URC řádky, které SIM800/SIM800C posílá a které mateou gammu.
# Filtrujeme jen PŘESNĚ tyto celé řádky, nic jiného se nedotýkáme.
DEFAULT_URC_PATTERNS = [
    b"OVER-VOLTAGE WARNNING",
    b"UNDER-VOLTAGE WARNNING",
    b"OVER-VOLTAGE POWER DOWN",
    b"UNDER-VOLTAGE POWER DOWN",
]


class URCFilterProxy:
    """Sériová pty proxy filtrující URC řádky před předáním gammu."""

    def __init__(self, real_device, baudrate=115200, patterns=None):
        self.real_device = real_device
        self.baudrate = int(baudrate)
        self.patterns = patterns if patterns is not None else DEFAULT_URC_PATTERNS
        self.real = None
        self.master_fd = None
        self.slave_fd = None
        self.slave_name = None
        self.filtered_count = 0
        self._stop = threading.Event()
        self._threads = []

    def start(self):
        """Otevře reálný port a pty, spustí přeposílací vlákna.
        Vrací cestu k virtuálnímu portu (slave), kterou se předá gammu.
        """
        self.real = serial.Serial(self.real_device, self.baudrate, timeout=0)
        self.master_fd, self.slave_fd = os.openpty()
        # raw režim na obou koncích, ať se nepřekládají CR/LF ani echo
        tty.setraw(self.master_fd)
        tty.setraw(self.slave_fd)
        self.slave_name = os.ttyname(self.slave_fd)

        self._threads = [
            threading.Thread(target=self._real_to_gammu, daemon=True,
                             name="urc-real2gammu"),
            threading.Thread(target=self._gammu_to_real, daemon=True,
                             name="urc-gammu2real"),
        ]
        for t in self._threads:
            t.start()

        logging.info(
            f"🧹 URC filter proxy active: {self.real_device}@{self.baudrate} "
            f"-> {self.slave_name} (filtering {len(self.patterns)} URC patterns)"
        )
        return self.slave_name

    def stop(self):
        """Zastaví proxy a uvolní zdroje."""
        self._stop.set()
        for fd in (self.master_fd, self.slave_fd):
            try:
                if fd is not None:
                    os.close(fd)
            except OSError:
                pass
        try:
            if self.real is not None:
                self.real.close()
        except Exception:
            pass

    def _tail_might_be_urc(self, tail):
        """True, pokud nedokončený zbytek (bez koncového \\n) MŮŽE být
        začátkem některého URC řádku — pak ho radši pozdržíme.
        Cokoli jiného (např. prompt "> ") propustíme okamžitě.
        """
        t = tail.lstrip(b"\r\n")
        if not t:
            return False
        return any(p.startswith(t) for p in self.patterns)

    def _real_to_gammu(self):
        """Modem -> (filtr) -> gammu. Zahazuje kompletní URC řádky."""
        buf = b""
        while not self._stop.is_set():
            try:
                data = self.real.read(4096)
            except Exception as e:
                if not self._stop.is_set():
                    logging.error(f"URC proxy read error: {e}")
                break

            if not data:
                # Žádná nová data: pokud držíme zbytek, který nemůže být URC,
                # pusť ho dál (typicky prompt "> ").
                if buf and not self._tail_might_be_urc(buf):
                    self._write_master(buf)
                    buf = b""
                time.sleep(0.003)
                continue

            buf += data
            out = b""
            # Zpracuj všechny KOMPLETNÍ řádky (ukončené \n)
            while b"\n" in buf:
                idx = buf.index(b"\n")
                line = buf[:idx + 1]
                buf = buf[idx + 1:]
                if any(p in line for p in self.patterns):
                    self.filtered_count += 1  # zahoď celý URC řádek
                else:
                    out += line
            # Nedokončený zbytek pusť hned, pokud nemůže být začátek URC
            if buf and not self._tail_might_be_urc(buf):
                out += buf
                buf = b""
            if out:
                self._write_master(out)

    def _gammu_to_real(self):
        """gammu -> modem (bez úprav)."""
        while not self._stop.is_set():
            try:
                data = os.read(self.master_fd, 4096)
            except OSError:
                break
            if data:
                try:
                    self.real.write(data)
                except Exception as e:
                    if not self._stop.is_set():
                        logging.error(f"URC proxy write error: {e}")
                    break

    def _write_master(self, data):
        try:
            os.write(self.master_fd, data)
        except OSError as e:
            if not self._stop.is_set():
                logging.error(f"URC proxy master write error: {e}")
