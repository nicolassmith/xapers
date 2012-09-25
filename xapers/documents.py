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
    """Represents a set of Xapers documents given a Xapian mset."""

    def __init__(self, xapers, mset):
        # Xapers db
        self.xapers = xapers
        self.mset = mset
        self.index = -1
        self.max = len(mset)

    def __iter__(self):
        return self

    def next(self):
        self.index = self.index + 1
        if self.index == self.max:
            raise StopIteration
        m = self.mset[self.index]
        doc = Document(self.xapers, m.document)
        doc.matchp = m.percent
        return doc


class Document():
    """Represents a single Xapers document."""

    def __init__(self, xapers, doc=None):
        # Xapers db
        self.xapers = xapers
        self.root = self.xapers.root

        # if Xapian doc provided, initiate for that document
        if doc:
            self.doc = doc
            self.docid = doc.get_docid()
            self.path = self._get_terms(self.xapers._find_prefix('file'))

        # else, create a new empty document
        # document won't be added to database until _sync is called
        else:
            self.doc = xapian.Document()
            self.docid = self.xapers._generate_docid()
            self._add_term(self.xapers._find_prefix('id'), self.docid)

    def _sync(self):
        self.xapers.xapian_db.replace_document(self.docid, self.doc)

    ########################################
    # internal stuff

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
        if prefix:
            term_gen.index_text(text, 1, prefix)
        term_gen.index_text(text)
            
    # return a list of terms for prefix
    # FIXME: is this the fastest way to do this?
    def _get_terms(self, prefix):
        list = []
        for term in self.doc:
            if term.term.find(prefix) == 0:
                index = len(prefix)
                list.append(term.term[index:])
        return list

    # set the data object for the document
    def _set_data(self, text):
        self.doc.set_data(text)

    def _set_path(self, path):
        prefix = self.xapers._find_prefix('file')
        self._add_term(prefix, path)

    # this is really only needed to fix bad entries
    def set_path(self, path):
        self._set_path(path)
        self._sync()

    # index/add a new file for the document
    # file should be relative to xapian.root
    # FIXME: codify this more
    def _index_file(self, path):
        from .parsers import pdf as parser
        text = parser.parse_file(os.path.join(self.root, path))

        self._gen_terms(None, text)

        self._set_path(path)

        # set data to be text sample
        # FIXME: what should really be in here?  what if we have
        # multiple files for the document?  what about bibtex?  what
        # if there is multiple bibtex entries?
        self._set_data(text[0:997].translate(None,'\n') + '...')

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

    ########################################
    # external stuff

    # FIXME: we output the relative path as an ad-hoc doc id.
    # this should really just be the actual docid, and we need
    # a way to access docs by docid directly (via "id:")
    def get_docid(self):
        """Return document id of document."""
        #return self._get_terms(self.xapers._find_prefix('file'))[0]
        return self.docid

    def get_paths(self):
        """Return all paths associated with document."""
        return self._get_terms(self.xapers._find_prefix('file'))

    def get_fullpaths(self):
        """Return fullpaths associated with document."""
        # FIXME: PATHS!!! full or partial!
        # FIXME: this is a hack!
        root = self.root.lstrip('/')
        paths = self.get_paths()
        list = []
        for path in paths:
            path = path.lstrip('/')
            if path.find(root) == 0:
                index = len(root)
                path = path[index:]
            list.append(os.path.join('/', root, path))
        return list

    def get_data(self):
        """Return data associated with document."""
        return self.doc.get_data()

    # multi value fields

    # SOURCES
    def _add_source(self, source, sid):
        prefix = self.xapers._find_prefix('source')
        self._add_term(prefix, source)
        prefix = self.xapers._make_source_prefix(source)
        self._add_term(prefix, sid)

    def add_sources(self, sources):
        """Add sources, in form of a source:sid dictionary, to document."""
        for source,sid in sources.items():
            self._add_source(source,sid)
        self._sync()

    def get_source_id(self, source):
        """Return source id for specified document source."""
        # FIXME: this should produce a single term
        prefix = self.xapers._make_source_prefix(source)
        sid = self._get_terms(prefix)
        if sid:
            return sid[0]
        else:
            return None

    def get_sources(self):
        """Return a source:sid dictionary associated with document."""
        prefix = self.xapers._find_prefix('source')
        sources = {}
        for source in self._get_terms(prefix):
            if not source:
                break
            sources[source] = self.get_source_id(source)
        return sources

    def remove_source(self, source):
        """Remove source from document."""
        prefix = self.xapers._make_source_prefix(source)
        for sid in self._get_terms(prefix):
            self._remove_term(prefix, sid)
        self._remove_term(self.xapers._find_prefix('source'), source)

    # TAGS
    def _add_tag(self, tag):
        prefix = self.xapers._find_prefix('tag')
        self._add_term(prefix, tag)

    def add_tags(self, tags):
        """Add tags to a document."""
        for tag in tags:
            self._add_tag(tag)
            # FIXME: index tags so they're searchable
        self._sync()

    def get_tags(self):
        """Return document tags."""
        prefix = self.xapers._find_prefix('tag')
        return self._get_terms(prefix)

    def _remove_tag(self, tag):
        prefix = self.xapers._find_prefix('tag')
        self._remove_term(prefix, tag)

    def remove_tags(self, tags):
        """Remove tags from a document."""
        for tag in tags:
            self._remove_tag(tag)
        self._sync()


    # single value fields

    # URL
    def _set_url(self, url):
        prefix = self.xapers._find_prefix('url')
        for term in self._get_terms(prefix):
            self._remove_term(prefix, term)
        self._add_term(prefix, url)

    def set_url(self, url):
        """Add a url to document"""
        self._set_url(url)
        self._sync()

    def get_url(self):
        """Return url associated with document."""
        prefix = self.xapers._find_prefix('url')
        url = self._get_terms(prefix)
        if url:
            return url[0]
        else:
            return ''

    # TITLE
    def _set_title(self, title):
        """Set title of document."""
        pt = self.xapers._find_prefix('title')
        pf = self.xapers._find_prefix('fulltitle')
        for term in self._get_terms(pt):
            self._remove_term(pt, term)
        # FIXME: what the clean way all these prefixed terms?
        for term in self._get_terms('ZS'):
            self._remove_term('ZS', term)
        for term in self._get_terms(pf):
            self._remove_term(pf, term)
        self._gen_terms(pt, title)
        self._add_term(pf, title)

    def set_title(self, title):
        self._set_title(title)
        self._sync()

    def get_title(self):
        """Return title of document."""
        title = self._get_terms(self.xapers._find_prefix('fulltitle'))
        if title:
            return title[0]
        else:
            return ''

    # AUTHOR
    def _set_authors(self, authors):
        pa = self.xapers._find_prefix('author')
        pf = self.xapers._find_prefix('fullauthors')
        for term in self._get_terms(pa):
            self._remove_term(pa, term)
        # FIXME: what the clean way all these prefixed terms?
        for term in self._get_terms('ZA'):
            self._remove_term('ZA', term)
        for term in self._get_terms(pf):
            self._remove_term(pf, term)
        self._gen_terms(pa, authors)
        # FIXME: can't handle long author lists.  character limit.
        # need to check limit and split up, and maybe store each
        # author individually?
        self._add_term(pf, authors)

    def set_authors(self, authors):
        """Set authors of document."""
        self._set_authors(authors)
        self._sync()

    def get_authors(self):
        """Return authors of document."""
        authors = self._get_terms(self.xapers._find_prefix('fullauthors'))
        if authors:
            return authors[0]
        else:
            return ''

    # YEAR
    def _set_year(self, year):
        prefix = self.xapers._find_prefix('year')
        for term in self._get_terms(prefix):
            self._remove_term(prefix, term)
        self._add_term(prefix, year)

    def set_year(self, year):
        """Set publication year of document."""
        self._set_year(year)
        self._sync()

    def get_year(self):
        """Return publication year of document."""
        prefix = self.xapers._find_prefix('year')
        year =  self._get_terms(prefix)
        if year:
            return year[0]
        else:
            return ''
