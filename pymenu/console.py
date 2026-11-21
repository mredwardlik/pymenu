"""Terminals: how a page is shown and how the user chooses an element."""

from __future__ import annotations

import contextlib
import io
import sys
import typing as t
from dataclasses import dataclass, field

from rich.console import Console as RichConsole
from rich.console import Group as RichGroup
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pymenu import keys
from pymenu.elements import ElementInterface
from pymenu.triggers import CharsTrigger, normalize

__all__ = ['View', 'Choice', 'Console', 'InteractiveConsole', 'LineConsole', 'create_console']

ACCENT = 'cyan'


@dataclass
class View:
    """Everything needed to draw a page."""

    title: str
    elements: t.List[ElementInterface]
    description: t.Optional[str] = None
    breadcrumbs: t.List[str] = field(default_factory=list)
    messages: t.List[Text] = field(default_factory=list)
    highlight: int = 0
    can_go_back: bool = False

    @property
    def options(self) -> t.List[ElementInterface]:
        """Elements that can be chosen with the arrows and numbers."""
        return [e for e in self.elements if e.visible and e.selectable]

    def number(self, element: ElementInterface) -> t.Optional[int]:
        for i, option in enumerate(self.options, start=1):
            if option is element:
                return i
        return None

    def match(self, text: str) -> t.Optional[ElementInterface]:
        """The element chosen by typed text: a trigger, or a number."""
        trigger = CharsTrigger(text)
        if not trigger.content:
            return None
        for element in self.elements:
            if element.listen(trigger):
                return element
        if trigger.content.isdigit():
            index = int(trigger.content)
            if 1 <= index <= len(self.options):
                return self.options[index - 1]
        return None

    def is_prefix(self, text: str) -> bool:
        """``True`` if a longer trigger or number starts with ``text``."""
        text = normalize(text)
        words = [str(i) for i in range(1, len(self.options) + 1)]
        words += [trigger for element in self.elements for trigger in element.triggers]
        return any(word != text and word.startswith(text) for word in words)


@dataclass
class Choice:
    """What the user did on a page."""

    kind: t.Literal['select', 'back', 'exit']
    element: t.Optional[ElementInterface] = None
    highlight: int = 0


class Console:
    """Base terminal. ``choose`` shows a page and waits for the user."""

    interactive = False

    def __init__(self, console: t.Optional[RichConsole] = None):
        # bound to the real stdout, so captured action output doesn't hide it
        self.console = console or RichConsole(file=sys.stdout, highlight=False)

    def choose(self, view: View) -> Choice:
        raise NotImplementedError

    def input(self, prompt: str = '') -> str:
        return self.console.input(prompt)

    @contextlib.contextmanager
    def capture(self) -> t.Iterator[io.StringIO]:
        """Collect what an action prints."""
        buffer = io.StringIO()
        yield buffer

    def close(self) -> None:
        pass

    # drawing

    def render(self, view: View, highlight: t.Optional[int] = None) -> Panel:
        table = Table.grid(padding=(0, 1), expand=True)
        table.add_column(width=1)                       # pointer
        table.add_column(justify='right', style='dim')  # number
        table.add_column(ratio=1)                       # label
        table.add_column(justify='right', style='dim')  # triggers

        options = view.options
        for element in view.elements:
            if not element.visible:
                continue
            if not element.selectable:
                table.add_row('', '', Text.from_markup(element.label or '', style=element.style or ''), '')
                continue
            number = view.number(element)
            active = highlight is not None and options[highlight] is element
            label = Text.from_markup(element.label or '', style=element.style or '')
            if active:
                label.stylize(f'bold {ACCENT}')
            table.add_row(
                Text('❯', style=f'bold {ACCENT}') if active else '',
                str(number),
                label,
                ', '.join(element.triggers),
            )

        body: t.List[t.Any] = []
        if view.description:
            body += [Text.from_markup(view.description, style='dim'), '']
        body.append(table)
        return Panel(
            RichGroup(*body),
            title=Text(view.title, style=f'bold {ACCENT}'),
            title_align='left',
            subtitle=Text(' › '.join(view.breadcrumbs), style='dim') if len(view.breadcrumbs) > 1 else None,
            subtitle_align='right',
            border_style=ACCENT,
            padding=(1, 2),
            width=min(self.console.width, 72),
        )

    def print_messages(self, view: View) -> None:
        for message in view.messages:
            self.console.print(message)


class InteractiveConsole(Console):
    """Arrows and Enter, numbers and triggers, Esc to go back.

    :param read_key: function that returns the next key (see
        :mod:`pymenu.keys`). Tests pass a scripted one.
    :param clear: clear the screen before every frame.
    """

    interactive = True

    def __init__(self, console: t.Optional[RichConsole] = None,
                 read_key: t.Optional[t.Callable[[], str]] = None, clear: bool = True):
        super().__init__(console)
        self.read_key = read_key or keys.read_key
        self.clear = clear

    @contextlib.contextmanager
    def capture(self) -> t.Iterator[io.StringIO]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            yield buffer

    def frame(self, view: View, highlight: int, typed: str, error: t.Optional[str]) -> None:
        if self.clear:
            self.console.clear()
        self.console.print(self.render(view, highlight if view.options else None))
        self.print_messages(view)
        if error:
            self.console.print(Text(error, style='red'))
        self.console.print(Text.assemble(('› ', f'bold {ACCENT}'), typed, ('▏', ACCENT)))
        hints = ['↑↓ move', 'enter select', 'type a number or command']
        hints.append('esc back' if view.can_go_back else 'esc exit')
        self.console.print(Text(' · '.join(hints), style='dim'))

    def choose(self, view: View) -> Choice:
        options = view.options
        highlight = min(max(view.highlight, 0), max(len(options) - 1, 0))
        typed, error = '', None
        while True:
            self.frame(view, highlight, typed, error)
            error = None
            key = self.read_key()

            if key == keys.CTRL_C:
                return Choice('exit', highlight=highlight)
            if key in (keys.UP, keys.DOWN, keys.HOME, keys.END) and options:
                typed = ''
                highlight = {
                    keys.UP: (highlight - 1) % len(options),
                    keys.DOWN: (highlight + 1) % len(options),
                    keys.HOME: 0,
                    keys.END: len(options) - 1,
                }[key]
            elif key == keys.ENTER:
                if typed:
                    element = view.match(typed)
                    if element is None:
                        error = f'Unknown command: {typed}'
                        typed = ''
                        continue
                    return Choice('select', element, highlight)
                if options:
                    return Choice('select', options[highlight], highlight)
            elif key == keys.BACKSPACE:
                typed = typed[:-1]
            elif key == keys.ESC:
                if typed:
                    typed = ''
                else:
                    return Choice('back', highlight=highlight)
            elif len(key) == 1 and key.isprintable():
                typed += key
                element = view.match(typed)
                if element is not None and element in options:
                    highlight = options.index(element)
                # single keys and numbers work at once, words wait for Enter
                hotkey = len(typed) == 1 or typed.isdigit()
                if element is not None and hotkey and not view.is_prefix(typed):
                    return Choice('select', element, highlight)


class LineConsole(Console):
    """Line by line input: for pipes, scripts and terminals without raw keys.

    :param stdin: where to read lines from; ``sys.stdin`` by default.
    """

    def __init__(self, console: t.Optional[RichConsole] = None, stdin: t.Optional[t.TextIO] = None):
        super().__init__(console)
        self.stdin = stdin

    def readline(self, prompt: str) -> t.Optional[str]:
        self.console.print(Text(prompt, style=f'bold {ACCENT}'), end='')
        if self.stdin is None:
            try:
                line = input()
            except EOFError:
                return None
            if not sys.stdin.isatty():  # piped input is not echoed
                self.console.print(line, markup=False)
            return line
        line = self.stdin.readline()
        if not line:
            return None
        self.console.print(line.rstrip('\n'), markup=False)
        return line.rstrip('\n')

    def input(self, prompt: str = '') -> str:
        line = self.readline(prompt)
        if line is None:
            raise EOFError
        return line

    def choose(self, view: View) -> Choice:
        self.console.print(self.render(view))
        self.print_messages(view)
        while True:
            line = self.readline('› ')
            if line is None:
                return Choice('exit')
            if not line.strip():
                continue
            element = view.match(line)
            if element is not None:
                return Choice('select', element)
            self.console.print(Text(f'Unknown command: {line.strip()}', style='red'))


def create_console() -> Console:
    """Arrow keys in a real terminal, line input otherwise."""
    if sys.stdin.isatty() and sys.stdout.isatty():
        return InteractiveConsole()
    return LineConsole()


def message(*objects: t.Any, style: t.Optional[str] = None) -> Text:
    parts = [obj if isinstance(obj, str) else repr(obj) for obj in objects]
    try:
        text = Text.from_markup(' '.join(parts))
    except Exception:
        text = Text(escape(' '.join(parts)))
    if style:
        text.stylize(style)
    return text
