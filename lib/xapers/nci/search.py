import os
import subprocess
import urwid

from ..cli import initdb
from ..database import DatabaseLockError

############################################################

def xclip(text, isfile=False):
    """Copy text or file contents into X clipboard."""
    f = None
    if isfile:
        f = open(text, 'r')
        sin = f
    else:
        sin = subprocess.PIPE
    p = subprocess.Popen(["xclip", "-i"],
                         stdin=sin)
    p.communicate(text)
    if f:
        f.close()

############################################################

class DocListItem(urwid.WidgetWrap):

    FIELDS = ['title',
              'authors',
              'journal',
              'year',
              'source',
              #'tags',
              'file',
              #'summary',
              ]

    def __init__(self, doc):
        self.doc = doc
        self.docid = self.doc.docid

        self.fields = dict.fromkeys(self.FIELDS, '')

        self.fields['tags'] = ' '.join(self.doc.get_tags())

        bibdata = self.doc.get_bibdata()
        if bibdata:
            for field, value in bibdata.iteritems():
                if 'title' == field:
                    self.fields[field] = value
                elif 'authors' == field:
                    astring = ' and '.join(value[:4])
                    if len(value) > 4:
                        astring = astring + ' et al.'
                    self.fields[field] = astring
                elif 'year' == field:
                    self.fields[field] = value

                if self.fields['journal'] == '':
                    if 'journal' == field:
                        self.fields['journal'] = value
                    elif 'container-title' == field:
                        self.fields['journal'] = value
                    elif 'arxiv' == field:
                        self.fields['journal'] = 'arXiv.org'
                    elif 'dcc' == field:
                        self.fields['journal'] = 'LIGO DCC'

        urls = self.doc.get_urls()
        if urls:
            self.fields['source'] = urls[0]

        summary = self.doc.get_data()
        if not summary:
            summary = 'NO FILE'
        self.fields['summary'] = summary

        files = self.doc.get_files()
        if files:
            self.fields['file'] = os.path.basename(files[0])

        self.c1width = 10

        self.tag_field = urwid.Text(self.fields['tags'])
        header = urwid.AttrMap(urwid.Columns([
            ('fixed', self.c1width, urwid.Text('id:%d' % (self.docid))),
            urwid.AttrMap(self.tag_field, 'tags'),
            urwid.Text('%s%% match' % (doc.matchp), align='right'),
            ]),
            'head')
        pile = [urwid.AttrMap(urwid.Divider(' '), '', ''),
                header
                ] + [self.docfield(field) for field in self.FIELDS]
        w = urwid.AttrMap(urwid.AttrMap(urwid.Pile(pile), 'field'),
                          '',
                          {'head': 'head focus',
                           'field': 'field focus',
                           'tags': 'tags focus',
                           'title': 'title focus',
                           'authors': 'authors focus',
                           'journal': 'journal focus',
                           },
                          )

        self.__super.__init__(w)

    def docfield(self, field):
        if field in ['journal', 'year', 'source']:
            color = 'journal'
        elif field in ['file']:
            color = 'field'
        else:
            color = field
        return urwid.Columns([
            ('fixed', self.c1width, urwid.Text(('field', field + ':'))),
            urwid.Text((color, self.fields[field])),
            ])

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

############################################################

class DocListWalker(urwid.ListWalker):
    def __init__(self, db, query):
        self.db = db
        self.query = query
        
############################################################

class Search(urwid.WidgetWrap):

    palette = [
        ('head', 'dark blue, bold', ''),
        ('head focus', 'white, bold', 'dark blue'),
        ('field', 'light gray', ''),
        ('field focus', '', 'dark gray', '', '', 'g19'),
        ('tags', 'dark green', ''),
        #('tags focus', 'dark green', 'dark gray', '', 'dark green', 'g19'),
        ('tags focus', 'light green', 'dark blue'),
        ('title', 'yellow', ''),
        ('title focus', 'yellow', 'dark gray', '', 'yellow', 'g19'),
        ('authors', 'light cyan', ''),
        ('authors focus', 'light cyan', 'dark gray', '', 'light cyan', 'g19'),
        ('journal', 'dark magenta', '',),
        ('journal focus', 'dark magenta', 'dark gray', '', 'dark magenta', 'g19'),
        ]

    keys = {
        '=': "refresh",
        'l': "filterSearch",
        'n': "nextEntry",
        'p': "prevEntry",
        'down': "nextEntry",
        'up': "prevEntry",
        'enter': "viewFile",
        'u': "viewURL",
        'b': "viewBibtex",
        '+': "addTags",
        '-': "removeTags",
        'a': "archive",
        'meta i': "copyID",
        'meta f': "copyPath",
        'meta u': "copyURL",
        'meta b': "copyBibtex",
        }

    def __init__(self, ui, query=None):
        self.ui = ui
        self.query = query

        limit = 20
        items = []

        count = self.ui.db.count(query)
        for doc in self.ui.db.search(query, limit=limit):
            items.append(DocListItem(doc))

        if count == 0:
            self.ui.set_status('No documents found.')
        if count > limit:
            shown = limit
        else:
            shown = count
        self.ui.set_header([urwid.Columns([
            urwid.Text("search: \"%s\"" % (query)),
            urwid.Text("(%d/%d shown)" % (shown, count), align='right'),
            ])])

        self.lenitems = limit
        self.docwalker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(self.docwalker)
        w = self.listbox

        self.__super.__init__(w)

    ##########

    def refresh(self):
        """refresh search results"""
        self.ui.newbuffer(['search', self.query])
        self.ui.killBuffer()

    def filterSearch(self):
        """filter current search with additional terms"""
        prompt = 'filter search: '
        urwid.connect_signal(self.ui.prompt(prompt), 'done', self._filterSearch_done)

    def _filterSearch_done(self, newquery):
        self.ui.view.set_focus('body')
        urwid.disconnect_signal(self.ui, self.ui.prompt, 'done', self._filterSearch_done)
        if not newquery:
            self.ui.set_status()
            return
        self.ui.newbuffer(['search', self.query, newquery])

    def nextEntry(self):
        """next entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        if pos + 1 >= self.lenitems: return
        self.listbox.set_focus(pos + 1)

    def prevEntry(self):
        """previous entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        if pos == 0: return
        self.listbox.set_focus(pos - 1)

    def viewFile(self):
        """open document file"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        path = entry.doc.get_fullpaths()
        if not path:
            self.ui.set_status('No file for document id:%d.' % entry.docid)
            return
        path = path[0]
        if not os.path.exists(path):
            self.ui.set_status('ERROR: id:%d: file not found.' % entry.docid)
            return
        self.ui.set_status('opening file: %s...' % path)
        subprocess.Popen(['xdg-open', path],
                         stdin=self.ui.devnull,
                         stdout=self.ui.devnull,
                         stderr=self.ui.devnull)

    def viewURL(self):
        """open document URL in browser"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        urls = entry.doc.get_urls()
        if not urls:
            self.ui.set_status('ERROR: id:%d: no URLs found.' % entry.docid)
            return
        # FIXME: open all instead of just first?
        url = urls[0]
        self.ui.set_status('opening url: %s...' % url)
        subprocess.call(['xdg-open', url],
                         stdin=self.ui.devnull,
                         stdout=self.ui.devnull,
                         stderr=self.ui.devnull)

    def viewBibtex(self):
        """view document bibtex"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        self.ui.newbuffer(['bibview', 'id:' + str(entry.docid)])

    def copyID(self):
        """copy document ID to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        docid = "id:%d" % entry.docid
        xclip(docid)
        self.ui.set_status('docid yanked: %s' % docid)

    def copyPath(self):
        """copy document file path to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        path = entry.doc.get_fullpaths()[0]
        if not path:
            self.ui.set_status('ERROR: id:%d: file path not found.' % entry.docid)
            return
        xclip(path)
        self.ui.set_status('path yanked: %s' % path)

    def copyURL(self):
        """copy document URL to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        urls = entry.doc.get_urls()
        if not urls:
            self.ui.set_status('ERROR: id:%d: URL not found.' % entry.docid)
            return
        # FIXME: copy all instead of just first?
        url = urls[0]
        xclip(url)
        self.ui.set_status('url yanked: %s' % url)

    def copyBibtex(self):
        """copy document bibtex to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        bibtex = entry.doc.get_bibpath()
        if not bibtex:
            self.ui.set_status('ERROR: id:%d: bibtex not found.' % entry.docid)
            return
        xclip(bibtex, isfile=True)
        self.ui.set_status('bibtex yanked: %s' % bibtex)

    def addTags(self):
        """add tags to document (space separated)"""
        self.promptTag('+')

    def removeTags(self):
        """remove tags from document (space separated)"""
        self.promptTag('-')

    def promptTag(self, sign):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        if sign is '+':
            # FIXME: autocomplete to existing tags
            prompt = 'add tags: '
        elif sign is '-':
            # FIXME: autocomplete to doc tags only
            prompt = 'remove tags: '
        urwid.connect_signal(self.ui.prompt(prompt), 'done', self._promptTag_done, sign)

    def _promptTag_done(self, tag_string, sign):
        self.ui.view.set_focus('body')
        urwid.disconnect_signal(self, self.ui.prompt, 'done', self._promptTag_done)
        if not tag_string:
            self.ui.set_status('No tags set.')
            return
        entry = self.listbox.get_focus()[0]
        try:
            with initdb(writable=True) as db:
                doc = db[entry.docid]
                tags = tag_string.split()
                if sign is '+':
                    doc.add_tags(tags)
                    msg = "Added tags: %s" % (tag_string)
                elif sign is '-':
                    doc.remove_tags(tags)
                    msg = "Removed tags: %s" % (tag_string)
                doc.sync()
            tags = doc.get_tags()
            entry.tag_field.set_text(' '.join(tags))
        except DatabaseLockError as e:
            msg = e.msg
        self.ui.set_status(msg)

    def archive(self):
        """archive document (remove 'new' tag) and advance"""
        self._promptTag_done('new', '-')
        self.nextEntry()

    def keypress(self, size, key):
        if key in self.keys:
            cmd = "self.%s()" % (self.keys[key])
            eval(cmd)
        else:
            self.ui.keypress(key)
