from __future__ import annotations

import base64
import hashlib
import hmac
import time
import uuid
from dataclasses import dataclass
from email.utils import formatdate
from typing import Any, Dict, Iterable, List, Tuple


EXCLUDED_SIGN_HEADERS = {
    "x-ca-signature",
    "x-ca-signature-headers",
    "accept",
    "content-md5",
    "content-type",
    "date",
    "content-length",
    "server",
    "connection",
    "host",
    "transfer-encoding",
    "x-application-context",
    "content-encoding",
}


def _lower_headers(headers: Dict[str, Any]) -> Dict[str, str]:
    lowered: Dict[str, str] = {}
    for key, value in headers.items():
        if value is None:
            continue
        lowered[key.lower()] = str(value).strip()
    return lowered


def _determine_sign_headers(headers: Dict[str, Any], override: str | None) -> List[str]:
    if override and override.strip():
        items = [item.strip().lower() for item in override.split(",") if item.strip()]
        return sorted(set(items))

    sign_headers: List[str] = []
    for key in headers.keys():
        lower = key.lower()
        if lower in EXCLUDED_SIGN_HEADERS:
            continue
        sign_headers.append(lower)
    return sorted(set(sign_headers))


def _canonical_headers(headers_lower: Dict[str, str], sign_headers: Iterable[str]) -> str:
    lines: List[str] = []
    for key in sign_headers:
        if key in headers_lower:
            lines.append(f"{key}:{headers_lower[key]}\n")
    return "".join(lines)


def _canonical_resource(path: str, query_items: Iterable[Tuple[str, str]]) -> str:
    if not query_items:
        return path
    first_values: Dict[str, str] = {}
    for key, value in query_items:
        key_str = str(key)
        if key_str in first_values:
            continue
        if value is None:
            first_values[key_str] = ""
        else:
            first_values[key_str] = str(value)
    parts: List[str] = []
    for key in sorted(first_values.keys()):
        value = first_values[key]
        if value == "":
            parts.append(key)
        else:
            parts.append(f"{key}={value}")
    return f"{path}?{'&'.join(parts)}"


def _content_md5(body: bytes) -> str:
    digest = hashlib.md5(body).digest()
    return base64.b64encode(digest).decode("utf-8")


def _string_to_sign(
    method: str,
    headers_lower: Dict[str, str],
    canonical_headers: str,
    canonical_resource: str,
) -> str:
    parts = [method]
    if "accept" in headers_lower:
        parts.append(headers_lower.get("accept", ""))
    if "content-md5" in headers_lower:
        parts.append(headers_lower.get("content-md5", ""))
    if "content-type" in headers_lower:
        parts.append(headers_lower.get("content-type", ""))
    if "date" in headers_lower:
        parts.append(headers_lower.get("date", ""))
    return "\n".join(parts) + "\n" + canonical_headers + canonical_resource


@dataclass
class SignatureResult:
    headers: Dict[str, str]
    string_to_sign: str
    canonical_resource: str


def sign_request(
    method: str,
    path: str,
    query_items: List[Tuple[str, str]],
    headers: Dict[str, Any],
    body: bytes | None,
    app_key: str,
    app_secret: str,
    sign_headers_override: str | None,
    use_date: bool,
    compute_content_md5: bool,
) -> SignatureResult:
    method = method.upper()

    merged = dict(headers)

    if body and compute_content_md5:
        merged.setdefault("Content-MD5", _content_md5(body))

    if use_date:
        merged.setdefault("Date", formatdate(time.time(), usegmt=True))

    merged["X-Ca-Key"] = app_key
    merged.setdefault("X-Ca-Timestamp", str(int(time.time() * 1000)))
    merged.setdefault("X-Ca-Nonce", str(uuid.uuid4()))

    sign_headers = _determine_sign_headers(merged, sign_headers_override)
    merged["X-Ca-Signature-Headers"] = ",".join(sign_headers)

    headers_lower = _lower_headers(merged)
    canonical_headers = _canonical_headers(headers_lower, sign_headers)
    canonical_resource = _canonical_resource(path, query_items)

    string_to_sign = _string_to_sign(
        method,
        headers_lower,
        canonical_headers,
        canonical_resource,
    )

    signature = base64.b64encode(
        hmac.new(app_secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")
    merged["X-Ca-Signature"] = signature

    final_headers = {key: str(value) for key, value in merged.items() if value is not None}
    return SignatureResult(final_headers, string_to_sign, canonical_resource)
