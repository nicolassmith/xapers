"""
This file is part of xapers.

Xapers is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

Xapers is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with notmuch.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2012, 2013
Jameson Rollins <jrollins@finestructure.net>
"""

import os
import sys
import urwid

from ..cli import initdb
from search import Search
from bibview import Bibview
from help import Help

############################################################

class UI():

    palette = [
        ('header', 'white', 'dark blue'),
        ('footer', 'white', 'dark blue'),
        ('prompt', 'black', 'light green'),
        ]

    keys = {
        '?': "help",
        's': "promptSearch",
        'q': "killBuffer",
        'Q': "quit",
        }

    def __init__(self, cmd=None):
        self.db = initdb()

        self.header_string = "Xapers"
        self.status_string = "s: search, q: kill buffer, Q: quit Xapers, ?: help and additional commands"

        self.view = urwid.Frame(urwid.SolidFill())
        self.set_header()
        self.set_status()
        self.devnull = open('/dev/null', 'rw')

        if not cmd:
            cmd = ['search', '*']

        if cmd[0] == 'search':
            query = ' '.join(cmd[1:])
            self.buffer = Search(self, query)
        elif cmd[0] == 'bibview':
            query = ' '.join(cmd[1:])
            self.buffer = Bibview(self, query)
        elif cmd[0] == 'help':
            target = None
            if len(cmd) > 1:
                target = cmd[1]
            if isinstance(target, str):
                target = None
            self.buffer = Help(self, target)
        else:
            self.buffer = Help(self)
            self.set_status("Unknown command '%s'." % (cmd[0]))

        self.merge_palette(self.buffer)

        self.view.body = urwid.AttrMap(self.buffer, 'body')

        self.mainloop = urwid.MainLoop(
            self.view,
            self.palette,
            unhandled_input=self.keypress,
            handle_mouse=False,
            )
        self.mainloop.screen.set_terminal_properties(colors=88)
        self.mainloop.run()

    ##########

    def merge_palette(self, buffer):
        if hasattr(buffer, 'palette'):
            self.palette = list(set(self.palette) | set(buffer.palette))

    def set_header(self, widget=[]):
        header = urwid.Columns([('pack', urwid.Text('Xapers '))] + widget)
        self.view.set_header(urwid.AttrMap(header, 'header'))

    def set_status(self, text=None):
        if text:
            self.status_string = '%s' % (text)
        self.view.set_footer(urwid.AttrMap(urwid.Text(self.status_string), 'footer'))

    def newbuffer(self, cmd):
        UI(cmd=cmd)
        self.set_status()

    def prompt(self, string):
        prompt = PromptEdit(string)
        self.view.set_footer(urwid.AttrMap(prompt, 'prompt'))
        self.view.set_focus('footer')
        return prompt

    ##########

    def promptSearch(self):
        """search database"""
        prompt = 'search: '
        urwid.connect_signal(self.prompt(prompt), 'done', self._promptSearch_done)

    def _promptSearch_done(self, query):
        self.view.set_focus('body')
        urwid.disconnect_signal(self, self.prompt, 'done', self._promptSearch_done)
        if not query:
            self.set_status()
            return
        self.newbuffer(['search', query])

    def killBuffer(self):
        """kill current buffer (quit if last buffer)"""
        raise urwid.ExitMainLoop()

    def quit(self):
        """quit Xapers"""
        sys.exit()

    def help(self):
        """help"""
        self.newbuffer(['help', self.buffer])

    def keypress(self, key):
        if key in self.keys:
            cmd = "self.%s()" % (self.keys[key])
            eval(cmd)

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
