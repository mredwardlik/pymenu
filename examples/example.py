"""A small to-do app built with pymenu.

    python examples/example.py

Use the arrows and Enter, type a number, or type a command shown on the
right (for example "a" to add a task). Esc goes back.
"""

from pymenu import Back, Exit, Hidden, Item, Page, PyMenu, Redirect, Text

menu = PyMenu()

tasks = [
    {'title': 'Write the README', 'done': True},
    {'title': 'Add arrow keys to pymenu', 'done': True},
    {'title': 'Publish the release', 'done': False},
]
settings = {'show_done': True, 'newest_first': False}


def open_tasks():
    return sum(not task['done'] for task in tasks)


@menu.page('home')
class Home(Page):
    title = 'To-do'
    description = 'A tiny task list. Everything here is built with pymenu pages.'

    def build(self):
        return (
            Redirect('tasks', f'Tasks  [dim]({open_tasks()} open)[/dim]', triggers='t'),
            Item('Add a task', action=self.add, triggers='a'),
            Redirect('settings', 'Settings', triggers='s'),
            Text(),
            Exit('Quit', triggers='q'),
            # not shown: type "history" and press Enter
            Hidden(action=lambda: self.print(f'History: {self.context.history}'), triggers='history'),
        )

    def add(self):
        title = self.input('New task: ').strip()
        if not title:
            self.print('Nothing added.', style='yellow')
            return
        tasks.append({'title': title, 'done': False})
        self.print(f'Added “{title}”.', style='green')


@menu.page('tasks')
class Tasks(Page):
    title = 'Tasks'

    def build(self):
        shown = [task for task in tasks if settings['show_done'] or not task['done']]
        if settings['newest_first']:
            shown = shown[::-1]
        items = [
            Item(
                ('[green]✔[/green] [dim strike]' if task['done'] else '[yellow]○[/yellow] ') + task['title']
                + ('[/dim strike]' if task['done'] else ''),
                action=lambda task=task: self.toggle(task),
            )
            for task in shown
        ]
        return (
            Text('Enter marks a task as done or not done.', style='dim'),
            Text(),
            *(items or [Text('No tasks to show.', style='italic')]),
            Text(),
            Item('Remove done tasks', action=self.clear, triggers='c'),
            Back('Back', triggers='b'),
        )

    def toggle(self, task):
        task['done'] = not task['done']

    def clear(self):
        before = len(tasks)
        tasks[:] = [task for task in tasks if not task['done']]
        self.print(f'Removed {before - len(tasks)} done task(s).', style='green')


@menu.page('settings')
class Settings(Page):
    title = 'Settings'

    def build(self):
        def switch(name):
            return lambda: settings.update({name: not settings[name]})

        def state(name):
            return '[green]on[/green]' if settings[name] else '[red]off[/red]'

        return (
            Item(f'Show done tasks: {state("show_done")}', action=switch('show_done')),
            Item(f'Newest first:    {state("newest_first")}', action=switch('newest_first')),
            Text(),
            Redirect('about', 'About'),
            Back('Back', triggers='b'),
        )


@menu.none
def missing(pagename):
    menu.message(f'Page "{pagename}" is not ready yet.', style='yellow')


if __name__ == '__main__':
    menu.run('home')
