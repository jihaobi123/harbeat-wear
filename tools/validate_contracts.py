from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
KINDS = {
    "hello",
    "hello_ok",
    "get_state",
    "state",
    "set_direction",
    "accepted",
    "progress",
    "completed",
    "rejected",
}


def validate_ble_vectors(root: Path = ROOT) -> None:
    path = root / "contracts" / "golden-vectors" / "ble-v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    names = {item["name"] for item in data.get("commands", [])}
    assert names == {"set_energy_5", "set_style_breaking"}, "unexpected BLE vector names"
    for item in data["commands"]:
        encoded = bytes.fromhex(item["cbor_hex"])
        assert 0 < len(encoded) <= 192, f"{item['name']}: encoded size"


def validate_engine_examples(root: Path = ROOT) -> None:
    path = root / "contracts" / "examples" / "engine-ipc-v1.jsonl"
    seen: set[str] = set()
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        message = json.loads(raw)
        assert message.get("v") == 1, f"line {number}: v must be 1"
        kind = message.get("kind")
        assert kind in KINDS, f"line {number}: unsupported kind {kind}"
        if kind == "set_direction":
            required = ("request_id", "wrist_command_id", "op", "value", "received_at_ms")
            missing_fields = [field for field in required if field not in message]
            assert not missing_fields, f"set_direction missing: {', '.join(missing_fields)}"
        seen.add(kind)
    missing = sorted(KINDS - seen)
    assert not missing, f"missing kinds: {', '.join(missing)}"


def validate_engine_schema(root: Path = ROOT) -> None:
    schema_path = root / "contracts" / "engine-ipc-v1.schema.json"
    examples_path = root / "contracts" / "examples" / "engine-ipc-v1.jsonl"
    validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
    for number, raw in enumerate(examples_path.read_text(encoding="utf-8").splitlines(), 1):
        errors = sorted(validator.iter_errors(json.loads(raw)), key=lambda item: list(item.path))
        assert not errors, f"line {number}: schema: {[error.message for error in errors]}"


def main() -> int:
    validate_ble_vectors()
    print("BLE v1 vectors: OK")
    validate_engine_examples()
    validate_engine_schema()
    print("Engine IPC v1 examples: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
