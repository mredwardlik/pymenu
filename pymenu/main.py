from __future__ import annotations

import typing as t

from rich.text import Text

from pymenu.console import Console, View, create_console, message
from pymenu.context import Context
from pymenu.elements import flatten
from pymenu.holder import Holder
from pymenu.page import Page

__all__ = ['PyMenu']

P = t.TypeVar('P', bound=t.Type[Page])


class PyMenu:
    """A console menu made of pages.

    >>> from pymenu import Item, LineConsole
    >>> menu = PyMenu(LineConsole())
    >>> @menu.page('home')
    ... class Home(Page):
    ...     def build(self):
    ...         return Item('Hello', action=lambda: self.print('Hi!'))
    >>> menu.pages
    (('home', <class 'pymenu.main.Home'>),)

    :param terminal: how pages are shown and read. By default arrow keys in
        a real terminal and line input when the input is piped.
    """

    def __init__(self, terminal: t.Optional[Console] = None):
        self.pageholder: Holder = Holder()  # {pagename: pageclass}
        self.context: Context = Context()
        self.terminal: Console = terminal or create_console()
        self._none: t.Optional[t.Callable[[str], t.Any]] = None
        self._messages: t.List[Text] = []
        self._highlight: t.Dict[t.Tuple[int, str], int] = {}
        self._running = False

    @property
    def pages(self) -> t.Tuple[t.Tuple[str, t.Type[Page]], ...]:
        return tuple(self.pageholder.items())

    # registration

    @t.overload
    def page(self, page: P) -> P: ...
    @t.overload
    def page(self, page: t.Optional[str] = None) -> t.Callable[[P], P]: ...

    def page(self, page: t.Union[P, str, None] = None) -> t.Any:
        """Register a page class. Works as ``@menu.page``, ``@menu.page()``
        and ``@menu.page('name')``. Without a name the class name is used."""
        def decorator(pageclass: P, pagename: t.Optional[str] = None) -> P:
            if not (isinstance(pageclass, type) and issubclass(pageclass, Page)):
                raise TypeError(f'{pageclass!r} must be inherited from Page class.')
            name = pagename or pageclass.__name__
            if not self.pageholder.add(name, pageclass):
                raise ValueError(f'Page "{name}" is already registered.')
            return pageclass

        if isinstance(page, str) or page is None:
            return lambda pageclass: decorator(pageclass, page)
        return decorator(page)

    def none(self, f: t.Callable[[str], t.Any]) -> t.Callable[[str], t.Any]:
        """Register a function that is called with the page name when a
        missing page is opened."""
        self._none = f
        return f

    # navigation

    def go(self, pagename: str) -> None:
        """Open a page. The current page stays in the history."""
        if not self.pageholder.haskey(pagename):
            if self._none is not None:
                self._none(pagename)
            else:
                self.message(f'Page "{pagename}" does not exist.', style='red')
            return
        if self.context.page != pagename:
            self.context.history.append(pagename)

    def back(self) -> None:
        """Return to the previous page. On the first page the menu closes."""
        if self.context.history:
            self._highlight.pop((len(self.context.history), self.context.history[-1]), None)
            self.context.history.pop()
        if not self.context.history:
            self._running = False

    def exit(self) -> None:
        """Close the menu after the current action."""
        self._running = False

    def message(self, *objects: t.Any, style: t.Optional[str] = None) -> None:
        """Show a message under the menu on the next render."""
        self._messages.append(message(*objects, style=style))

    # loop

    def run(self, pagename: t.Optional[str] = None) -> Context:
        """Show the menu until the user leaves it. Starts on ``pagename`` or
        on the first registered page. Returns the context."""
        if not self.pageholder:
            raise RuntimeError('Register at least one page with @menu.page.')
        start = pagename or next(iter(self.pageholder))
        if not self.pageholder.haskey(start):
            if self._none is not None:
                self._none(start)
                return self.context
            raise KeyError(f'Page "{start}" does not exist.')

        self.context.history = [start]
        self._running = True
        current: t.Optional[t.Tuple[int, str]] = None
        instance: t.Optional[Page] = None
        try:
            while self._running and self.context.history:
                key = (len(self.context.history), self.context.history[-1])
                if key != current or instance is None:
                    instance = self.pageholder[key[1]](self.context, self)
                    current = key
                view = View(
                    title=instance.get_title(),
                    description=instance.description,
                    elements=flatten(instance.build()),
                    breadcrumbs=[self._title(name) for name in self.context.history],
                    messages=self._messages,
                    highlight=self._highlight.get(key, 0),
                    can_go_back=len(self.context.history) > 1,
                )
                self._messages = []
                choice = self.terminal.choose(view)
                self._highlight[key] = choice.highlight
                if choice.kind == 'exit':
                    self.exit()
                elif choice.kind == 'back':
                    self.back()
                elif choice.element is not None:
                    self._activate(choice.element)
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False
            self.terminal.close()
        return self.context

    def _activate(self, element: t.Any) -> None:
        with self.terminal.capture() as output:
            try:
                element.activate(self)
            except (KeyboardInterrupt, EOFError):
                self.message('Cancelled.', style='yellow')
            except Exception as error:  # show it and keep the menu open
                self.message(f'{error.__class__.__name__}: {error}', style='red')
        printed = output.getvalue().rstrip('\n')
        if printed:
            self._messages.insert(0, Text.from_ansi(printed))

    def _title(self, pagename: str) -> str:
        pageclass = self.pageholder.get(pagename)
        return (pageclass.title or pageclass.__name__) if pageclass else pagename
