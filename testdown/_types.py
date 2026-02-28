from __future__ import annotations

import dataclasses
import fnmatch
import io
import json
import types
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import yaml

if TYPE_CHECKING:
    from collections.abc import ItemsView
    from collections.abc import Iterator
    from collections.abc import KeysView
    from collections.abc import ValuesView

    import pandas as pd
    import polars as pl

_DATA_EXTRAS_HINT = "Install the data extras: pip install 'testdown[data]'"


class MarkdownBlocks:
    """Encapsulation of loaded Markdown blocks."""

    def __init__(self) -> None:
        """Construct an extracted markdown blocks instance."""
        self._blocks: dict[str, MarkdownBlock] = {}

    def __getitem__(self, key: str) -> MarkdownBlock:
        """Get a markdown block by name."""
        return self._blocks[key]

    def __setitem__(self, key: str, value: MarkdownBlock) -> None:
        """Set a markdown block by name."""
        self._blocks[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete a markdown block by name."""
        del self._blocks[key]

    def __contains__(self, key: object) -> bool:
        """Check if a markdown block exists by name."""
        return key in self._blocks

    def __iter__(self) -> Iterator[str]:
        """Iterate over markdown block names."""
        return iter(self._blocks)

    def __len__(self) -> int:
        """Get the number of markdown blocks."""
        return len(self._blocks)

    def __repr__(self) -> str:
        """Return a string representation of the markdown blocks."""
        return f"ExtractedMarkdownBlocks({self._blocks!r})"

    def keys(self) -> KeysView[str]:
        """Return the names of all markdown blocks."""
        return self._blocks.keys()

    def values(self) -> ValuesView[MarkdownBlock]:
        """Return all markdown blocks."""
        return self._blocks.values()

    def items(self) -> ItemsView[str, MarkdownBlock]:
        """Return name-block pairs for all markdown blocks."""
        return self._blocks.items()

    def get(
        self, key: str, default: MarkdownBlock | None = None
    ) -> MarkdownBlock | None:
        """Get a markdown block by name, with optional default."""
        return self._blocks.get(key, default)

    def find_all(self, pattern: str) -> tuple[MarkdownBlock, ...]:
        """Find all blocks that match the specified wildcard pattern argument."""
        return tuple(
            b
            for b in self._blocks.values()
            if fnmatch.fnmatch(b.name.lower(), pattern.lower())
        )


@dataclasses.dataclass()
class MarkdownBlock:
    """Data structure for an extracted Markdown blocks."""

    name: str
    index: int
    language: str
    contents: str

    def to_pandas_frame(
        self, csv_options: dict[str, Any] | None = None
    ) -> pd.DataFrame:
        """Convert to a Pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                f"pandas is required for this operation. {_DATA_EXTRAS_HINT}"
            ) from None

        if self.language == "df":
            try:
                import dftxt as _dftxt
            except ImportError:
                raise ImportError(
                    f"dftxt is required for 'df' blocks. {_DATA_EXTRAS_HINT}"
                ) from None
            return cast("pd.DataFrame", _dftxt.reads(self.contents, kind="pandas"))

        if self.language == "csv":
            return cast(
                "pd.DataFrame",
                pd.read_csv(io.StringIO(self.contents), **(csv_options or {})),
            )

        raise ValueError(
            f"Block type {self.language!r} cannot be converted to a pandas DataFrame."
        )

    def to_frame(self, csv_options: dict[str, Any] | None = None) -> pl.DataFrame:
        """Convert frame to a Polars DataFrame."""
        try:
            import polars as pl
        except ImportError:
            raise ImportError(
                f"polars is required for this operation. {_DATA_EXTRAS_HINT}"
            ) from None

        if self.language == "df":
            try:
                import dftxt as _dftxt
            except ImportError:
                raise ImportError(
                    f"dftxt is required for 'df' blocks. {_DATA_EXTRAS_HINT}"
                ) from None
            return cast("pl.DataFrame", _dftxt.reads(self.contents, kind="polars"))

        if self.language == "csv":
            return pl.read_csv(io.StringIO(self.contents), **(csv_options or {}))

        raise ValueError(
            f"Block type {self.language!r} cannot be converted to a Polars DataFrame."
        )

    def to_polars_frame(
        self, csv_options: dict[str, Any] | None = None
    ) -> pl.DataFrame:
        """Convert to a Polars DataFrame as an alias for the to_frame method."""
        return self.to_frame(csv_options)

    def to_dict(self, *, safe_load: bool = True) -> dict[str, Any]:
        """Convert block to a Python dictionary if possible."""
        if self.language == "json":
            return cast("dict[str, Any]", json.loads(self.contents))

        if self.language in ("yaml", "yml"):
            if safe_load:
                return cast("dict[str, Any]", yaml.safe_load(self.contents))
            return cast("dict[str, Any]", yaml.full_load(self.contents))

        raise ValueError(f"Block type {self.language!r} cannot be converted to a dict.")

    def exec_python_code(self, **kwargs: object) -> types.ModuleType:
        """Execute the code block as a python script module.

        @return The ModuleType populated by the execution.
        """
        temp_module = types.ModuleType(
            f"markdown_code_block_{self.language}_{self.name}_{self.index}"
        )
        if kwargs:
            temp_module.__dict__.update(**kwargs)
        exec(self.contents, temp_module.__dict__)  # noqa: S102
        return temp_module
