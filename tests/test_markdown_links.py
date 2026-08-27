from pathlib import Path

from tools.check_markdown_links import find_missing_links


def test_find_missing_relative_markdown_link(tmp_path: Path) -> None:
    guide = tmp_path / "docs" / "guide.md"
    guide.parent.mkdir()
    guide.write_text("Read [the contract](../contracts/ble-v1.md).\n", encoding="utf-8")

    assert find_missing_links(tmp_path) == ["docs/guide.md -> ../contracts/ble-v1.md"]


def test_ignore_external_and_anchor_links(tmp_path: Path) -> None:
    guide = tmp_path / "guide.md"
    guide.write_text(
        "[web](https://example.com) [mail](mailto:test@example.com) [section](#part)\n",
        encoding="utf-8",
    )

    assert find_missing_links(tmp_path) == []


def test_ignore_generated_dependency_trees(tmp_path: Path) -> None:
    generated = tmp_path / "managed_components" / "vendor" / "README.md"
    generated.parent.mkdir(parents=True)
    generated.write_text("[vendor link](../missing.md)\n", encoding="utf-8")

    assert find_missing_links(tmp_path) == []
