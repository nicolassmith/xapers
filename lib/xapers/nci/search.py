import os
import sys
import subprocess
import urwid

from xapers.database import Database, DatabaseError
from xapers.documents import Document

############################################################

def xclip(text, isfile=False):
    """Copy text or file contents into X clipboard."""
    f = None
    if isfile:
        f = open(text, 'r')
        sin = f
    else:
        sin = subprocess.PIPE
    p = subprocess.Popen(' '.join(["xclip", "-i"]),
                         shell=True,
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

        self.sources = urwid.Text(' '.join(self.doc.get_sources_list()))
        self.tags = urwid.Text(' '.join(self.doc.get_tags()))
        self.title = urwid.Text('')
        self.authors = urwid.Text('')
        self.year = urwid.Text('')
        self.summary = urwid.Text('')

        data = self.doc.get_bibdata()
        if data:
            if 'title' in data:
                self.title = urwid.Text(data['title'])
            if 'authors' in data:
                # astring = ' and '.join(data['authors'])
                astring = ' and '.join(data['authors'][:10])
                if len(data['authors']) > 10:
                    astring = astring + ' et al.'
                self.authors = urwid.Text(astring)
            if 'year' in data:
                self.year = urwid.Text(data['year'])

        self.summary = urwid.Text(self.doc.get_data())

        self.c1width = 10

        self.rowHeader = urwid.AttrWrap(
            urwid.Text('id:%s (%s)' % (self.docid, self.matchp)),
            'head_id',
            'focus_id')

        # self.rowHeader = urwid.Columns(
        #     [('fixed', self.c1width,
        #       urwid.AttrWrap(
        #                 urwid.Text('id:%s (%s)' % (self.docid, self.matchp)),
        #                 'head_id',
        #                 'focus_id')),
        #      # ('fixed', 5,
        #      #  urwid.AttrWrap(
        #      #            urwid.Text('%i%%' % (self.percent)),
        #      #            'search_value_default',
        #      #            'focus')),
        #      # ('fixed', len(self.source_string),
        #      #  urwid.AttrWrap(
        #      #            urwid.Text('%s' % (self.source_string)),
        #      #            'search_value_default',
        #      #            'focus')),
        #      ],
        #     )

        w = urwid.Pile(
            [
                urwid.Divider('-'),
                self.rowHeader,
                self.docfield('sources', value_palette='search_sources'),
                self.docfield('tags', value_palette='search_tags'),
                self.docfield('title', value_palette='search_title'),
                self.docfield('authors'),
                self.docfield('year'),
                self.docfield('summary'),
                ]
            ,
            focus_item=1)
        self.__super.__init__(w)

    def docfield(self, field, field_palette=None, value_palette='search_value_default'):
        return urwid.Columns(
            [
                ('fixed', self.c1width,
                 urwid.AttrWrap(
                        urwid.Text(field + ':'),
                        field_palette, 'focus')),
                urwid.AttrWrap(
                    eval('self.' + field),
                    value_palette, 'focus')
                ]
            )

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

############################################################

class Search(urwid.WidgetWrap):
    def __init__(self, ui, query):
        self.ui = ui

        self.ui.set_header("search: " + query)
        self.ui.set_status("enter to view document ('h' for help).")

        docs = self.ui.db.search(query, limit=20)
        if len(docs) == 0:
            self.ui.set_status('No documents found.')

        items = []
        for doc in docs:
            items.append(DocListItem(doc))

        self.listwalker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(self.listwalker)
        w = self.listbox

        self.__super.__init__(w)

    ##########

    def nextEntry(self):
        entry, pos = self.listbox.get_focus()
        if not entry: return
        self.listbox.set_focus(pos + 1)

    def prevEntry(self):
        entry, pos = self.listbox.get_focus()
        if not entry: return
        if pos == 0: return
        self.listbox.set_focus(pos - 1)

    def viewEntry(self):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        path = entry.doc.get_fullpaths()[0].replace(' ','\ ')
        if not path or not os.path.exists(path):
            self.ui.set_status('ERROR: id:%s: file not found.' % entry.docid)
            return
        self.ui.set_status('opening file: %s...' % path)
        subprocess.call(' '.join(["nohup", "okular", path]) + ' &',
                        shell=True,
                        stdout=open('/dev/null','w'),
                        stderr=open('/dev/null','w'))

    def viewURL(self):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        url = entry.doc.get_url()
        if not url:
            self.ui.set_status('ERROR: id:%s: URL not found.' % entry.docid)
            return
        self.ui.set_status('opening url: %s...' % url)
        subprocess.call(' '.join(["nohup", "jbrowser", url]) + ' &',
                        shell=True,
                        stdout=open('/dev/null','w'),
                        stderr=open('/dev/null','w'))

    def viewBibtex(self):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        bibtex = entry.doc.get_bibpath()
        if not bibtex:
            self.ui.set_status('ERROR: id:%s: bibtex not found.' % entry.docid)
            return
        self.ui.set_status('viewing bibtex: %s...' % bibtex)
        # FIXME: we can do this better
        subprocess.call(' '.join(["nohup", "x-terminal-emulator", "-e", "less", bibtex]) + ' &',
                        shell=True,
                        stdout=open('/dev/null','w'),
                        stderr=open('/dev/null','w'))

    def copyPath(self):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        path = entry.doc.get_fullpaths()[0]
        if not path:
            self.ui.set_status('ERROR: id:%s: file path not found.' % entry.docid)
            return
        xclip(path)
        self.ui.set_status('path yanked: %s' % path)

    def copyURL(self):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        url = entry.doc.get_url()
        if not url:
            self.ui.set_status('ERROR: id:%s: URL not found.' % entry.docid)
            return
        xclip(url)
        self.ui.set_status('url yanked: %s' % url)

    def copyBibtex(self):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        bibtex = entry.doc.get_bibpath()
        if not bibtex:
            self.ui.set_status('ERROR: id:%s: bibtex not found.' % entry.docid)
            return
        xclip(bibtex, isfile=True)
        self.ui.set_status('bibtex yanked: %s' % bibtex)

    def promptTag(self, sign):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        if sign is '+':
            # FIXME: autocomplete to existing tags
            prompt = 'add tags: '
        elif sign is '-':
            # FIXME: autocomplete to doc tags only
            prompt = 'remove tags: '
        urwid.connect_signal(self.ui.prompt(prompt), 'done', self.promptTag_done, sign)

    def promptTag_done(self, tag_string, sign):
        self.ui.view.set_focus('body')
        urwid.disconnect_signal(self, self.ui.prompt, 'done', self.promptTag_done)
        if not tag_string:
            self.ui.set_status('No tags set.')
            return
        entry = self.listbox.get_focus()[0]
        db = Database(self.ui.xdir, writable=True)
        doc = db.doc_for_docid(entry.docid)
        tags = tag_string.split()
        if sign is '+':
            doc.add_tags(tags)
            msg = "Added tags: %s" % (tag_string)
        elif sign is '-':
            doc.remove_tags(tags)
            msg = "Removed tags: %s" % (tag_string)
        doc.sync()
        tags = doc.get_tags()
        entry.tags.set_text(' '.join(tags))
        self.ui.set_status(msg)

    def archive(self):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        db = Database(self.ui.xdir, writable=True)
        doc = db.doc_for_docid(entry.docid)
        tag = 'inbox'
        msg = "Removed tag '%s'." % (tag)
        doc.remove_tags([tag])
        doc.sync()
        tags = doc.get_tags()
        entry.tags.set_text(' '.join(tags))
        self.ui.set_status(msg)

    def setField(self, field):
        self.ui.set_status('Not implemented')
        return
        focus = self.listbox.get_focus()[0]
        element = eval('focus.' + field)
        value = element.get_text()[0]
        self.prompt = Prompt(field + ': ', edit_text=value)
        self.ui.set_prompt(self.prompt)
        urwid.connect_signal(self.prompt, 'done', self.setField_done, field)

    def setField_done(self, new, field):
        self.ui.view.set_focus('body')
        urwid.disconnect_signal(self, self.prompt, 'done', self.setField_done)
        if new is not None:
            focus = self.listbox.get_focus()[0]
            docid = focus.docid
            # open the database writable and set the new field
            db = Database(self.ui.xdir, writable=True)
            doc = db.doc_for_docid(docid)
            eval('doc.set_' + field + '("' + new + '")')
            doc.sync()
            # FIXME: update the in-place doc
            # update the display
            element = eval('focus.' + field)
            element.set_text(new)
            msg = "Document id:%s %s updated." % (focus.docid, field)
        else:
            msg = "Nothing done."
        self.ui.set_status(msg)

    ##########

    def keypress(self, size, key):
        if key is 'n':
            self.nextEntry()
        elif key is 'p':
            self.prevEntry()
        elif key is '+':
            self.promptTag('+')
        elif key is '-':
            self.promptTag('-')
        elif key is 'a':
            self.archive()
        elif key is 'enter':
            self.viewEntry()
        elif key is 'u':
            self.viewURL()
        elif key is 'b':
            self.viewBibtex()
        elif key is 'F':
            self.copyPath()
        elif key is 'U':
            self.copyURL()
        elif key is 'B':
            self.copyBibtex()
        else:
            self.ui.keypress(key)
