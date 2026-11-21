from __future__ import annotations

__all__ = ['Trigger', 'CharsTrigger', 'KeysTrigger', 'normalize']


def normalize(text: str) -> str:
    """Triggers don't depend on case and surrounding spaces."""
    return ' '.join(str(text).split()).casefold()


class Trigger:
    """Something the user did that may choose an element."""

    def __init__(self, content: str):
        self.content: str = normalize(content)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.content!r})'


class CharsTrigger(Trigger):
    """Typed text, for example ``2`` or ``help``."""


class KeysTrigger(Trigger):
    """A special key, for example ``up`` or ``enter``."""
