import subprocess
import urwid

from xapers.database import Database
from xapers.documents import Document
import xapers.nci as nci

class ItemWidget (urwid.WidgetWrap):

    def __init__ (self, doc, percent):
        self.doc = doc
        self.percent = percent
        self.docid = self.doc.get_docid()
        self.path = self.doc.get_fullpaths()[0]
        self.tags = self.doc.get_tags()
        self.sources = self.doc.get_sources()
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

        c1width = 10

        self.rowHeader = urwid.Columns(
            [('fixed', c1width,
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
        self.rowTitle = urwid.Columns(
            [('fixed', c1width,
              urwid.AttrWrap(
                  urwid.Text('title:'),
                  'title_bold',
                  'focus')),
             urwid.AttrWrap(
                 urwid.Text('%s' % (self.title)),
                 'title',
                 'focus')
             ]
            )
        self.rowAuthor = urwid.Columns(
            [('fixed', c1width,
              urwid.AttrWrap(
                  urwid.Text('authors:'),
                  'title_bold',
                  'focus')),
             urwid.AttrWrap(
                 urwid.Text('%s' % (self.authors)),
                 'title',
                 'focus')
             ]
            )
        self.rowYear = urwid.Columns(
            [('fixed', c1width,
              urwid.AttrWrap(
                  urwid.Text('year:'),
                  'title_bold',
                  'focus')),
             urwid.AttrWrap(
                 urwid.Text('%s' % (self.year)),
                 'title',
                 'focus')
             ]
            )
        self.rowBody = urwid.Columns(
            [('fixed', c1width,
              urwid.AttrWrap(
                  urwid.Text('data:'),
                  'data_bold',
                  'focus')),
             urwid.AttrWrap(
                 urwid.Text('%s' % (self.data)),
                 'body',
                 'focus')
             ]
            )

        #w = urwid.Columns(self.frame)
        w = urwid.Pile(
            [
                urwid.Divider('-'),
                self.rowHeader,
                self.rowTitle,
                self.rowAuthor,
                self.rowYear,
                self.rowBody]
            ,
            focus_item=1)
        self.__super.__init__(w)

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

    def __init__(self, xdir, query_string='*'):
        # FIXME: how do we deal with atomic read/write operations?
        self.db = Database(xdir, writable=False)

        matches = self.db.search(query_string, count=20)

        items = []
        for m in matches:
            doc = Document(self.db, doc=m.document)
            items.append(ItemWidget(doc, m.percent))

        self.listwalker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(self.listwalker)
        self.view = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'))
        self.set_status('')
        self.mainloop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.keystroke)
        self.mainloop.run()

    def set_status(self, text):
        message = 'Xapers %s' % (text)
        self.view.set_footer(urwid.AttrWrap(urwid.Text(message), 'footer'))

    def keystroke(self, input):
        if input is 'n':
            #listbox.set_focus(listbox.get_next())
            pos = self.listbox.get_focus()[1]
            self.listbox.set_focus(pos + 1)
            #self.listbox.keypress(1, 'down')

        if input is 'p':
            pos = self.listbox.get_focus()[1]
            if pos == 0: return
            self.listbox.set_focus(pos - 1)

        if input is 's':
            pass

        if input is '+':
            self.set_status('add tag: ')
            doc = self.listbox.get_focus()[0].doc
            doc.add_tags(['QUX'])
            # FIXME: need to sync db?

        if input is '-':
            doc = self.listbox.get_focus()[0].doc
            doc.remove_tags(['QUX'])

        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        if input is 'enter':
            docid = self.listbox.get_focus()[0].docid
            path = self.listbox.get_focus()[0].path
            query = 'id:%s' % docid
            message = 'opening doc id:%s...' % docid
            self.set_status(message)
            subprocess.call(' '.join(["nohup", "okular", path]) + ' &',
                            shell=True,
                            stdout=open('/dev/null','w'),
                            stderr=open('/dev/null','w'))
