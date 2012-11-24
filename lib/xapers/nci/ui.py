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
        ('head_id', 'dark blue,bold', '', 'standout'),
        ('focus_id', 'white,bold', 'dark blue', 'standout'),
        ('search_sources', 'light magenta,bold', '', 'standout'),
        ('search_tags', 'dark green,bold', '', 'standout'),
        ('search_title', 'yellow,bold', '', 'standout'),
        ('search_path', 'dark red', '', 'standout'),
        ('search_value_default', 'dark cyan', ''),
        ('focus', 'black', 'dark cyan'),

        ('header', 'white', 'dark blue'),
        ('footer', 'white', 'dark blue'),
        ('prompt', 'black', 'light green'),
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

        if not cmd:
            cmd = ['search', '*']
        if cmd[0] == 'search':
            query = ' '.join(cmd[1:])
            widget = Search(self, query)
        elif cmd[0] == 'bibview':
            query = ' '.join(cmd[1:])
            widget = Bibview(self, query)

        self.view.body = urwid.AttrWrap(widget, 'body')

        self.mainloop = urwid.MainLoop(
            self.view,
            self.palette,
            unhandled_input=self.keypress,
            handle_mouse=False,
            )
        self.mainloop.run()

    ##########

    def set_header(self, text=None):
        if text:
            self.header_string = 'Xapers %s' % (text)
        self.view.set_header(urwid.AttrWrap(urwid.Text(self.header_string), 'header'))

    def set_status(self, text=None):
        if text:
            self.status_string = '%s' % (text)
        self.view.set_footer(urwid.AttrWrap(urwid.Text(self.status_string), 'footer'))

    def newbuffer(self, cmd):
        UI(self.xdir, db=self.db, cmd=cmd)
        self.set_status()

    def prompt(self, string):
        prompt = PromptEdit(string)
        self.view.set_footer(urwid.AttrWrap(prompt, 'prompt'))
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
