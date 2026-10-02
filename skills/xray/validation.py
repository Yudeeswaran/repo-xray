from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SchemaValidationError(ValueError):
    pass


def _load_schema(name: str) -> dict[str, Any]:
    path = Path(__file__).with_name("schemas") / name
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_ref(ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaValidationError(f"unsupported schema reference: {ref}")
    root = _load_schema("evidence-ledger.json")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _check(value: Any, schema: dict[str, Any], path: str, root_schema: dict[str, Any]) -> None:
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref == "claim.json":
            schema = _load_schema("claim.json")
        elif ref.startswith("#/"):
            node: Any = root_schema
            for part in ref[2:].split("/"):
                node = node[part]
            schema = node
        else:
            raise SchemaValidationError(f"unsupported $ref at {path}: {ref}")

    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path}: expected {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path}: value {value!r} is not in enum")

    typ = schema.get("type")
    if typ == "object":
        if not isinstance(value, dict):
            raise SchemaValidationError(f"{path}: expected object")
        for key in schema.get("required", []):
            if key not in value:
                raise SchemaValidationError(f"{path}: missing required property {key!r}")
        for key, child in schema.get("properties", {}).items():
            if key in value:
                _check(value[key], child, f"{path}.{key}", root_schema)
    elif typ == "array":
        if not isinstance(value, list):
            raise SchemaValidationError(f"{path}: expected array")
        if "items" in schema:
            for i, item in enumerate(value):
                _check(item, schema["items"], f"{path}[{i}]", root_schema)
    elif typ == "string":
        if not isinstance(value, str):
            raise SchemaValidationError(f"{path}: expected string")
    elif typ == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SchemaValidationError(f"{path}: expected number")
        if "minimum" in schema and value < schema["minimum"]:
            raise SchemaValidationError(f"{path}: below minimum")


def validate_artifact(value: dict[str, Any], schema_name: str = "evidence-ledger.json") -> None:
    schema = _load_schema(schema_name)
    _check(value, schema, "$", schema)
