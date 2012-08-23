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

Copyright 2012
Jameson Rollins <jrollins@finestructure.net>
"""

import os
import sys
import xapian

class Documents():
    """Represents a set of Xapers documents."""

    def __init__(self, xapers, mset):
        # Xapers db
        self.xapers = xapers
        self.mset = mset
        self.index = len(mset)

    def __iter__(self):
        return self

    def next(self):
        if self.index == 0:
            raise StopIteration
        self.index = self.index - 1
        item = self.mset[self.index]
        doc = Document(self.xapers, item.document)
        return doc


class Document():
    """Represents a Xapers document."""

    def __init__(self, xapers, doc=None):
        # Xapers db
        self.xapers = xapers
        if doc:
            # Create document from Xapian document
            # FIXME: check that what we're recieving here is legit
            self.doc = doc
            self.doc_id = doc.get_docid()
        else:
            # Create a new document
            self.doc = xapian.Document()
            self.doc_id = self.xapers._generate_doc_id()
            self._add_term(self.xapers._find_prefix('id'), self.doc_id)

        # FIXME: what other metadata should the document have?

    # FIXME: should we add equivalent of
    # _notmuch_message_ensure_metadata, that would extract fields from
    # the xapian document?

    # add an individual prefix'd term for the document
    def _add_term(self, prefix, value):
        term = '%s%s' % (prefix, value)
        self.doc.add_term(term)

    # remove an individual prefix'd term for the document
    def _remove_term(self, prefix, value):
        term = '%s%s' % (prefix, value)
        self.doc.remove_term(term)

    # Parse 'text' and add a term to 'message' for each parsed
    # word. Each term will be added both prefixed (if prefix_name is
    # not NULL) and also non-prefixed).
    # http://xapian.org/docs/bindings/python/
    # http://xapian.org/docs/quickstart.html
    # http://www.flax.co.uk/blog/2009/04/02/xapian-search-architecture/
    def _gen_terms(self, prefix, text):
        term_gen = self.xapers.term_gen
        term_gen.set_document(self.doc)
        # FIXME: this should be for adding 
        # if prefix:
        #     do something
        term_gen.index_text(text)
            
    # return a list of terms for prefix
    # FIXME: is this the fastest way to do this?
    def _get_terms(self, prefix):
        list = []
        for term in self.doc:
            if term.term.startswith(prefix):
                list.append(term.term.lstrip(prefix))
        return list

    # set the data object for the document
    def _set_data(self, text):
        self.doc.set_data(text)

    # FIXME: this definitely needs to move to a different parsing
    # module
    # oh and it sucks.
    def _pdf2text(self, pdf):
        from subprocess import Popen, PIPE
        cmd = ['pdftotext', '-', '-']
        p = Popen(' '.join(cmd), stdin=PIPE, stdout=PIPE, shell=True)
        text = p.communicate(pdf.getvalue())[0]
        if p.wait() != 0:
            raise IOerror
        return text

    def _sync(self):
        self.xapers.xapian_db.replace_document(self.doc_id, self.doc)

    # this should only we set when we index a new file
    def _set_path(self, filename):
        prefix = self.xapers._find_prefix('file')
        self._add_term(prefix, '/' + filename)

    # index/add a new file for the document
    def _index_file(self, filename):
        print >>sys.stderr, "  indexing:", filename

        # extract text from pdf
        import cStringIO
        pdf = cStringIO.StringIO()
        fi = open(os.path.join(self.xapers.root,filename), 'rb')
        #fi = open(filename, 'rb')
        pdf.write(fi.read())
        fi.close()
        text = self._pdf2text(pdf)

        # index document text
        self._gen_terms(None, text)

        # set data to be text sample
        # FIXME: what should really be in here?  what if we have
        # multiple files for the document?  what about bibtex?  what
        # if there is multiple bibtex entries?
        self._set_data(text[0:997].translate(None,'\n') + '...')

        self._set_path(filename)

        # FIXME: would it be better for this function to _sync at the
        # end?

    def _parse_bibtex(self, bibtex):
        # FIXME: extract title/author/? from bibtex
        # BOOL INT
        # doc.add_term('A', author) # author
        # doc.add_term('S', title) # title
        # doc.add_term('D', date) # modification/creation? date
        # doc.add_term('T', type) # mimetype
        # BOOL EXT
        # PROB
        # doc.add_term('XAUTHOR', author) # author
        # doc.add_term('XTITLE', title) # title
        pass

    ##########

    # FIXME: we output the relative path as an ad-hoc doc id.
    # this should really just be the actual docid, and we need
    # a way to access docs by docid directly (via "id:")
    def get_id(self):
        """Return document id of document."""
        #return self._get_terms(self.xapers._find_prefix('file'))[0]
        return self.doc_id

    def get_paths(self):
        """Return all paths associated with document."""
        prefix = self.xapers._find_prefix('file')
        return self._get_terms(prefix)

    def get_full_path(self):
        """Return fullpaths associated with document."""
        root = self.xapers.root
        paths = self.get_paths()
        list = []
        for path in paths:
            list.append(os.path.join(root,path.lstrip('/')))
        return list

    def get_data(self):
        """Return data associated with document."""
        return self.doc.get_data()

    def _add_url(self, url):
        prefix = self.xapers._find_prefix('url')
        self._add_term(prefix, url)

    def add_url(self, url):
        """Add a url to document"""
        # FIXME: accept multiple urls
        self._add_url(source)
        self._sync()

    def get_urls(self):
        """Return url associated with document."""
        prefix = self.xapers._find_prefix('url')
        return self._get_terms(prefix)

    def _add_source(self, source):
        print >>sys.stderr, "  adding source:", source
        prefix = self.xapers._find_prefix('source')
        self._add_term(prefix, source)

    def add_source(self, source):
        """Add a source to document."""
        self._add_source(source)
        self._sync()

    def get_sources(self):
        """Return sources associated with document."""
        prefix = self.xapers._find_prefix('source')
        return self._get_terms(prefix)

    def _add_source_id(self, source, sid):
        print >>sys.stderr, "  adding source id:", source, sid
        prefix = self.xapers._make_source_prefix(source)
        self._add_term(prefix, sid)

    def add_source_id(self, source, sid):
        """Add a source id for a document source."""
        self._add_source_id(source, sid)
        self._sync()

    def remove_source(self, source):
        pass

    def get_source_id(self, source):
        """Return source id for specified document source."""
        # FIXME: this should produce a single term
        prefix = self.xapers._make_source_prefix(source)
        return self._get_terms(prefix)[0]

    def _add_tag(self, tag):
        prefix = self.xapers._find_prefix('tag')
        self._add_term(prefix, tag)

    def _remove_tag(self, tag):
        prefix = self.xapers._find_prefix('tag')
        self._remove_term(prefix, tag)

    def add_tags(self, tags):
        """Add tags to a document."""
        # FIXME: this should take a list of tags
        print tags
        for tag in tags:
            self._add_tag(tag)
        self._sync()

    def add_tags(self, tags):
        """Add tags to a document."""
        for tag in tags:
            self._add_tag(tag)
        self._sync()

    def remove_tags(self, tags):
        """Remove tags from a document."""
        for tag in tags:
            self._remove_tag(tag)
        self._sync()

    def get_tags(self):
        """Return document tags."""
        prefix = self.xapers._find_prefix('tag')
        return self._get_terms(prefix)
