import sys
import subprocess
import urwid

from xapers.database import Database
from xapers.documents import Document

class UI():

    palette = [
        ('head_id', 'dark red,bold', '', 'standout'),
        ('focus_id', 'white,bold', 'dark blue', 'standout'),
        ('search_sources', 'light magenta,bold', '', 'standout'),
        ('search_tags', 'dark green,bold', '', 'standout'),
        ('search_title', 'yellow,bold', '', 'standout'),
        ('search_path', 'dark red', '', 'standout'),
        ('search_value_default', 'dark cyan', ''),
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
        self.set_status("enter to view document, u to view url.")
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

    def set_prompt(self, prompt):
        # prompt is an Edit object
        self.view.set_footer(urwid.AttrWrap(prompt, 'prompt'))
        self.view.set_focus('footer')

    def keypress(self, key):
        if key is 's':
            return
        if key is 'q':
            raise urwid.ExitMainLoop()
