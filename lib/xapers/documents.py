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

Copyright 2012, 2013
Jameson Rollins <jrollins@finestructure.net>
"""

import os
import shutil
import xapian

from parser import parse_data
from source import Sources
from bibtex import Bibtex

##################################################

class DocumentError(Exception):
    """Base class for Xapers document exceptions."""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

##################################################

class Documents():
    """Represents a set of Xapers documents given a Xapian mset."""

    def __init__(self, db, mset):
        self.db = db
        self.mset = mset
        self.index = -1
        self.max = len(mset)

    def __getitem__(self, index):
        m = self.mset[index]
        doc = Document(self.db, m.document)
        doc.matchp = m.percent
        return doc

    def __iter__(self):
        return self

    def __len__(self):
        return self.max

    def next(self):
        self.index = self.index + 1
        if self.index == self.max:
            raise StopIteration
        return self[self.index]

##################################################

class Document():
    """Represents a single Xapers document."""

    def __init__(self, db, doc=None, docid=None):
        # Xapers db
        self.db = db
        self.root = self.db.root

        # if Xapian doc provided, initiate for that document
        if doc:
            self.doc = doc
            self.docid = str(doc.get_docid())

        # else, create a new empty document
        # document won't be added to database until sync is called
        else:
            self.doc = xapian.Document()
            # use specified docid if provided
            if docid:
                if self.db[docid]:
                    raise DocumentError('Document already exists for id %s.' % docid)
                self.docid = docid
            else:
                self.docid = str(self.db._generate_docid())
            self._add_term(self.db._find_prefix('id'), self.docid)

        # specify a directory in the Xapers root for document data
        self.docdir = os.path.join(self.root, '%010d' % int(self.docid))

        #
        self.bibentry = None

        self._infiles = {}

    def get_docid(self):
        """Return document id of document."""
        return self.docid

    def _make_docdir(self):
        if os.path.exists(self.docdir):
            if not os.path.isdir(self.docdir):
                raise DocumentError('File exists at intended docdir location: %s' % self.docdir)
        else:
            os.makedirs(self.docdir)

    def _write_files(self):
        for name, data in self._infiles.iteritems():
            path = os.path.join(self.docdir, name)
            with open(path, 'w') as f:
                f.write(data)

    def _write_bibfile(self):
        bibpath = self.get_bibpath()
        # reload bibtex only if we have new files
        paths = self.get_fullpaths()
        if paths:
            self._load_bib()
        if self.bibentry:
            # we put only the first file in the bibtex
            # FIXME: does jabref/mendeley spec allow for multiple files?
            if paths and not self.bibentry.get_file():
                self.bibentry.set_file(paths[0])
            self.bibentry.to_file(bibpath)

    def _write_tagfile(self):
        with open(os.path.join(self.docdir, 'tags'), 'w') as f:
            for tag in self.get_tags():
                f.write(tag)
                f.write('\n')

    def _rm_docdir(self):
        if os.path.exists(self.docdir) and os.path.isdir(self.docdir):
            shutil.rmtree(self.docdir)

    def sync(self):
        """Sync document to database."""
        # FIXME: add value for modification time
        # FIXME: catch db not writable errors
        try:
            self._make_docdir()
            self._write_files()
            self._write_bibfile()
            self._write_tagfile()
            self.db.replace_document(self.docid, self.doc)
        except:
            self._rm_docdir()
            raise

    def purge(self):
        """Purge document from database and root."""
        # FIXME: catch db not writable errors
        try:
            self.db.delete_document(self.docid)
        except xapian.DocNotFoundError:
            pass
        self._rm_docdir()
        self.docid = None

    ########################################
    # internal stuff

    # add an individual prefix'd term for the document
    def _add_term(self, prefix, value):
        term = '%s%s' % (prefix, value)
        self.doc.add_term(term)

    # remove an individual prefix'd term for the document
    def _remove_term(self, prefix, value):
        term = '%s%s' % (prefix, value)
        try:
            self.doc.remove_term(term)
        except xapian.InvalidArgumentError:
            pass

    # Parse 'text' and add a term to 'message' for each parsed
    # word. Each term will be added both prefixed (if prefix_name is
    # not NULL) and also non-prefixed).
    # http://xapian.org/docs/bindings/python/
    # http://xapian.org/docs/quickstart.html
    # http://www.flax.co.uk/blog/2009/04/02/xapian-search-architecture/
    def _gen_terms(self, prefix, text):
        term_gen = self.db.term_gen
        term_gen.set_document(self.doc)
        if prefix:
            term_gen.index_text(text, 1, prefix)
        term_gen.index_text(text)
            
    # return a list of terms for prefix
    # FIXME: is this the fastest way to do this?
    def _get_terms(self, prefix):
        list = []
        for term in self.doc:
            if term.term.find(prefix.encode("utf-8")) == 0:
                index = len(prefix)
                list.append(term.term[index:])
        return list

    # set the data object for the document
    def _set_data(self, text):
        self.doc.set_data(text)

    def get_data(self):
        """Get data object for document."""
        return self.doc.get_data()

    ########################################
    # files

    def add_file_data(self, name, data):
        """Add a file data to document.

        'name' is the name of the file, 'data is the file data.

        File will not copied in to docdir until sync().
        """
        # FIXME: set mime type term

        # parse the file data into text
        text = parse_data(data)

        # generate terms from the text
        self._gen_terms(None, text)

        # set data to be text sample
        # FIXME: is this the right thing to put in the data?
        summary = text[0:997].translate(None, '\n') + '...'
        self._set_data(summary)

        # FIXME: should files be renamed to something generic (0.pdf)?
        prefix = self.db._find_prefix('file')
        self._add_term(prefix, name)

        # add it to the cache to be written at sync()
        self._infiles[name] = data

    def add_file(self, infile):
        """Add a file to document.

        Added file will have the same name.

        File will not copied in to docdir until sync().
        """
        with open(infile, 'r') as f:
            data = f.read()
        name = os.path.basename(infile)
        self.add_file_data(name, data)

    def get_files(self):
        """Return files associated with document."""
        return self._get_terms(self.db._find_prefix('file'))

    def get_fullpaths(self):
        """Return fullpaths of files associated with document."""
        list = []
        for path in self.get_files():
            # FIXME: this is a hack for old bad path specifications and should be removed
            if path.find(self.root) == 0:
                index = len(self.root) + 1
                path = path[index:]
            list.append(os.path.join(self.docdir, path))
        return list


    ########################################

    # SOURCES
    def _purge_sources_prefix(self, source):
        # purge all terms for a given source prefix
        prefix = self.db._make_source_prefix(source)
        for i in self._get_terms(prefix):
            self._remove_term(prefix, i)
        self._remove_term(self.db._find_prefix('source'), source)

    def add_sid(self, sid):
        """Add source sid to document."""
        source, oid = sid.split(':', 1)
        source = source.lower()
        # remove any existing terms for this source
        self._purge_sources_prefix(source)
        # add a term for the source
        self._add_term(self.db._find_prefix('source'), source)
        # add a term for the sid, with source as prefix
        self._add_term(self.db._make_source_prefix(source), oid)

    def get_sids(self):
        """Return a list of sids for document."""
        sids = []
        for source in self._get_terms(self.db._find_prefix('source')):
            for oid in self._get_terms(self.db._make_source_prefix(source)):
                sids.append('%s:%s' % (source, oid))
        return sids

    # BIBTEX KEYS
    def get_keys(self):
        """Return a list of bibtex citation keys associated with document."""
        prefix = self.db._find_prefix('key')
        return self._get_terms(prefix)

    # TAGS
    def add_tags(self, tags):
        """Add tags from list to document."""
        prefix = self.db._find_prefix('tag')
        for tag in tags:
            self._add_term(prefix, tag)

    def get_tags(self):
        """Return a list of tags associated with document."""
        prefix = self.db._find_prefix('tag')
        return self._get_terms(prefix)

    def remove_tags(self, tags):
        """Remove tags from a document."""
        prefix = self.db._find_prefix('tag')
        for tag in tags:
            self._remove_term(prefix, tag)

    # TITLE
    def _set_title(self, title):
        pt = self.db._find_prefix('title')
        for term in self._get_terms(pt):
            self._remove_term(pt, term)
        # FIXME: what's the clean way to get these prefixes?
        for term in self._get_terms('ZS'):
            self._remove_term('ZS', term)
        self._gen_terms(pt, title)

    # AUTHOR
    def _set_authors(self, authors):
        pa = self.db._find_prefix('author')
        for term in self._get_terms(pa):
            self._remove_term(pa, term)
        # FIXME: what's the clean way to get these prefixes?
        for term in self._get_terms('ZA'):
            self._remove_term('ZA', term)
        self._gen_terms(pa, authors)

    # YEAR
    def _set_year(self, year):
        # FIXME: what to do if year is not an int?
        try:
            year = int(year)
        except ValueError:
            pass
        prefix = self.db._find_prefix('year')
        for term in self._get_terms(prefix):
            self._remove_term(prefix, year)
        self._add_term(prefix, year)
        facet = self.db._find_facet('year')
        self.doc.add_value(facet, xapian.sortable_serialise(year))

    ########################################
    # bibtex

    def get_bibpath(self):
        """Return path to document bibtex file."""
        return os.path.join(self.docdir, 'bibtex')

    def _set_bibkey(self, key):
        prefix = self.db._find_prefix('key')
        for term in self._get_terms(prefix):
            self._remove_term(prefix, term)
        self._add_term(prefix, key)

    def _index_bibentry(self, bibentry):
        authors = bibentry.get_authors()
        fields = bibentry.get_fields()
        if 'title' in fields:
            self._set_title(fields['title'])
        if 'year' in fields:
            self._set_year(fields['year'])
        if authors:
            # authors should be a list, so we make a single text string
            # FIXME: better way to do this?
            self._set_authors(' '.join(authors))

        # add any sources in the bibtex
        for source in Sources().scan_bibentry(bibentry):
            self.add_sid(source.sid)

        # FIXME: index 'keywords' field as regular terms

        self._set_bibkey(bibentry.key)

    def add_bibentry(self, bibentry):
        """Add bibentry object."""
        self.bibentry = bibentry
        self._index_bibentry(self.bibentry)

    def add_bibtex(self, bibtex):
        """Add bibtex to document, as string or file path."""
        self.add_bibentry(Bibtex(bibtex)[0])

    def _load_bib(self):
        if self.bibentry:
            return
        bibpath = self.get_bibpath()
        if os.path.exists(bibpath):
            self.bibentry = Bibtex(bibpath)[0]

    def get_bibtex(self):
        """Get the bib for document as a bibtex string."""
        self._load_bib()
        if self.bibentry:
            return self.bibentry.as_string()
        else:
            return None

    def get_bibdata(self):
        self._load_bib()
        if self.bibentry:
            data = self.bibentry.get_fields()
            data['authors'] = self.bibentry.get_authors()
            return data
        else:
            return None

    def update_from_bibtex(self):
        """Update document metadata from document bibtex."""
        self._load_bib()
        self._index_bibentry(self.bibentry)

    ########################################

    def get_title(self):
        """Get the title from document bibtex."""
        self._load_bib()
        if not self.bibentry:
            return None
        fields = self.bibentry.get_fields()
        if 'title' in fields:
            return fields['title']
        return None

    def get_urls(self):
        """Get all URLs associated with document."""
        sources = Sources()
        urls = []
        # get urls associated with known sources
        for sid in self.get_sids():
            urls.append(sources[sid].url())
        # get urls from bibtex
        self._load_bib()
        if self.bibentry:
            fields = self.bibentry.get_fields()
            if 'url' in fields:
                urls.append(fields['url'])
            if 'adsurl' in fields:
                urls.append(fields['adsurl'])
        return urls
