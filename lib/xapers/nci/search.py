import os
import subprocess
import urwid

from ..database import Database, DatabaseLockError

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

    def __init__(self, doc):
        self.doc = doc
        self.matchp = doc.matchp
        self.docid = self.doc.docid

        # fill the default attributes for the fields
        self.fields = {}
        for field in ['sources', 'tags', 'title', 'authors', 'year', 'summary']:
            self.fields[field] = urwid.Text('')

        self.fields['sources'].set_text(' '.join(self.doc.get_sids()))
        self.fields['tags'].set_text(' '.join(self.doc.get_tags()))

        data = self.doc.get_bibdata()
        if data:
            if 'title' in data:
                self.fields['title'].set_text(data['title'])
            if 'authors' in data:
                astring = ' and '.join(data['authors'][:10])
                if len(data['authors']) > 10:
                    astring = astring + ' et al.'
                self.fields['authors'].set_text(astring)
            if 'year' in data:
                self.fields['year'].set_text(data['year'])

        self.fields['summary'].set_text(self.doc.get_data())

        self.c1width = 10

        self.rowHeader = urwid.AttrMap(
            urwid.Text('id:%s (%s)' % (self.docid, self.matchp)),
            'head', 'head_focus')

        # FIXME: how do we hightlight everything in pile during focus?
        w = urwid.Pile(
            [
                urwid.Divider('-'),
                self.rowHeader,
                self.docfield('sources'),
                self.docfield('tags'),
                self.docfield('title'),
                self.docfield('authors'),
                self.docfield('year'),
                self.docfield('summary'),
                ]
            ,
            focus_item=1)
        self.__super.__init__(w)

    def docfield(self, field):
        attr_map = field
        return urwid.Columns(
            [
                ('fixed', self.c1width,
                 urwid.AttrMap(
                     urwid.Text(field + ':'),
                     'field', 'field_focus')),
                urwid.AttrMap(
                    self.fields[field],
                    attr_map)
                ]
            )

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

############################################################

class Search(urwid.WidgetWrap):

    palette = [
        ('head', 'dark blue, bold', ''),
        ('head_focus', 'white, bold', 'dark blue'),
        ('field', 'light gray', ''),
        ('field_focus', '', 'light gray'),
        ('sources', 'light magenta, bold', ''),
        ('tags', 'dark green, bold', ''),
        ('title', 'yellow', ''),
        ('authors', 'dark cyan, bold', ''),
        ('year', 'dark red', '',),
        ]

    keys = {
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

        self.ui.set_header("Search: " + query)

        docs = self.ui.db.search(query, limit=20)
        if len(docs) == 0:
            self.ui.set_status('No documents found.')

        items = []
        for doc in docs:
            items.append(DocListItem(doc))

        self.lenitems = len(items)
        self.listwalker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(self.listwalker)
        w = self.listbox

        self.__super.__init__(w)

    ##########

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
            self.ui.set_status('No file for document id:%s.' % entry.docid)
            return
        path = path[0]
        if not os.path.exists(path):
            self.ui.set_status('ERROR: id:%s: file not found.' % entry.docid)
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
            self.ui.set_status('ERROR: id:%s: no URLs found.' % entry.docid)
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
        self.ui.newbuffer(['bibview', 'id:' + entry.docid])

    def copyID(self):
        """copy document ID to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        docid = "id:%s" % entry.docid
        xclip(docid)
        self.ui.set_status('docid yanked: %s' % docid)

    def copyPath(self):
        """copy document file path to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        path = entry.doc.get_fullpaths()[0]
        if not path:
            self.ui.set_status('ERROR: id:%s: file path not found.' % entry.docid)
            return
        xclip(path)
        self.ui.set_status('path yanked: %s' % path)

    def copyURL(self):
        """copy document URL to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        urls = entry.doc.get_urls()
        if not urls:
            self.ui.set_status('ERROR: id:%s: URL not found.' % entry.docid)
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
            self.ui.set_status('ERROR: id:%s: bibtex not found.' % entry.docid)
            return
        xclip(bibtex, isfile=True)
        self.ui.set_status('bibtex yanked: %s' % bibtex)

    def addTags(self):
        """add tags from document (space separated)"""
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
            with Database(self.ui.xroot, writable=True) as db:
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
            entry.fields['tags'].set_text(' '.join(tags))
        except DatabaseLockError as e:
            msg = e.msg
        self.ui.set_status(msg)

    def archive(self):
        """archive document (remove 'new' tag)"""
        self._promptTag_done('new', '-')

    def keypress(self, size, key):
        if key in self.keys:
            cmd = "self.%s()" % (self.keys[key])
            eval(cmd)
        else:
            self.ui.keypress(key)
