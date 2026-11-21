from pymenu import Item, Page

from conftest import output


def test_input_print_and_state(keys_menu):
    menu = keys_menu('1', '1', '2', '\x03' if False else 'ctrl+c', inputs=['Alice'])

    @menu.page('home')
    class Home(Page):
        def build(self):
            name = self.context.data.get('name', 'nobody')
            return (
                Item(f'Name: {name}', action=self.ask),
                Item('Greet', action=lambda: self.print(f'Hello, [bold]{name}[/bold]!', style='green')),
            )

        def ask(self):
            self.context.data['name'] = self.input('Your name: ')

    menu.run()
    out = output(menu)
    assert 'Name: Alice' in out
    assert 'Hello, Alice!' in out


def test_page_navigation_helpers(keys_menu):
    menu = keys_menu('1', '1', '1')

    @menu.page('a')
    class A(Page):
        def build(self):
            return Item('to b', action=lambda: self.go('b'))

    @menu.page('b')
    class B(Page):
        def build(self):
            return Item('back', action=self.back)

    # a -> b -> back to a -> b ... then exit from b
    menu.terminal.read_key.keys += ['ctrl+c']
    context = menu.run('a')
    assert context.history == ['a', 'b']


def test_dynamic_labels(keys_menu):
    menu = keys_menu('1', '1', 'ctrl+c')
    counter = {'n': 0}

    @menu.page
    class Counter(Page):
        def build(self):
            return Item(f'Clicked {counter["n"]} times', action=lambda: counter.update(n=counter['n'] + 1))

    menu.run()
    assert 'Clicked 2 times' in output(menu)
