from __future__ import annotations

import pathlib
import re

from testdown import _types


def extract_blocks(
    markdown_contents: str | pathlib.Path,
) -> _types.MarkdownBlocks:
    """Extract named blocks and return them as a collection."""
    source = (
        markdown_contents.read_text("utf-8")
        if isinstance(markdown_contents, pathlib.Path)
        else markdown_contents
    )
    pattern = r"```(?P<lang>[^\s]+)\s+(?P<name>[^\s]+)"
    matched = re.search(pattern, source)
    extracted = _types.MarkdownBlocks()
    while matched is not None:
        name: str = matched.group("name")
        language: str = matched.group("lang")
        contents, source = source[matched.end() :].split("```", 1)
        extracted[name] = _types.MarkdownBlock(
            name=name,
            language=language,
            contents=contents.strip(),
            index=len(extracted),
        )

        matched = re.search(pattern, source)

    return extracted
