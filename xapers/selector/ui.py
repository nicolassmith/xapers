import subprocess
import urwid

from xapers.database import Database
from xapers.documents import Document
import xapers.nci as nci

class Search(urwid.WidgetWrap):
    def __init__(self, ui, args):
        self.ui = ui
        self.db = Database(self.ui.xdir, writable=False)

        matches = self.db.search(args, limit=20)

        items = []
        for m in matches:
            doc = Document(self.db, doc=m.document)
            items.append(DocListItem(doc, m.percent))

        self.listwalker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(self.listwalker)
        #w = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'))
        w = urwid.AttrWrap(self.listbox, 'body')
        self.__super.__init__(w)

    def nextEntry(self):
        # listbox.set_focus(listbox.get_next())
        pos = self.listbox.get_focus()[1]
        self.listbox.set_focus(pos + 1)
        # self.listbox.keypress(1, 'down')

    def prevEntry(self):
        pos = self.listbox.get_focus()[1]
        if pos == 0: return
        self.listbox.set_focus(pos - 1)

    def viewEntry(self):
        docid = self.listbox.get_focus()[0].docid
        path = self.listbox.get_focus()[0].path
        path = path.replace(' ','\ ')
        message = 'opening doc id:%s...' % docid
        self.ui.set_status(message)
        subprocess.call(' '.join(["nohup", "okular", path]) + ' &',
                        shell=True,
                        stdout=open('/dev/null','w'),
                        stderr=open('/dev/null','w'))

    def editEntry(self):
        return
        doc = self.listbox.get_focus()[0].doc

        self.prompt(prefix='add tag: ')

        wdb = Database(self.xdir, writable=True)
        wdoc = Document(wdb, doc=doc.doc)
        wdoc.add_tags(['QUX'])

    def keypress(self, size, key):
        if key is 'n':
            self.nextEntry()
        elif key is 'p':
            self.prevEntry()
        elif key is 'e':
            self.editEntry()
        elif key is 'enter':
            self.viewEntry()
        else:
            self.ui.keypress(key)


class DocListItem(urwid.WidgetWrap):
    def __init__(self, doc, percent):
        self.doc = doc
        self.percent = percent
        self.docid = self.doc.get_docid()
        self.path = self.doc.get_fullpaths()[0]
        self.tags = self.doc.get_tags()
        self.sources = self.doc.get_sources()
        self.url = self.doc.get_url()
        self.title = self.doc.get_title()
        self.authors = self.doc.get_authors()
        if not self.authors: self.authors = ''
        self.year = self.doc.get_year()
        self.data = self.doc.get_data()

        self.tag_string = '(%s)' % (' '.join(self.tags))
        self.source_string = '['
        for source,sid in self.sources.items():
            self.source_string += '%s:%s' % (source, sid)
        self.source_string += ']'

        self.c1width = 10

        self.rowHeader = urwid.Columns(
            [('fixed', self.c1width,
              urwid.AttrWrap(
                  urwid.Text('id:%s' % (self.docid)),
                  'head_id',
                  'focus_id')),
             ('fixed', 4,
              urwid.AttrWrap(
                  urwid.Text('%i%%' % (self.percent)),
                  'head_percent',
                  'focus')),
             ('fixed', len(self.path),
              urwid.AttrWrap(
                  urwid.Text('%s' % (self.path)),
                  'head_path',
                  'focus')),
             ('fixed', len(self.tag_string),
              urwid.AttrWrap(
                  urwid.Text('%s' % (self.tag_string)),
                  'head_tags',
                  'focus')),
             ('fixed', len(self.source_string),
              urwid.AttrWrap(
                  urwid.Text('%s' % (self.source_string)),
                  'head_sources',
                  'focus')),
             ],
            dividechars=1,
            )

        w = urwid.Pile(
            [
                urwid.Divider('-'),
                self.rowHeader,
                self.docfield('url', self.url),
                self.docfield('title', self.title),
                self.docfield('author', self.authors),
                self.docfield('year', self.year),
                self.docfield('data', self.data),
                ]
            ,
            focus_item=1)
        self.__super.__init__(w)

    def docfield(self, field, value):
        return urwid.Columns(
            [('fixed', self.c1width,
              urwid.AttrWrap(
                        urwid.Text(field + ':'),
                        'data_bold',
                        'focus')),
             urwid.AttrWrap(
                    urwid.Text('%s' % (value)),
                    'body',
                    'focus')
             ]
            )

    def selectable (self):
        return True

    def keypress(self, size, key):
        return key


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
        ('footer', 'white', 'dark blue'),
        ]

    def __init__(self, xdir, cmd, args):
        self.xdir = xdir

        if cmd is 'search':
            self.cmd = Search(self, args)
        else:
            print >>sys.stderr, "Unknown command:", cmd
            sys.exit()

        self.view = urwid.Frame(self.cmd)
        self.set_status()
        self.mainloop = urwid.MainLoop(
            self.view,
            self.palette,
            unhandled_input=self.keypress,
            handle_mouse=False,
            )
        self.mainloop.run()

    def set_status(self, text=None):
        if not text:
            message = 'Xapers'
        else:
            message = 'Xapers: %s' % (text)
        self.view.set_footer(urwid.AttrWrap(urwid.Text(message), 'footer'))

    def keypress(self, key):
        if key is 's':
            return
        if key is 'q':
            raise urwid.ExitMainLoop()
