from __future__ import annotations

import typing as t

from pymenu.context import Context
from pymenu.elements import ElementInterface

if t.TYPE_CHECKING:
    from pymenu.main import PyMenu

__all__ = ['Page']


class Page:
    """A screen of the menu. Subclass it and override :meth:`build`.

    ``build`` is called before every render, so labels can show the
    current state.

    :cvar title: shown in the page header; the class name by default.
    :cvar description: optional text under the header.
    """

    title: t.Optional[str] = None
    description: t.Optional[str] = None

    def __init__(self, context: Context, menu: t.Optional[PyMenu] = None):
        self.context: Context = context
        self.menu: t.Optional[PyMenu] = menu

    def build(self) -> t.Union[ElementInterface, t.Iterable[ElementInterface]]:
        raise NotImplementedError(
            f'You need to override "build" method in {self.__class__.__name__} class.')

    def get_title(self) -> str:
        return self.title or self.__class__.__name__

    # helpers for actions

    def print(self, *objects: t.Any, style: t.Optional[str] = None) -> None:
        """Show a message under the menu (supports rich markup)."""
        if self.menu is None:
            print(*objects)
            return
        self.menu.message(*objects, style=style)

    def input(self, prompt: str = '') -> str:
        """Ask the user for a line of text."""
        if self.menu is None:
            return input(prompt)
        return self.menu.terminal.input(prompt)

    def go(self, page: str) -> None:
        self._require_menu().go(page)

    def back(self) -> None:
        self._require_menu().back()

    def exit(self) -> None:
        self._require_menu().exit()

    def _require_menu(self) -> PyMenu:
        if self.menu is None:
            raise RuntimeError('The page is not opened by a menu.')
        return self.menu
