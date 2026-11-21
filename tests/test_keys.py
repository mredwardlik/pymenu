import os
import sys
import threading

import pytest

from pymenu import keys


@pytest.mark.skipif(os.name == 'nt', reason='POSIX terminals only')
@pytest.mark.parametrize('data, expected', [
    (b'\x1b[A', keys.UP), (b'\x1b[B', keys.DOWN), (b'\x1bOA', keys.UP),
    (b'\x1b[H', keys.HOME), (b'\x1b[4~', keys.END),
    (b'\r', keys.ENTER), (b'\x7f', keys.BACKSPACE), (b'\x1b', keys.ESC),
    (b'\x03', keys.CTRL_C), (b'q', 'q'), ('ж'.encode(), 'ж'),
])
def test_posix_keys(monkeypatch, data, expected):
    import pty

    master, slave = pty.openpty()

    class FakeStdin:
        def fileno(self):
            return slave

    monkeypatch.setattr(sys, 'stdin', FakeStdin())
    # the key arrives while read_key() is already waiting, like a real key press
    timer = threading.Timer(0.1, os.write, (master, data))
    timer.start()
    try:
        assert keys.read_key() == expected
    finally:
        timer.join()
        os.close(master)
        os.close(slave)


@pytest.mark.skipif(os.name != 'nt', reason='Windows console only')
@pytest.mark.parametrize('chars, expected', [
    (['\xe0', 'H'], keys.UP), (['\xe0', 'P'], keys.DOWN), (['\x00', 'G'], keys.HOME),
    (['\r'], keys.ENTER), (['\x08'], keys.BACKSPACE), (['\x1b'], keys.ESC),
    (['\x03'], keys.CTRL_C), (['q'], 'q'), (['ж'], 'ж'),
])
def test_windows_keys(monkeypatch, chars, expected):
    import msvcrt

    queue = list(chars)
    monkeypatch.setattr(msvcrt, 'getwch', lambda: queue.pop(0))
    assert keys.read_key() == expected
