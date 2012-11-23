import os
import sys
import urwid
import subprocess

from xapers.nci.search import Search

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

    def __init__(self, cmd=None):
        try:
            self.xdir = os.environ['XAPERS_DIR']
        except:
            print >>sys.stderr, "XAPERS_DIR environment variable not specified."
            sys.exit(1)
        if not os.path.isdir(self.xdir):
            print >>sys.stderr, "XAPERS_DIR '%s' does not exist." % (self.xdir)
            sys.exit(2)

        self.header_string = "Xapers"
        self.status_string = "'s' to search."

        self.view = urwid.Frame(urwid.SolidFill())
        self.set_header()
        self.set_status()

        if not cmd:
            cmd = ['search', '*']
        if cmd and cmd[0] == 'search':
            query = ' '.join(cmd[1:])
            self.view.body = urwid.AttrWrap(Search(self, query), 'body')

        self.mainloop = urwid.MainLoop(
            self.view,
            self.palette,
            unhandled_input=self.keypress,
            handle_mouse=False,
            )
        self.mainloop.run()

    def set_header(self, text=None):
        if text:
            self.header_string = 'Xapers %s' % (text)
        self.view.set_header(urwid.AttrWrap(urwid.Text(self.header_string), 'header'))

    def set_status(self, text=None):
        if text:
            self.status_string = '%s' % (text)
        self.view.set_footer(urwid.AttrWrap(urwid.Text(self.status_string), 'footer'))

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
        if query:
            UI(self.xdir, ['search', query])
        self.set_status()

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
