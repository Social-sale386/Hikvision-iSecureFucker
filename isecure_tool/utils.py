from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable, List, Tuple
from urllib.parse import urlsplit, parse_qsl, urlencode


ISO8601_SECONDS_MIN = 946684800  # 2000-01-01
ISO8601_SECONDS_MAX = 4102444800  # 2100-01-01
ISO8601_MILLIS_MIN = ISO8601_SECONDS_MIN * 1000
ISO8601_MILLIS_MAX = ISO8601_SECONDS_MAX * 1000


def parse_json_text(text: str) -> tuple[bool, Any, str]:
    raw = text.strip()
    if not raw:
        return True, None, ""
    try:
        return True, json.loads(raw), ""
    except Exception as exc:
        return False, None, f"{exc.__class__.__name__}: {exc}"


def _epoch_to_iso(value: int, is_millis: bool) -> str:
    ts = value / 1000.0 if is_millis else value
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    if is_millis:
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def _maybe_convert_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        iv = int(value)
        length = len(str(abs(iv)))
        if length == 10 and ISO8601_SECONDS_MIN <= iv <= ISO8601_SECONDS_MAX:
            return _epoch_to_iso(iv, False)
        if length == 13 and ISO8601_MILLIS_MIN <= iv <= ISO8601_MILLIS_MAX:
            return _epoch_to_iso(iv, True)
        return value

    if isinstance(value, str):
        sv = value.strip()
        if sv.isdigit():
            iv = int(sv)
            length = len(sv)
            if length == 10 and ISO8601_SECONDS_MIN <= iv <= ISO8601_SECONDS_MAX:
                return _epoch_to_iso(iv, False)
            if length == 13 and ISO8601_MILLIS_MIN <= iv <= ISO8601_MILLIS_MAX:
                return _epoch_to_iso(iv, True)
        return value

    return value


def convert_time_values(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: convert_time_values(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [convert_time_values(item) for item in obj]
    return _maybe_convert_scalar(obj)


def build_full_url(scheme: str, host: str, api_path: str) -> tuple[str, str, List[Tuple[str, str]]]:
    host = host.strip()
    api_path = api_path.strip()

    if api_path.startswith("http://") or api_path.startswith("https://"):
        split = urlsplit(api_path)
        base = f"{split.scheme}://{split.netloc}"
        base_path = split.path
        query_items = parse_qsl(split.query, keep_blank_values=True)
        return f"{base}{base_path}", base_path or "/", query_items

    if host.startswith("http://") or host.startswith("https://"):
        split = urlsplit(host)
        scheme = split.scheme
        host = split.netloc
        base_path = split.path.rstrip("/")
    else:
        base_path = ""

    split_api = urlsplit(api_path)
    path = split_api.path if split_api.path.startswith("/") else f"/{split_api.path}"
    full_path = f"{base_path}{path}"
    query_items = parse_qsl(split_api.query, keep_blank_values=True)
    full_url = f"{scheme}://{host}{full_path}"
    return full_url, full_path, query_items


def combine_query_items(existing: List[Tuple[str, str]], extra: Any) -> List[Tuple[str, str]]:
    items = list(existing)
    if extra is None:
        return items
    if isinstance(extra, dict):
        for key, value in extra.items():
            if isinstance(value, list):
                for item in value:
                    items.append((str(key), "" if item is None else str(item)))
            else:
                items.append((str(key), "" if value is None else str(value)))
    return items


def canonicalize_query(items: Iterable[Tuple[str, str]]) -> str:
    ordered = sorted([(k, v) for k, v in items], key=lambda kv: (kv[0], kv[1]))
    return urlencode(ordered, doseq=True)
