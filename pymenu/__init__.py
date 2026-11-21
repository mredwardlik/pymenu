"""Console menus made of pages, with arrow keys, numbers and commands."""

from pymenu import page as page
from pymenu.console import InteractiveConsole, LineConsole
from pymenu.context import Context
from pymenu.elements import Back, Exit, Group, Hidden, Item, Redirect, Text
from pymenu.main import PyMenu
from pymenu.page import Page

__version__ = '1.0.0'
__all__ = [
    'PyMenu', 'Page', 'Context',
    'Group', 'Item', 'Hidden', 'Redirect', 'Back', 'Exit', 'Text',
    'InteractiveConsole', 'LineConsole',
]
