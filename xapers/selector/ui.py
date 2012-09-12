import sys
import subprocess
import urwid

from xapers.database import Database
from xapers.documents import Document

class UI():

    palette = [
        ('head_id', 'dark blue,bold', '', 'standout'),
        ('head_percent', 'yellow,bold', '', 'standout'),
        ('head_path', 'dark red,bold', '', 'standout'),
        ('head_tags', 'dark green,bold', '', 'standout'),
        ('head_sources', 'light magenta,bold', '', 'standout'),
        ('focus_id', 'white,bold', 'dark blue', 'standout'),
        ('title', 'dark green', ''),
        ('body', 'dark cyan', ''),
        ('focus', 'black', 'dark cyan'),

        ('header', 'white', 'dark blue'),
        ('footer', 'white', 'dark blue'),
        ]

    def __init__(self, xdir, cmd, args):
        self.xdir = xdir
        self.view = urwid.Frame(urwid.SolidFill())

        if cmd is 'search':
            from .search import Search
            self.cmd = Search(self, args)
            self.title = "search: " + args
        elif cmd is 'edit':
            from .edit import Edit
            self.cmd = Edit(self, args)
            self.title = "edit: " + args
        else:
            print >>sys.stderr, "Unknown command:", cmd
            sys.exit()

        self.view = urwid.Frame(urwid.AttrWrap(self.cmd, 'body'))

        self.set_header(self.title)
        self.set_status('foo')
        self.mainloop = urwid.MainLoop(
            self.view,
            self.palette,
            unhandled_input=self.keypress,
            handle_mouse=False,
            )
        self.mainloop.run()

    def set_header(self, text=None):
        if not text:
            message = 'Xapers'
        else:
            message = 'Xapers %s' % (text)
        self.view.set_header(urwid.AttrWrap(urwid.Text(message), 'header'))

    def set_status(self, text=None):
        if not text:
            message = 'Xapers'
        else:
            message = '%s' % (text)
        self.view.set_footer(urwid.AttrWrap(urwid.Text(message), 'footer'))

    def keypress(self, key):
        if key is 's':
            return
        if key is 'q':
            raise urwid.ExitMainLoop()
