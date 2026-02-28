"""Tests for the testdown package."""

import pathlib
import sys
import types
from unittest import mock

import pytest

import testdown

_SCENARIOS_DIR = pathlib.Path(__file__).parent / "scenarios"

_SCENARIOS = [
    f.name for f in _SCENARIOS_DIR.iterdir() if f.is_file() and f.name.endswith(".md")
]

_CSV_CONTENTS = "name,age\nAlice,30\nBob,25"
_DF_CONTENTS = "name   age\n&&str  &&int\nAlice  30"


def _make_block(name="test", language="python", contents="pass", index=0):
    return testdown.MarkdownBlock(
        name=name,
        index=index,
        language=language,
        contents=contents,
    )


# ---------------------------------------------------------------------------
# extract_blocks
# ---------------------------------------------------------------------------


def test_extract_blocks_from_string():
    md = "```python setup\nx = 1\n```"
    blocks = testdown.extract_blocks(md)
    assert "setup" in blocks
    assert blocks["setup"].language == "python"
    assert blocks["setup"].contents == "x = 1"


def test_extract_blocks_from_path(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text('```json config\n{"key": "value"}\n```', encoding="utf-8")
    blocks = testdown.extract_blocks(md_file)
    assert "config" in blocks
    assert blocks["config"].language == "json"


def test_extract_blocks_empty():
    blocks = testdown.extract_blocks("# Just a heading\nSome text.")
    assert len(blocks) == 0


def test_extract_blocks_multiple():
    md = (
        "```python setup\nx = 1\n```\n\n"
        '```json config\n{"a": 1}\n```\n\n'
        "```yaml meta\nkey: val\n```"
    )
    blocks = testdown.extract_blocks(md)
    assert set(blocks.keys()) == {"setup", "config", "meta"}
    assert blocks["setup"].index < blocks["config"].index < blocks["meta"].index


# ---------------------------------------------------------------------------
# MarkdownBlocks
# ---------------------------------------------------------------------------


def test_markdown_blocks_setitem_getitem():
    blocks = testdown.MarkdownBlocks()
    block = _make_block("foo")
    blocks["foo"] = block
    assert blocks["foo"] is block


def test_markdown_blocks_delitem():
    blocks = testdown.MarkdownBlocks()
    blocks["foo"] = _make_block("foo")
    del blocks["foo"]
    assert "foo" not in blocks


def test_markdown_blocks_contains_true_and_false():
    blocks = testdown.MarkdownBlocks()
    blocks["foo"] = _make_block("foo")
    assert "foo" in blocks
    assert "bar" not in blocks


def test_markdown_blocks_iter():
    blocks = testdown.MarkdownBlocks()
    blocks["a"] = _make_block("a")
    blocks["b"] = _make_block("b")
    assert list(blocks) == ["a", "b"]


def test_markdown_blocks_len():
    blocks = testdown.MarkdownBlocks()
    assert len(blocks) == 0
    blocks["x"] = _make_block("x")
    assert len(blocks) == 1


def test_markdown_blocks_repr():
    blocks = testdown.MarkdownBlocks()
    blocks["a"] = _make_block("a")
    assert "ExtractedMarkdownBlocks(" in repr(blocks)


def test_markdown_blocks_keys():
    blocks = testdown.MarkdownBlocks()
    blocks["a"] = _make_block("a")
    blocks["b"] = _make_block("b")
    assert set(blocks.keys()) == {"a", "b"}


def test_markdown_blocks_values():
    blocks = testdown.MarkdownBlocks()
    block = _make_block("a")
    blocks["a"] = block
    assert block in blocks.values()


def test_markdown_blocks_items():
    blocks = testdown.MarkdownBlocks()
    block = _make_block("a")
    blocks["a"] = block
    assert ("a", block) in blocks.items()


def test_markdown_blocks_get_present():
    blocks = testdown.MarkdownBlocks()
    block = _make_block("a")
    blocks["a"] = block
    assert blocks.get("a") is block


def test_markdown_blocks_get_missing_returns_none():
    blocks = testdown.MarkdownBlocks()
    assert blocks.get("missing") is None


def test_markdown_blocks_get_custom_default():
    blocks = testdown.MarkdownBlocks()
    fallback = _make_block("fallback")
    assert blocks.get("missing", fallback) is fallback


def test_markdown_blocks_find_all_matches_and_skips():
    blocks = testdown.MarkdownBlocks()
    blocks["expected_actual_foo"] = _make_block("expected_actual_foo")
    blocks["expected_aggregate_foo"] = _make_block("expected_aggregate_foo")
    blocks["setup"] = _make_block("setup")
    results = blocks.find_all("expected_*_*")
    expected_names = {"expected_actual_foo", "expected_aggregate_foo"}
    assert {b.name for b in results} == expected_names


def test_markdown_blocks_find_all_no_match():
    blocks = testdown.MarkdownBlocks()
    blocks["setup"] = _make_block("setup")
    assert blocks.find_all("expected_*") == ()


# ---------------------------------------------------------------------------
# MarkdownBlock.to_dict
# ---------------------------------------------------------------------------


def test_to_dict_json():
    block = _make_block(language="json", contents='{"key": "value"}')
    assert block.to_dict() == {"key": "value"}


def test_to_dict_yaml_safe_load():
    block = _make_block(language="yaml", contents="key: value\nnumber: 42")
    assert block.to_dict() == {"key": "value", "number": 42}


def test_to_dict_yaml_full_load():
    block = _make_block(language="yaml", contents="key: value")
    assert block.to_dict(safe_load=False) == {"key": "value"}


def test_to_dict_yml():
    block = _make_block(language="yml", contents="name: test")
    assert block.to_dict() == {"name": "test"}


def test_to_dict_invalid_language():
    block = _make_block(language="python", contents="x = 1")
    with pytest.raises(ValueError, match="cannot be converted to a dict"):
        block.to_dict()


# ---------------------------------------------------------------------------
# MarkdownBlock.exec_python_code
# ---------------------------------------------------------------------------


def test_exec_python_code_basic():
    block = _make_block(language="python", contents="result = 1 + 1")
    module = block.exec_python_code()
    assert isinstance(module, types.ModuleType)
    assert module.result == 1 + 1


def test_exec_python_code_with_kwargs():
    block = _make_block(language="python", contents="doubled = x + x")
    module = block.exec_python_code(x=5)
    assert module.doubled == 5 + 5


# ---------------------------------------------------------------------------
# MarkdownBlock.to_pandas_frame
# ---------------------------------------------------------------------------


def test_to_pandas_frame_csv():
    block = _make_block(language="csv", contents=_CSV_CONTENTS)
    df = block.to_pandas_frame()
    assert set(df.columns) == {"name", "age"}
    assert set(df["name"].tolist()) == {"Alice", "Bob"}


def test_to_pandas_frame_csv_with_options():
    block = _make_block(language="csv", contents="name|age\nAlice|30", name="data")
    df = block.to_pandas_frame(csv_options={"sep": "|"})
    assert set(df.columns) == {"name", "age"}


def test_to_pandas_frame_df():
    block = _make_block(language="df", contents=_DF_CONTENTS)
    df = block.to_pandas_frame()
    assert set(df.columns) == {"name", "age"}


def test_to_pandas_frame_invalid_language():
    block = _make_block(language="python", contents="x = 1")
    with pytest.raises(ValueError, match="cannot be converted to a pandas DataFrame"):
        block.to_pandas_frame()


def test_to_pandas_frame_pandas_not_installed():
    block = _make_block(language="csv", contents=_CSV_CONTENTS)
    with (
        mock.patch.dict(sys.modules, {"pandas": None}),
        pytest.raises(ImportError, match="pandas is required"),
    ):
        block.to_pandas_frame()


def test_to_pandas_frame_dftxt_not_installed():
    block = _make_block(language="df", contents=_DF_CONTENTS)
    with (
        mock.patch.dict(sys.modules, {"dftxt": None}),
        pytest.raises(ImportError, match="dftxt is required"),
    ):
        block.to_pandas_frame()


# ---------------------------------------------------------------------------
# MarkdownBlock.to_frame / to_polars_frame
# ---------------------------------------------------------------------------


def test_to_frame_csv():
    block = _make_block(language="csv", contents=_CSV_CONTENTS)
    df = block.to_frame()
    assert set(df.columns) == {"name", "age"}
    assert set(df["name"].to_list()) == {"Alice", "Bob"}


def test_to_frame_csv_with_options():
    block = _make_block(language="csv", contents="name|age\nAlice|30", name="data")
    df = block.to_frame(csv_options={"separator": "|"})
    assert set(df.columns) == {"name", "age"}


def test_to_frame_df():
    block = _make_block(language="df", contents=_DF_CONTENTS)
    df = block.to_frame()
    assert set(df.columns) == {"name", "age"}


def test_to_frame_invalid_language():
    block = _make_block(language="python", contents="x = 1")
    with pytest.raises(ValueError, match="cannot be converted to a Polars DataFrame"):
        block.to_frame()


def test_to_frame_polars_not_installed():
    block = _make_block(language="csv", contents=_CSV_CONTENTS)
    with (
        mock.patch.dict(sys.modules, {"polars": None}),
        pytest.raises(ImportError, match="polars is required"),
    ):
        block.to_frame()


def test_to_frame_dftxt_not_installed():
    block = _make_block(language="df", contents=_DF_CONTENTS)
    with (
        mock.patch.dict(sys.modules, {"dftxt": None}),
        pytest.raises(ImportError, match="dftxt is required"),
    ):
        block.to_frame()


def test_to_polars_frame_delegates_to_frame():
    block = _make_block(language="csv", contents="name,age\nAlice,30")
    df = block.to_polars_frame()
    assert "name" in df.columns


# ---------------------------------------------------------------------------
# Scenario-based integration tests (example-inspired pattern)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario_name", _SCENARIOS)
def test_scenario_population(scenario_name):
    blocks = testdown.extract_blocks(_SCENARIOS_DIR / scenario_name)
    assert "setup" in blocks
    setup_module = blocks["setup"].exec_python_code()
    assert isinstance(setup_module, types.ModuleType)
    expected_blocks = blocks.find_all("expected_*_*")
    for block in expected_blocks:
        result = block.to_dict()
        assert isinstance(result, dict)
