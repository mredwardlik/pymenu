from pymenu import Back, Exit, Group, Hidden, Item, Page, Redirect, Text
from pymenu.keys import DOWN, END, ENTER, ESC, BACKSPACE, UP, CTRL_C, HOME

from conftest import output


def register(menu, log):
    @menu.page('home')
    class Home(Page):
        title = 'Home'

        def build(self):
            return Group(
                Text('Welcome'),
                Item('Say hello', action=lambda: log.append('hello'), triggers=('h', 'hello')),
                Redirect('work', 'Go to work', triggers='w'),
                Hidden(action=lambda: log.append('secret'), triggers='secret'),
                Exit('Quit', triggers='q'),
            )

    @menu.page('work')
    class Work(Page):
        title = 'Work'

        def build(self):
            return [
                Item('Write report', action=lambda: log.append('report')),
                Item('Print', action=lambda: print('printed by action')),
                Item('Fail', action=lambda: 1 / 0),
                Redirect('nowhere', 'Broken link'),
                Back(),
            ]

    return menu


def test_arrows_and_enter(keys_menu):
    log = []
    menu = register(keys_menu(ENTER, DOWN, ENTER, ENTER, ESC, UP, UP, ENTER), log)
    context = menu.run('home')
    # Enter on "Say hello", Down + Enter opens work, Enter on "Write report",
    # Esc back home (highlight is remembered on "Go to work"), Up Up wraps to "Quit"
    assert log == ['hello', 'report']
    assert context.history == ['home']


def test_numbers_and_triggers(keys_menu):
    log = []
    menu = register(keys_menu('1', 'w', '1', ESC, 'hello', ENTER, 'secret', ENTER, 'q'), log)
    menu.run('home')
    assert log == ['hello', 'report', 'hello', 'secret']


def test_prefix_waits_for_enter(keys_menu):
    log = []
    # "h" is both a trigger and the start of "hello": Enter confirms it
    menu = register(keys_menu('h', ENTER, CTRL_C), log)
    menu.run('home')
    assert log == ['hello']


def test_unknown_command_and_editing(keys_menu):
    log = []
    menu = register(keys_menu('xyz', ENTER, 'hellx', BACKSPACE, 'o', ENTER, 'abc', ESC, 'q'), log)
    menu.run('home')
    assert log == ['hello']
    assert 'Unknown command: xyz' in output(menu)


def test_home_end(keys_menu):
    log = []
    menu = register(keys_menu(END, UP, UP, UP, HOME, ENTER, 'q'), log)
    menu.run('home')
    assert log == ['hello']


def test_back_from_first_page_closes(keys_menu):
    menu = register(keys_menu(ESC), [])
    assert menu.run('home').history == []


def test_back_element(keys_menu):
    menu = register(keys_menu('w', '5', 'q'), [])
    assert menu.run('home').history == ['home']


def test_printed_output_and_errors_are_shown(keys_menu):
    menu = register(keys_menu('w', '2', '3', CTRL_C), [])
    menu.run('home')
    out = output(menu)
    assert 'printed by action' in out
    assert 'ZeroDivisionError: division by zero' in out


def test_missing_page_message(keys_menu):
    menu = register(keys_menu('w', '4', CTRL_C), [])
    menu.run('home')
    assert 'Page "nowhere" does not exist.' in output(menu)


def test_none_handler(keys_menu):
    seen = []
    menu = register(keys_menu('w', '4', CTRL_C), [])
    menu.none(seen.append)
    menu.run('home')
    assert seen == ['nowhere']


def test_breadcrumbs_and_highlight(keys_menu):
    menu = register(keys_menu(DOWN, CTRL_C), [])
    menu.run('home')
    out = output(menu)
    assert '❯ 2 Go to work' in out
    assert '› hello' not in out


def test_line_mode(line_menu):
    log = []
    menu = register(line_menu('', 'nope', '1', 'W', '1', '5', 'q'), log)
    context = menu.run('home')
    assert log == ['hello', 'report']
    assert 'Unknown command: nope' in output(menu)
    assert context.history == ['home']


def test_line_mode_end_of_input(line_menu):
    log = []
    menu = register(line_menu('1'), log)
    menu.run('home')
    assert log == ['hello']


def test_starts_on_first_page(line_menu):
    log = []
    menu = register(line_menu('h'), log)
    menu.run()
    assert log == ['hello']
