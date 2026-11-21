"""Reading single key presses without waiting for Enter."""

from __future__ import annotations

import os
import sys

__all__ = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'HOME', 'END', 'ENTER', 'BACKSPACE', 'ESC', 'CTRL_C', 'TAB', 'read_key']

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'
HOME = 'home'
END = 'end'
ENTER = 'enter'
BACKSPACE = 'backspace'
ESC = 'escape'
CTRL_C = 'ctrl+c'
TAB = 'tab'

SPECIAL = {UP, DOWN, LEFT, RIGHT, HOME, END, ENTER, BACKSPACE, ESC, CTRL_C, TAB}

_CONTROL = {
    '\r': ENTER, '\n': ENTER, '\t': TAB,
    '\x08': BACKSPACE, '\x7f': BACKSPACE,
    '\x1b': ESC, '\x03': CTRL_C,
}

if os.name == 'nt':
    import msvcrt

    _WINDOWS_ARROWS = {'H': UP, 'P': DOWN, 'K': LEFT, 'M': RIGHT, 'G': HOME, 'O': END}

    def read_key() -> str:
        """Wait for a key and return it: a character or one of the constants."""
        char = msvcrt.getwch()
        if char in ('\x00', '\xe0'):
            return _WINDOWS_ARROWS.get(msvcrt.getwch(), '')
        return _CONTROL.get(char, char)

else:
    import codecs
    import select
    import termios
    import tty

    _SEQUENCES = {
        '[A': UP, '[B': DOWN, '[C': RIGHT, '[D': LEFT,
        'OA': UP, 'OB': DOWN, 'OC': RIGHT, 'OD': LEFT,
        '[H': HOME, '[F': END, 'OH': HOME, 'OF': END,
        '[1~': HOME, '[4~': END, '[7~': HOME, '[8~': END,
    }

    def _read_char(fd: int, decoder: codecs.IncrementalDecoder) -> str:
        while True:
            char = decoder.decode(os.read(fd, 1))
            if char:
                return char

    def _ready(fd: int, timeout: float = 0.03) -> bool:
        return bool(select.select([fd], [], [], timeout)[0])

    def read_key() -> str:
        """Wait for a key and return it: a character or one of the constants."""
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        try:
            # TCSANOW keeps keys typed in advance (TCSAFLUSH would drop them)
            tty.setraw(fd, termios.TCSANOW)
            char = _read_char(fd, decoder)
            if char != '\x1b' or not _ready(fd):
                return _CONTROL.get(char, char)
            sequence = ''
            while _ready(fd) and len(sequence) < 6:
                sequence += _read_char(fd, decoder)
                if sequence in _SEQUENCES:
                    return _SEQUENCES[sequence]
            return ''
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
