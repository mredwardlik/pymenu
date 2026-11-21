from __future__ import annotations

import typing as t
from abc import ABC

from pymenu.triggers import Trigger, normalize

if t.TYPE_CHECKING:
    from pymenu.main import PyMenu

__all__ = [
    'ElementInterface', 'Element', 'Group', 'Item', 'Hidden',
    'Redirect', 'Back', 'Exit', 'Text', 'flatten',
]

Action = t.Callable[[], t.Any]
Triggers = t.Union[str, t.Iterable[str], None]


def _triggers(triggers: Triggers) -> t.Tuple[str, ...]:
    if triggers is None:
        return ()
    if isinstance(triggers, str):
        triggers = (triggers,)
    return tuple(normalize(trigger) for trigger in triggers if normalize(trigger))


class ElementInterface(ABC):
    """Anything a page can show."""

    #: shown in the list
    visible: bool = True
    #: can be chosen with the arrows or a number
    selectable: bool = False
    label: t.Optional[str] = None
    style: t.Optional[str] = None
    triggers: t.Tuple[str, ...] = ()

    def listen(self, trigger: Trigger) -> bool:
        """``True`` if the typed text is one of the element's triggers."""
        return trigger.content in self.triggers

    def activate(self, menu: PyMenu) -> None:
        """Called when the user chooses the element."""


class Element(ElementInterface):
    selectable = True

    def __init__(self, label: t.Optional[str] = None, triggers: Triggers = None, style: t.Optional[str] = None):
        self.label = label
        self.triggers = _triggers(triggers)
        self.style = style

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.label!r})'


class Item(Element):
    """A menu line that runs ``action`` when chosen.

    :param label: text of the line.
    :param action: function without arguments.
    :param triggers: words or keys that choose the item, for example
        ``('h', 'help')``.
    """

    def __init__(self, label: str, action: t.Optional[Action] = None, triggers: Triggers = None,
                 style: t.Optional[str] = None):
        super().__init__(label, triggers, style)
        self.action = action

    def activate(self, menu: PyMenu) -> None:
        if self.action is not None:
            self.action()


class Hidden(Item):
    """Not shown in the list, works only through its triggers: secret
    commands and shortcuts."""

    visible = False
    selectable = False

    def __init__(self, action: Action, triggers: Triggers):
        super().__init__('', action, triggers)
        if not self.triggers:
            raise ValueError('Hidden element needs at least one trigger.')


class Redirect(Element):
    """Opens another page.

    :param to: name of the page.
    :param label: text of the line; the page title by default.
    """

    def __init__(self, to: str, label: t.Optional[str] = None, triggers: Triggers = None,
                 style: t.Optional[str] = None):
        super().__init__(label, triggers, style)
        self.to = to

    def activate(self, menu: PyMenu) -> None:
        menu.go(self.to)


class Back(Element):
    """Returns to the previous page, or closes the menu on the first one."""

    def __init__(self, label: str = 'Back', triggers: Triggers = None, style: t.Optional[str] = 'dim'):
        super().__init__(label, triggers, style)

    def activate(self, menu: PyMenu) -> None:
        menu.back()


class Exit(Element):
    """Closes the menu."""

    def __init__(self, label: str = 'Exit', triggers: Triggers = None, style: t.Optional[str] = 'dim'):
        super().__init__(label, triggers, style)

    def activate(self, menu: PyMenu) -> None:
        menu.exit()


class Text(ElementInterface):
    """A line of text that can't be chosen: a heading, a hint or an empty
    line between groups. Supports rich markup."""

    def __init__(self, text: str = '', style: t.Optional[str] = None):
        self.label = text
        self.style = style

    def __repr__(self) -> str:
        return f'Text({self.label!r})'


class Group(ElementInterface):
    """Several elements returned from :meth:`Page.build` as one."""

    visible = False

    def __init__(self, *childs: t.Union[ElementInterface, t.Iterable[ElementInterface], None]):
        self.childs: t.List[ElementInterface] = flatten(childs)

    def __iter__(self) -> t.Iterator[ElementInterface]:
        return iter(self.childs)

    def __repr__(self) -> str:
        return f'Group({", ".join(map(repr, self.childs))})'


def flatten(elements: t.Any) -> t.List[ElementInterface]:
    """All elements in order, with groups and lists opened and ``None``
    skipped."""
    result: t.List[ElementInterface] = []
    if elements is None:
        return result
    if isinstance(elements, Group):
        return list(elements.childs)
    if isinstance(elements, ElementInterface):
        return [elements]
    for element in elements:
        result.extend(flatten(element))
    return result
