#!/usr/bin/env python3
"""Parser for Teltonika AVL data - simplified version for CSV logging"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Iterable

# HEX delimiter for splitting segments
HEX_DELIMITER = "59D90010"

# Accept timestamps roughly between 2015-01-01 and 2035-01-01 UTC
MIN_TS_MS = int(datetime(2015, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
MAX_TS_MS = int(datetime(2035, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

# IO IDs for accelerometer axes in Codec8(E) payloads
ACCEL_IO_IDS = {0x0011: "x", 0x0012: "y", 0x0013: "z"}


class AvlRecord:
    """Represents a single AVL record with GPS and accelerometer data"""

    def __init__(
        self,
        timestamp_ms: int,
        priority: int,
        lon: float,
        lat: float,
        altitude: int,
        angle: int,
        satellites: int,
        speed: int,
        accel: Dict[str, Optional[int]]
    ):
        self.timestamp_ms = timestamp_ms
        self.priority = priority
        self.lon = lon
        self.lat = lat
        self.altitude = altitude
        self.angle = angle
        self.satellites = satellites
        self.speed = speed
        self.accel = accel

    @property
    def iso_timestamp(self) -> str:
        """ISO formatted timestamp"""
        dt = datetime.fromtimestamp(self.timestamp_ms / 1000, timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    @property
    def date_str(self) -> str:
        """Date part of ISO timestamp"""
        return self.iso_timestamp.split("T", 1)[0]

    def as_dict(self) -> Dict:
        """Convert to dictionary for CSV export"""
        return {
            "date": self.date_str,
            "deviceTimestamp": self.iso_timestamp,
            "gps_lat": round(self.lat, 7),
            "gps_lon": round(self.lon, 7),
            "gps_altitude": self.altitude,
            "gps_angle": self.angle,
            "gps_satellites": self.satellites,
            "gps_speedKph": self.speed,
            "acc_x": self.accel.get("x"),
            "acc_y": self.accel.get("y"),
            "acc_z": self.accel.get("z"),
            "priority": self.priority,
        }


def iter_segments(raw_hex: str) -> Iterable[bytes]:
    """Split raw hex string into segments based on delimiter"""
    clean = raw_hex.strip().upper()
    if not clean:
        return
    for part in clean.split(HEX_DELIMITER):
        if not part:
            continue
        # Teltonika packets should have even number of characters
        if len(part) % 2 != 0:
            part = part[:-1]
        try:
            yield bytes.fromhex(part)
        except ValueError:
            continue


def find_timestamp_offset(data: bytes, start: int) -> Optional[int]:
    """Locate the next plausible AVL timestamp in milliseconds"""
    min_len = 8 + 1 + 4 + 4 + 2 + 2 + 1 + 2  # timestamp + minimal GPS
    for offset in range(start, max(len(data) - min_len, 0)):
        window = data[offset : offset + 8]
        if len(window) < 8:
            break
        ts = int.from_bytes(window, "big")
        if not (MIN_TS_MS <= ts <= MAX_TS_MS):
            continue
        # Basic sanity checks on priority + satellite count
        if offset + 9 >= len(data):
            continue
        priority = data[offset + 8]
        sat_pos = offset + 8 + 1 + 4 + 4 + 2 + 2
        sats = data[sat_pos] if sat_pos < len(data) else None
        if priority > 3:
            continue
        if sats is not None and sats > 32:
            continue
        return offset
    return None


def _to_signed(raw: bytes, bits: int) -> int:
    """Convert bytes to signed integer"""
    value = int.from_bytes(raw, "big", signed=False)
    return _to_signed_int(value, bits)


def _to_signed_int(value: int, bits: int) -> int:
    """Convert unsigned integer to signed using bit width"""
    threshold = 1 << (bits - 1)
    mask = 1 << bits
    if value >= threshold:
        value -= mask
    return value


def read_record(data: bytes, ts_offset: int) -> Tuple[Optional[AvlRecord], int]:
    """Read a single AVL record from data starting at ts_offset"""
    ptr = ts_offset
    if len(data) - ptr < 32:
        return None, ts_offset + 1

    ts = int.from_bytes(data[ptr : ptr + 8], "big")
    if not (MIN_TS_MS <= ts <= MAX_TS_MS):
        return None, ts_offset + 1
    ptr += 8

    priority = data[ptr]
    ptr += 1

    lon = _to_signed(data[ptr : ptr + 4], 32) / 10_000_000
    ptr += 4
    lat = _to_signed(data[ptr : ptr + 4], 32) / 10_000_000
    ptr += 4
    altitude = _to_signed(data[ptr : ptr + 2], 16)
    ptr += 2
    angle = int.from_bytes(data[ptr : ptr + 2], "big")
    ptr += 2
    sats = data[ptr]
    ptr += 1
    speed = int.from_bytes(data[ptr : ptr + 2], "big")
    ptr += 2

    # Attempt Codec8 Extended layout (event + total as 2 bytes each)
    if len(data) - ptr < 4:
        return None, ts_offset + 1

    event_id = int.from_bytes(data[ptr : ptr + 2], "big")
    ptr += 2
    total_io = int.from_bytes(data[ptr : ptr + 2], "big")
    ptr += 2

    if total_io > 256:
        return None, ts_offset + 1

    # Parse IO elements by size groups (1, 2, 4, 8 bytes)
    groups: Dict[int, Dict[int, int]] = {}
    for size in (1, 2, 4, 8):
        if len(data) - ptr < 2:
            break
        count = int.from_bytes(data[ptr : ptr + 2], "big")
        ptr += 2
        if count == 0:
            continue
        needed = count * (2 + size)
        if len(data) - ptr < needed:
            # Truncated tail – stop parsing further groups
            ptr = len(data)
            break
        entries: Dict[int, int] = {}
        for _ in range(count):
            io_id = int.from_bytes(data[ptr : ptr + 2], "big")
            ptr += 2
            value = int.from_bytes(data[ptr : ptr + size], "big")
            ptr += size
            entries[io_id] = value
        if entries:
            groups[size] = entries

    # Extract accelerometer values
    accel_vals: Dict[str, Optional[int]] = {"x": None, "y": None, "z": None}
    for io_id, axis in ACCEL_IO_IDS.items():
        raw = None
        if 2 in groups and io_id in groups[2]:
            raw = _to_signed_int(groups[2][io_id], 16)
        elif 1 in groups and io_id in groups[1]:
            raw = _to_signed_int(groups[1][io_id], 8)
        accel_vals[axis] = raw

    record = AvlRecord(
        timestamp_ms=ts,
        priority=priority,
        lon=lon,
        lat=lat,
        altitude=altitude,
        angle=angle,
        satellites=sats,
        speed=speed,
        accel=accel_vals,
    )

    return record, ptr


def parse_avl_data(raw_hex: str) -> List[AvlRecord]:
    """
    Parse Teltonika AVL data from hex string.
    Returns list of AvlRecord objects.
    """
    records: List[AvlRecord] = []

    for segment in iter_segments(raw_hex):
        pos = 0
        while pos < len(segment):
            ts_offset = find_timestamp_offset(segment, pos)
            if ts_offset is None:
                break
            rec, next_pos = read_record(segment, ts_offset)
            if rec is None:
                pos = ts_offset + 1
                continue
            records.append(rec)
            pos = max(next_pos, ts_offset + 1)

    return records
