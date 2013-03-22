import os
import sys
import urwid
import subprocess

from xapers.cli.ui import initdb
from xapers.nci.search import Search
from xapers.nci.bibview import Bibview

############################################################

class UI():

    palette = [
        ('header', 'white', 'dark blue'),
        ('footer', 'white', 'dark blue'),
        ('prompt', 'black', 'light green'),
        ]

    palette_search = [
        ('field', 'dark cyan', ''),
        ('field_focus', '', 'dark cyan'),
        ('head', 'dark blue,bold', '', 'standout'),
        ('head_focus', 'white,bold', 'dark blue', 'standout'),
        ('sources', 'light magenta,bold', '', 'standout'),
        ('sources_focus', 'light magenta,bold', '', 'standout'),
        ('tags', 'dark green,bold', '', 'standout'),
        ('tags_focus', 'dark green,bold', '', 'standout'),
        ('title', 'yellow,bold', '', 'standout'),
        ('title_focus', 'yellow,bold', '', 'standout'),
        ('default', 'dark cyan', ''),
        ('default_focus', '', 'dark cyan'),
        ]

    def __init__(self, xdir, db=None, cmd=None):
        self.xdir = xdir
        if db:
            # reuse db if provided
            self.db = db
        else:
            self.db = initdb(self.xdir)

        self.header_string = "Xapers"
        self.status_string = "'s' to search."

        self.view = urwid.Frame(urwid.SolidFill())
        self.set_header()
        self.set_status()

        palette = self.palette

        if not cmd:
            cmd = ['search', '*']

        if cmd[0] == 'search':
            query = ' '.join(cmd[1:])
            self.buffer = Search(self, query)
            palette = list(set(self.palette) | set(self.palette_search))
        elif cmd[0] == 'bibview':
            query = ' '.join(cmd[1:])
            self.buffer = Bibview(self, query)

        self.view.body = urwid.AttrMap(self.buffer, 'body')

        self.mainloop = urwid.MainLoop(
            self.view,
            palette,
            unhandled_input=self.keypress,
            handle_mouse=False,
            )
        self.mainloop.run()

    ##########

    def set_header(self, text=None):
        if text:
            self.header_string = 'Xapers %s' % (text)
        self.view.set_header(urwid.AttrMap(urwid.Text(self.header_string), 'header'))

    def set_status(self, text=None):
        if text:
            self.status_string = '%s' % (text)
        self.view.set_footer(urwid.AttrMap(urwid.Text(self.status_string), 'footer'))

    def newbuffer(self, cmd):
        UI(self.xdir, db=self.db, cmd=cmd)
        self.set_status()

    def prompt(self, string):
        prompt = PromptEdit(string)
        self.view.set_footer(urwid.AttrMap(prompt, 'prompt'))
        self.view.set_focus('footer')
        return prompt

    ##########

    def promptSearch(self):
        prompt = 'search: '
        urwid.connect_signal(self.prompt(prompt), 'done', self.promptSearch_done)

    def promptSearch_done(self, query):
        self.view.set_focus('body')
        urwid.disconnect_signal(self, self.prompt, 'done', self.promptSearch_done)
        if not query:
            self.set_status()
            return
        self.newbuffer(['search', query])

    ##########

    def keypress(self, key):
        if key is 's':
            self.promptSearch()
        if key is 'q':
            raise urwid.ExitMainLoop()
        if key is 'Q':
            sys.exit()

############################################################

class PromptEdit(urwid.Edit):
    __metaclass__ = urwid.signals.MetaSignals
    signals = ['done']

    def keypress(self, size, key):
        if key == 'enter':
            urwid.emit_signal(self, 'done', self.get_edit_text())
            return
        elif key == 'esc':
            urwid.emit_signal(self, 'done', None)
            return

        urwid.Edit.keypress(self, size, key)
