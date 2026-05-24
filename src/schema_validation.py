from __future__ import annotations

from typing import Any


EMPTY_VALUES = (None, "", [], {})


def _is_missing(payload: dict[str, Any], field: str) -> bool:
    if field == "missing_questions":
        return field not in payload or payload.get(field) is None
    return field not in payload or payload.get(field) in EMPTY_VALUES


def validate_required_fields(payload: dict[str, Any], schema_name: str, registry: dict[str, Any]) -> dict[str, Any]:
    schema = registry.get(schema_name)
    if not schema:
        return {
            "schema_name": schema_name,
            "verdict": "ERROR",
            "reason_code": "unknown_schema",
            "missing_fields": [],
            "summary": f"Unknown schema: {schema_name}",
        }

    required_fields = schema.get("required_fields", [])
    missing_fields = [field for field in required_fields if _is_missing(payload, field)]
    verdict = "PASS" if not missing_fields else "BLOCKED"
    reason_code = "pass" if verdict == "PASS" else "missing_required_fields"

    return {
        "schema_name": schema_name,
        "verdict": verdict,
        "reason_code": reason_code,
        "missing_fields": missing_fields,
        "summary": "All required fields are present." if verdict == "PASS" else "Required fields are missing.",
    }


def validate_collection(items: list[dict[str, Any]], schema_name: str, registry: dict[str, Any]) -> dict[str, Any]:
    item_results = [
        {
            "index": index,
            **validate_required_fields(item, schema_name, registry),
        }
        for index, item in enumerate(items)
    ]
    blocked = [result for result in item_results if result["verdict"] == "BLOCKED"]
    errors = [result for result in item_results if result["verdict"] == "ERROR"]
    if errors:
        verdict = "ERROR"
        reason_code = "schema_error"
    elif blocked:
        verdict = "BLOCKED"
        reason_code = "collection_missing_required_fields"
    else:
        verdict = "PASS"
        reason_code = "pass"

    return {
        "schema_name": schema_name,
        "verdict": verdict,
        "reason_code": reason_code,
        "item_results": item_results,
        "summary": f"{len(blocked)} of {len(items)} items are missing required fields.",
    }
