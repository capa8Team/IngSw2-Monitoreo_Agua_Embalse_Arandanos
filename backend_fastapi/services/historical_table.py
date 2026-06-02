"""Transformación de lecturas MongoDB a filas de tabla histórica (paridad con sensorUtils.js)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from services.mongodb import CHILE_TZ, get_all_devices, query_sensor_readings, to_chile_time

SensorFilter = Literal["all", "ph", "temperature", "conductivity"]

SENSOR_META: dict[str, dict[str, str | float]] = {
    "ph": {"label": "pH", "unit": "", "min": 6.0, "max": 8.5},
    "temperature": {"label": "Temperatura", "unit": "°C", "min": 15.0, "max": 30.0},
    "conductivity": {"label": "Conductividad", "unit": "µS/cm", "min": 700.0, "max": 1600.0},
}

HISTORICAL_LOOKBACK_DAYS = 7
TABLE_FETCH_LIMIT = 1500


def _device_id(device: dict) -> str:
    return str(device.get("id") or device.get("_id") or device.get("name") or "")


def _telemetry_keys(device: dict) -> list[str]:
    keys: list[str] = []
    telemetry_key = str(device.get("telemetry_key") or "").strip()
    arduino_id = str(device.get("arduino_id") or "").strip()
    name = str(device.get("name") or "").strip()
    if telemetry_key:
        keys.append(telemetry_key)
    if arduino_id and arduino_id not in keys:
        keys.append(arduino_id)
    if not telemetry_key and not arduino_id and name:
        keys.append(name)
    return keys


def _reading_matches_device(reading_key: str, device: dict) -> bool:
    rk = str(reading_key or "").strip()
    if not rk:
        return False
    return any(rk == k or rk.startswith(f"{k}-") for k in _telemetry_keys(device))


def _expand_readings(records: list[dict], registered_devices: list[dict]) -> list[dict]:
    if not registered_devices:
        return records

    peers_by_topic: dict[str, list[dict]] = {}
    for device in registered_devices:
        topic = str(device.get("topic") or "").strip()
        if not topic:
            continue
        peers_by_topic.setdefault(topic, []).append(device)

    output: list[dict] = []
    for record in records:
        targets = [d for d in registered_devices if _reading_matches_device(record.get("arduino_id", ""), d)]
        if not targets:
            continue

        topic_set = {str(d.get("topic") or "").strip() for d in targets if str(d.get("topic") or "").strip()}
        for topic in topic_set:
            merged = {_device_id(d): d for d in targets}
            for peer in peers_by_topic.get(topic, []):
                merged[_device_id(peer)] = peer
            targets = list(merged.values())

        for device in targets:
            display_name = str(device.get("name") or "").strip()
            if not display_name:
                continue
            output.append({**record, "device": display_name})

    output.sort(key=lambda r: r.get("timestamp") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return output


def _alert_status(sensor_key: str, value: float) -> tuple[str, str]:
    meta = SENSOR_META.get(sensor_key)
    if not meta:
        return "Normal", "normal"
    if value < float(meta["min"]) or value > float(meta["max"]):
        return "Alerta", "warning"
    return "Normal", "normal"


def _measurement_text(sensor_key: str, value: float) -> str:
    unit = str(SENSOR_META[sensor_key]["unit"])
    return f"{value:.2f} {unit}".strip() if unit else f"{value:.2f}"


def _local_date_key(ts: datetime) -> str:
    local = to_chile_time(ts)
    return local.strftime("%Y-%m-%d")


def _flatten_rows(records: list[dict], sensor_filter: SensorFilter = "all") -> list[dict]:
    rows: list[dict] = []
    for record in records:
        ts = to_chile_time(record.get("timestamp"))
        date_text = ts.strftime("%d-%m-%Y")
        date_key = _local_date_key(ts)
        time_text = ts.strftime("%H:%M:%S")
        device = str(record.get("device") or record.get("arduino_id") or "desconocido")

        for sensor_key, meta in SENSOR_META.items():
            if sensor_filter != "all" and sensor_filter != sensor_key:
                continue
            value = float(record.get(sensor_key, 0.0))
            status, css = _alert_status(sensor_key, value)
            rows.append(
                {
                    "key": f"{device}-{sensor_key}-{int(ts.timestamp() * 1000)}",
                    "device": device,
                    "sensorKey": sensor_key,
                    "sensorLabel": str(meta["label"]),
                    "rawValue": value,
                    "measurementText": _measurement_text(sensor_key, value),
                    "dateText": date_text,
                    "dateKey": date_key,
                    "timeText": time_text,
                    "timestamp": ts.isoformat(),
                    "alertStatus": status,
                    "alertClass": css,
                }
            )

    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    return rows


def _date_bounds(
    date_from: date | None,
    date_to: date | None,
) -> tuple[datetime | None, datetime | None]:
    since: datetime | None = None
    until: datetime | None = None
    if date_from is not None:
        since = datetime.combine(date_from, time.min, tzinfo=CHILE_TZ).astimezone(timezone.utc)
    if date_to is not None:
        until = datetime.combine(date_to, time.max, tzinfo=CHILE_TZ).astimezone(timezone.utc)
    return since, until


def get_historical_table_page(
    *,
    page: int = 1,
    page_size: int = 10,
    sensor: SensorFilter = "all",
    date_from: date | None = None,
    date_to: date | None = None,
    lookback_days: int = HISTORICAL_LOOKBACK_DAYS,
) -> dict:
    page = max(1, page)
    page_size = max(1, min(page_size, 50))

    now = datetime.now(timezone.utc)
    default_since = now - timedelta(days=max(1, min(lookback_days, 30)))
    filter_since, filter_until = _date_bounds(date_from, date_to)
    since = filter_since or default_since
    until = filter_until

    readings = query_sensor_readings(since=since, until=until, limit=TABLE_FETCH_LIMIT)
    devices = get_all_devices(active_only=True)
    expanded = _expand_readings(readings, devices)
    rows = _flatten_rows(expanded, sensor_filter=sensor)

    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "rows": rows[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": end < total,
    }
