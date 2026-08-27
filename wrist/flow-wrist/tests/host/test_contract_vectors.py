from __future__ import annotations

import json
from pathlib import Path

import cbor2

ROOT = Path(__file__).resolve().parents[4]


def test_vectors_are_available_from_wrist_tree() -> None:
    path = ROOT / "contracts" / "golden-vectors" / "ble-v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert [item["name"] for item in data["commands"]] == [
        "set_energy_5",
        "set_style_breaking",
    ]
    assert all(bytes.fromhex(item["cbor_hex"]) for item in data["commands"])
    for item in data["commands"]:
        assert cbor2.loads(bytes.fromhex(item["cbor_hex"])) == item["semantic"]
