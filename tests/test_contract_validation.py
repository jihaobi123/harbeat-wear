import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.validate_contracts import validate_engine_examples, validate_engine_schema


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


def write_examples(root: Path, messages: list[dict[str, object]]) -> None:
    path = root / "contracts" / "examples" / "engine-ipc-v1.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("\n".join(json.dumps(item) for item in messages) + "\n", encoding="utf-8")


def minimal_messages(kinds: set[str]) -> list[dict[str, object]]:
    messages = [{"v": 1, "kind": kind} for kind in sorted(kinds)]
    for message in messages:
        if message["kind"] == "set_direction":
            message.update(
                request_id="gw-test",
                wrist_command_id=42,
                op="set_energy",
                value=5,
                received_at_ms=1,
            )
    return messages


def test_engine_examples_require_every_message_kind(tmp_path: Path) -> None:
    messages = minimal_messages(KINDS - {"completed"})
    write_examples(tmp_path, messages)

    with pytest.raises(AssertionError, match="missing kinds: completed"):
        validate_engine_examples(tmp_path)


def test_engine_examples_reject_wrong_version(tmp_path: Path) -> None:
    messages = minimal_messages(KINDS)
    messages[0]["v"] = 2
    write_examples(tmp_path, messages)

    with pytest.raises(AssertionError, match="v must be 1"):
        validate_engine_examples(tmp_path)


def test_set_direction_requires_operation_and_value(tmp_path: Path) -> None:
    messages = [{"v": 1, "kind": kind} for kind in sorted(KINDS)]
    write_examples(tmp_path, messages)

    with pytest.raises(AssertionError, match="set_direction missing: request_id, wrist_command_id, op, value, received_at_ms"):
        validate_engine_examples(tmp_path)


def test_repository_engine_examples_match_schema() -> None:
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "contracts" / "engine-ipc-v1.schema.json").read_text())
    validator = Draft202012Validator(schema)
    examples = (root / "contracts" / "examples" / "engine-ipc-v1.jsonl").read_text().splitlines()

    for number, raw in enumerate(examples, 1):
        errors = sorted(validator.iter_errors(json.loads(raw)), key=lambda item: list(item.path))
        assert errors == [], f"line {number}: {[error.message for error in errors]}"


def test_schema_validation_rejects_out_of_range_energy(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    schema_source = root / "contracts" / "engine-ipc-v1.schema.json"
    schema_target = tmp_path / "contracts" / schema_source.name
    schema_target.parent.mkdir(parents=True)
    schema_target.write_text(schema_source.read_text(), encoding="utf-8")
    messages = [json.loads(raw) for raw in (root / "contracts" / "examples" / "engine-ipc-v1.jsonl").read_text().splitlines()]
    state = next(item for item in messages if item["kind"] == "state")
    state["current"]["energy"] = 9
    write_examples(tmp_path, messages)

    with pytest.raises(AssertionError, match="line 4: schema"):
        validate_engine_schema(tmp_path)
