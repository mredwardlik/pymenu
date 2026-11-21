from __future__ import annotations

import typing as t


class Context:
    """State shared by all pages of a menu.

    :ivar history: names of the opened pages, the current one is the last.
    :ivar data: your own values, for example settings chosen on one page
        and used on another.
    """

    def __init__(self) -> None:
        self.history: t.List[str] = []
        self.data: t.Dict[str, t.Any] = {}

    @property
    def page(self) -> t.Optional[str]:
        """Name of the current page."""
        return self.history[-1] if self.history else None

    @property
    def previous(self) -> t.Optional[str]:
        return self.history[-2] if len(self.history) > 1 else None

    def __repr__(self) -> str:
        return f'Context(history={self.history!r}, data={self.data!r})'
