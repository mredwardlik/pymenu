import io

import pytest
from rich.console import Console as RichConsole

from pymenu import InteractiveConsole, LineConsole, PyMenu


def rich_console():
    return RichConsole(file=io.StringIO(), width=80, color_system=None, legacy_windows=False)


class Keys:
    """Scripted key presses for InteractiveConsole."""

    def __init__(self, *keys):
        self.keys = []
        for key in keys:
            # plain strings are typed character by character
            self.keys.extend([key] if key in KEY_NAMES else list(key))

    def __call__(self):
        if not self.keys:
            raise AssertionError('The menu asked for more keys than the test has.')
        return self.keys.pop(0)


from pymenu.keys import SPECIAL as KEY_NAMES  # noqa: E402


@pytest.fixture
def keys_menu():
    def make(*keys, inputs=()):
        terminal = InteractiveConsole(console=rich_console(), read_key=Keys(*keys), clear=False)
        answers = list(inputs)
        terminal.input = lambda prompt='': answers.pop(0)
        return PyMenu(terminal)
    return make


@pytest.fixture
def line_menu():
    def make(*lines):
        stdin = io.StringIO(''.join(line + '\n' for line in lines))
        return PyMenu(LineConsole(console=rich_console(), stdin=stdin))
    return make


def output(menu):
    return menu.terminal.console.file.getvalue()
