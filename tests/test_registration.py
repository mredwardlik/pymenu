import pytest

from pymenu import Item, Page, PyMenu, LineConsole


def make():
    return PyMenu(LineConsole())


def test_decorator_without_brackets():
    menu = make()

    @menu.page
    class Home(Page):
        def build(self):
            return Item('x')

    assert menu.pages == (('Home', Home),)


def test_decorator_with_empty_brackets_and_name():
    menu = make()

    @menu.page()
    class First(Page):
        pass

    @menu.page('second')
    class Second(Page):
        pass

    assert [name for name, _ in menu.pages] == ['First', 'second']


def test_only_pages_can_be_registered():
    menu = make()
    with pytest.raises(TypeError):
        @menu.page('x')
        class NotAPage:
            pass


def test_duplicate_names():
    menu = make()

    @menu.page('home')
    class A(Page):
        pass

    with pytest.raises(ValueError):
        @menu.page('home')
        class B(Page):
            pass


def test_run_without_pages():
    with pytest.raises(RuntimeError):
        make().run()


def test_page_without_build():
    menu = make()

    @menu.page
    class Empty(Page):
        pass

    with pytest.raises(NotImplementedError):
        Empty(menu.context, menu).build()
