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

def initdb(xroot, writable=False, create=False, force=False):
    try:
        return Database(xroot, writable=writable, create=create, force=force)
    except DatabaseError as e:
        print >>sys.stderr, e.msg
        print >>sys.stderr, 'Import a document to initialize.'
        sys.exit(e.code)

############################################################

class UI():
    """Xapers command-line UI."""

    def __init__(self, xroot):
        self.xroot = xroot
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

    ############################################

    def add(self, query_string, infile=None, source=None, tags=None, prompt=False):

        doc = None
        bibtex = None
        smod = None

        ##################################
        # open db and get doc

        self.db = initdb(self.xroot, writable=True, create=True)

        # if query provided, find single doc to update
        if query_string:
            if self.db.count(query_string) != 1:
                print >>sys.stderr, "Search did not match a single document.  Aborting."
                sys.exit(1)

            for doc in self.db.search(query_string):
                break

        ##################################
        # do fancy option prompting

        if prompt:
            infile = self.prompt_for_file(infile)

        if infile:
            infile = os.path.expanduser(infile)
            if not os.path.exists(infile):
                print >>sys.stderr, "Specified file '%s' not found." % infile
                sys.exit(1)

        if prompt:
            sources = []
            if source:
                sources = [source]
            # scan the file for source info
            if infile:
                print >>sys.stderr, "Scanning document for source identifiers..."
                ss = xapers.source.scan_for_sources(infile)
                print >>sys.stderr, "%d source ids found:" % (len(sources))
                if len(sources) > 0:
                    for sid in ss:
                        print >>sys.stderr, "  %s" % (sid)
                    sources += ss
            source = self.prompt_for_source(sources)
            tags = self.prompt_for_tags(tags)

        if not query_string and not infile and not source:
            print >>sys.stderr, "Must specify file or source to import, or query to update existing document."
            sys.exit(1)

        ##################################
        # process source and get bibtex

        # check if source is a file, in which case interpret it as bibtex
        if source and os.path.exists(source):
            bibtex = source

        elif source:
            try:
                smod = xapers.source.get_source(source)
            except xapers.source.SourceError as e:
                print >>sys.stderr, e
                sys.exit(1)

            sid = smod.get_sid()
            if not sid:
                print >>sys.stderr, "Source ID not specified."
                sys.exit(1)

            # check that the source doesn't match an existing doc
            for tdoc in self.db.search(sid):
                if doc:
                    if tdoc != doc:
                        print >>sys.stderr, "Document already exists for source '%s'.  Aborting." % (sid)
                        sys.exit(1)
                else:
                    print >>sys.stderr, "Updating existing document..."
                    doc = tdoc
                break

        ##################################

        # if we still don't have a doc, create a new one
        if not doc:
            doc = Document(self.db)

        ##################################
        # not fetch the bibtex

        if smod:
            try:
                print >>sys.stderr, "Retrieving bibtex...",
                bibtex = smod.get_bibtex()
                print >>sys.stderr, "done."
            except Exception, e:
                print >>sys.stderr, "\n"
                print >>sys.stderr, "Could not retrieve bibtex: %s" % e
                sys.exit(1)

        ##################################
        # add stuff to the doc

        if infile:
            path = os.path.abspath(infile)
            try:
                print >>sys.stderr, "Adding file '%s'..." % (path),
                # FIXME: check if file already exists?
                doc.add_file(path)
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                raise

        if bibtex:
            try:
                print >>sys.stderr, "Adding bibtex...",
                doc.add_bibtex(bibtex)
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
                raise

        ##################################
        # sync the doc to db and disk

        try:
            print >>sys.stderr, "Syncing document...",
            doc.sync()
            print >>sys.stderr, "done.\n",
        except:
            print >>sys.stderr, "\n"
            raise

        print "id:%s" % doc.docid
        return doc.docid

    ############################################

    def delete(self, query_string, prompt=True):
        self.db = initdb(self.xroot, writable=True)
        count = self.db.count(query_string)
        if count == 0:
            print >>sys.stderr, "No documents found for query."
            sys.exit(1)
        if prompt:
            resp = raw_input("Type 'yes' to delete %d documents: " % count)
            if resp != 'yes':
                print >>sys.stderr, "Aborting."
                sys.exit(1)
        for doc in self.db.search(query_string):
            doc.purge()

    ############################################

    def update_all(self):
        self.db = initdb(self.xroot, writable=True)
        for doc in self.db.search('*', limit=0):
            try:
                print >>sys.stderr, "Updating %s..." % doc.docid,
                doc.update_from_bibtex()
                doc.sync()
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                raise

    ############################################

    def tag(self, query_string, add_tags, remove_tags):
        self.db = initdb(self.xroot, writable=True)

        for doc in self.db.search(query_string):
            doc.add_tags(add_tags)
            doc.remove_tags(remove_tags)
            doc.sync()

    ############################################

    def search(self, query_string, oformat='simple', limit=None):
        self.db = initdb(self.xroot)

        if oformat == 'tags' and query_string == '*':
            for tag in self.db.get_terms('tag'):
                print tag
            return
        if oformat == 'sources' and query_string == '*':
            for source in self.db.get_sids():
                print source
            return

        otags = set([])
        osources = set([])
        for doc in self.db.search(query_string, limit=limit):
            docid = doc.get_docid()

            if oformat in ['file','files']:
                # FIXME: could this be multiple paths?
                for path in doc.get_fullpaths():
                    print "%s" % (path)
                continue

            tags = doc.get_tags()
            sources = doc.get_sids()

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

    ############################################

    def count(self, query_string):
        self.db = initdb(self.xroot)

        count = self.db.count(query_string)
        print count

    ############################################

    def dumpterms(self, query_string):
        self.db = initdb(self.xroot)

        for doc in self.db.search(query_string):
            for term in doc.doc:
                print term.term

    ############################################

    def export(self, outdir, query_string):
        self.db = initdb(self.xroot)

        try:
            os.makedirs(outdir)
        except:
            pass
        for doc in self.db.search(query_string):
            origpaths = doc.get_fullpaths()
            nfiles = len(origpaths)
            for path in origpaths:
                title = doc.get_title()
                if not title:
                    name = os.path.basename(os.path.splitext(path)[0])
                else:
                    name = '%s' % (title.replace(' ','_'))
                ind = 0
                if nfiles > 1:
                    name += '.%s' % ind
                    ind += 1
                name += '.pdf'
                outpath = os.path.join(outdir,name)
                print outpath
                shutil.copyfile(path, outpath)

    ############################################

    def restore(self):
        self.db = initdb(self.xroot, writable=True, create=True, force=True)
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
