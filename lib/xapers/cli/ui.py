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
import sets
import shutil
import readline
from subprocess import call

from xapers.database import Database, DatabaseError
from xapers.documents import Document
import xapers.bibtex as bibparse
import xapers.source

############################################################

def initdb(xdir, writable=False, create=False, force=False):
    try:
        return Database(xdir, writable=writable, create=create, force=force)
    except DatabaseError as e:
        print >>sys.stderr, e.msg
        print >>sys.stderr, 'Import a document to initialize.'
        sys.exit(e.code)

############################################################

class UI():
    """Xapers command-line UI."""

    def __init__(self, xdir):
        self.xdir = xdir
        self.db = None

    ##########

    def prompt_for_file(self, infile):
        if infile:
            print >>sys.stderr, 'file: %s' % infile
        else:
            readline.set_startup_hook()
            readline.parse_and_bind('')
            readline.set_completer()
            infile = raw_input('file: ')
            if infile == '':
                infile = None
        return infile

    def prompt_for_source(self, sources):
        if sources:
            readline.set_startup_hook(lambda: readline.insert_text(sources[0]))
        elif self.db:
            sources = self.db.get_terms('source')
        readline.parse_and_bind("tab: complete")
        completer = Completer(sources)
        readline.set_completer(completer.terms)
        source = raw_input('source: ')
        if source == '':
            source = None
        return source

    def prompt_for_tags(self, tags):
        # always prompt for tags, and append to initial
        if tags:
            print >>sys.stderr, 'initial tags: %s' % ' '.join(tags)
        else:
            tags = []
        if self.db:
            itags = self.db.get_terms('tag')
        else:
            itags = None
        readline.set_startup_hook()
        readline.parse_and_bind("tab: complete")
        completer = Completer(itags)
        readline.set_completer(completer.terms)
        while True:
            tag = raw_input('tag: ')
            if tag and tag != '':
                tags.append(tag.strip())
            else:
                break
        return tags

    ##########

    def add(self, docid, infile=None, source=None, tags=None, prompt=False):
        if prompt:
            infile = self.prompt_for_file(infile)
            if infile:
                # scan the file for source info
                print >>sys.stderr, "Scanning document for source identifiers..."
                sources = xapers.source.scan_for_sources(infile)
                if len(sources) == 0:
                    print >>sys.stderr, "0 source ids found."
                else:
                    print >>sys.stderr, "%d source ids found:" % (len(sources))
                    for ss in sources:
                        print >>sys.stderr, "  %s" % (ss)
            source = self.prompt_for_source(sources)
            tags = self.prompt_for_tags(tags)

        if not docid and not infile and not source:
            print >>sys.stderr, "Must specify file or source to import, or docid to update."
            sys.exit(1)

        bibtex = None
        smod = None
        if source and os.path.exists(source):
            bibfile = source
            try:
                print >>sys.stderr, "Reading bibtex...",
                with open(bibfile, 'r') as f:
                    bibtex = f.read()
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                raise

        elif source:
            print >>sys.stderr, "Parsing source: %s" % source
            smod = xapers.source.source_from_string(source)
            if not smod:
                print >>sys.stderr, 'No matching source module found.'
            else:
                try:
                    print >>sys.stderr, "Retrieving bibtex...",
                    (bibtex, url) = smod.get_bibtex()
                    print >>sys.stderr, "done: ",
                    print >>sys.stderr, "%s" % (url)
                except:
                    print >>sys.stderr, "\n"
                    raise

        # if docid provided, update that doc, otherwise create a new one
        # need a document from a writable db.
        self.db = initdb(self.xdir, writable=True, create=True)

        if docid:
            if docid.find('id:') == 0:
                docid = docid.split(':')[1]
            doc = self.db.doc_for_docid(docid)
            if not doc:
                print >>sys.stderr, "Failed to find document id:%s." % (docid)
                sys.exit(1)
        else:
            doc = Document(self.db)

        if infile:
            path = os.path.abspath(infile)
            try:
                print >>sys.stderr, "Adding file '%s'..." % (path),
                # FIXME: what to do if file already exists for document?
                doc.add_file(path)
                print >>sys.stderr, "done."
            # except IllegalImportPath:
            #     print >>sys.stderr, "\nFile path not in Xapers directory."
            #     sys.exit(1)
            # except ImportPathExists as e:
            #     print >>sys.stderr, "\nFile already indexed as %s." % (e.docid)
            #     sys.exit(1)
            except:
                print >>sys.stderr, "\n"
                if not docid:
                    print >>sys.stderr, "error, purging..."
                    doc.purge()
                raise

        if bibtex:
            try:
                print >>sys.stderr, "Adding bibtex...",
                doc.add_bibtex(bibtex)
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                if not docid:
                    print >>sys.stderr, "error, purging..."
                    doc.purge()
                raise
        elif docid:
            try:
                print >>sys.stderr, "Updating from bibtex...",
                doc.update_from_bibtex()
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                raise

        if tags:
            try:
                print >>sys.stderr, "Adding tags...",
                doc.add_tags(tags)
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                if not docid:
                    print >>sys.stderr, "error, purging..."
                    doc.purge()
                raise

        try:
            print >>sys.stderr, "Syncing document...",
            doc.sync()
            print >>sys.stderr, "done: ",
            print "id:%s" % doc.docid
        except:
            print >>sys.stderr, "\n"
            if not docid:
                print >>sys.stderr, "error, purging..."
                doc.purge()
            raise

        return doc.docid

    def delete(self, docid):
        self.db = initdb(self.xdir, writable=True)

        if docid.find('id:') == 0:
            docid = docid.split(':')[1]
        doc = self.db.doc_for_docid(docid)
        if not doc:
            print >>sys.stderr, "No document id:%s." % (docid)
            sys.exit(1)
        resp = raw_input('Are you sure you want to delete document id:%s?: ' % docid)
        if resp != 'Y':
            print >>sys.stderr, "Aborting."
            sys.exit(1)
        doc._rm_docdir()
        self.db.delete_document(docid)


    def update_all(self):
        self.db = initdb(self.xdir, writable=True)

        for doc in self.db.search('*', limit=0):
            try:
                print >>sys.stderr, "Updating %s..." % doc.docid,
                doc.update_from_bibtex()
                doc.sync()
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                raise

    ##########

    def tag(self, query_string, add_tags, remove_tags):
        self.db = initdb(self.xdir, writable=True)

        for doc in self.db.search(query_string):
            doc.add_tags(add_tags)
            doc.remove_tags(remove_tags)
            doc.sync()

    ##########

    def search(self, query_string, oformat='simple', limit=None):
        self.db = initdb(self.xdir)

        if oformat == 'tags' and query_string == '*':
            for tag in self.db.get_terms('tag'):
                print tag
            return
        if oformat == 'sources' and query_string == '*':
            for source in self.db.get_terms('source'):
                print source
            return

        otags = set([])
        osources = set([])
        for doc in self.db.search(query_string, limit=limit):
            docid = doc.get_docid()

            # FIXME: could this be multiple paths?
            fullpaths = doc.get_fullpaths()
            if fullpaths:
                fullpath = doc.get_fullpaths()[0]
            else:
                fullpath = ''

            if oformat in ['file','files']:
                print "%s" % (fullpath)
                continue

            tags = doc.get_tags()
            sources = doc.get_sources_list()

            if oformat == 'tags':
                otags = otags | set(tags)
                continue
            if oformat == 'sources':
                osources = osources | set(sources)
                continue

            title = doc.get_title()
            if not title:
                title = ''

            if oformat in ['summary']:
                print "id:%s [%s] (%s) \"%s\"" % (docid,
                                                   ' '.join(sources),
                                                   ' '.join(tags),
                                                   title,
                                                   )
                continue

            if oformat == 'bibtex':
                bibtex = doc.get_bibtex()
                if not bibtex:
                    print >>sys.stderr, "No bibtex for doc id:%s." % docid
                else:
                    print bibtex
                    print
                continue

        if oformat == 'tags':
            for tag in otags:
                print tag
            return
        if oformat == 'sources':
            for source in osources:
                print source
            return

    def count(self, query_string):
        self.db = initdb(self.xdir)

        count = self.db.count(query_string)
        print count

    ##########

    def dumpterms(self, query_string):
        self.db = initdb(self.xdir)

        for doc in self.db.search(query_string):
            for term in doc.doc:
                print term.term

    ##########

    def export(self, outdir, query_string):
        self.db = initdb(self.xdir)

        try:
            os.makedirs(outdir)
        except:
            pass
        for doc in self.db.search(query_string):
            orig = doc.get_fullpaths()[0]
            title = doc.get_title()
            name = '%s.pdf' % (title.replace(' ','_'))
            outpath = os.path.join(outdir,name)
            print outpath
            shutil.copyfile(orig, outpath)

    ##########

    def restore(self):
        self.db = initdb(self.xdir, writable=True, create=True, force=True)
        self.db.restore(log=True)

############################################################

# readline completion class
class Completer:
    def __init__(self, words):
        self.words = words
    def terms(self, prefix, index):
        matching_words = [
            w for w in self.words if w.startswith(prefix)
            ]
        try:
            return matching_words[index]
        except IndexError:
            return None
