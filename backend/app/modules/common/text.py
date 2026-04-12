from __future__ import annotations

from typing import Any
import unicodedata


def sanitize_text(value: str | bytes) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")

    cleaned: list[str] = []
    for char in value:
        if char == "\x00":
            continue
        category = unicodedata.category(char)
        if category == "Cs":
            continue
        if category.startswith("C") and char not in {"\n", "\r", "\t"}:
            continue
        cleaned.append(char)
    return "".join(cleaned)


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, str | int | float | bool]:
    if not metadata:
        return {}

    cleaned: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        cleaned_key = sanitize_text(str(key)).strip()
        if not cleaned_key:
            continue

        if isinstance(value, (str, bytes)):
            cleaned_value = sanitize_text(value).strip()
            if cleaned_value:
                cleaned[cleaned_key] = cleaned_value
            continue

        if isinstance(value, (int, float, bool)):
            cleaned[cleaned_key] = value
            continue

        fallback_value = sanitize_text(str(value)).strip()
        if fallback_value:
            cleaned[cleaned_key] = fallback_value

    return cleaned
