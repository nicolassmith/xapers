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
import readline
from subprocess import call

from xapers.database import Database
from xapers.documents import Document
from xapers.documents import IllegalImportPath, ImportPathExists
import xapers.bibtex as bibparse
import xapers.source
import xapers.nci as nci

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


class UI():
    """Xapers command-line UI."""

    def __init__(self, xdir):
        self.xdir = xdir
        self.xdb = os.path.join(self.xdir, '.xapers')

    # prompt user for document metadata
    def prompt_for_metadata(self, data):
        isources = None
        itags = None

        source = None
        sid = None
        if 'sources' in data:
            for source in iter(data['sources']):
                sid = data['sources'][source]

        # db = Database(self.xdir, writable=False)
        # isources = db.get_terms('source')
        # itags = db.get_terms('tag')

        first = True
        while True:
            # get source
            if source:
                readline.set_startup_hook(lambda: readline.insert_text(source))
            else:
                readline.set_startup_hook()
            readline.parse_and_bind("tab: complete")
            completer = Completer(isources)
            readline.set_completer(completer.terms)
            source = raw_input('source: ')

            # get source id
            if sid:
                readline.set_startup_hook(lambda: readline.insert_text(sid))
            else:
                readline.set_startup_hook()
            readline.parse_and_bind('')
            readline.set_completer()
            sid = raw_input('sid: ')

            # get title
            if 'title' in data:
                readline.set_startup_hook(lambda: readline.insert_text(data['title']))
            else:
                readline.set_startup_hook()
            readline.parse_and_bind('')
            readline.set_completer()
            data['title'] = raw_input('title: ')

            # get authors
            if 'authors' in data:
                readline.set_startup_hook(lambda: readline.insert_text(data['authors']))
            else:
                readline.set_startup_hook()
            readline.parse_and_bind('')
            readline.set_completer()
            data['authors'] = raw_input('authors: ')

            # get year
            if 'year' in data:
                readline.set_startup_hook(lambda: readline.insert_text(data['year']))
            else:
                readline.set_startup_hook()
            readline.parse_and_bind('')
            readline.set_completer()
            data['year'] = raw_input('year: ')

            # get tags
            readline.set_startup_hook()
            readline.parse_and_bind("tab: complete")
            completer = Completer(itags)
            readline.set_completer(completer.terms)
            data['tags'] = []
            while True:
                tag = raw_input('tag: ')
                if tag:
                    data['tags'].append(tag.strip())
                else:
                    break

            print
            print "Is this data correct?:"
            print """
    url: %s
 source: %s
    sid: %s
  title: %s
authors: %s
   year: %s
   tags: %s
""" % (data['url'], source, sid, data['title'], data['authors'], data['year'], ' '.join(data['tags']))
            ret = raw_input("Enter to accept, 'r' to reenter, C-c to cancel: ")
            if ret is not 'r':
                break
            first = False

        data['sources'] = {source: sid}

        return data


    def add(self, infile, data=None, bibfile=None, prompt=False):
        if not infile and 'url' not in data and 'source' not in data:
            print >>sys.stderr, "Must specify file, url, or source:id to add."
            sys.exit(1)

        # FIXME: better checks about input file before prompting

        # find source object from specified source or url
        source = None
        if 'sources' in data:
            for ss,ii in data['sources'].items():
                break
            print >>sys.stderr, "Loading source: %s:%s" % (ss,ii)
            source = xapers.source.get_source(ss,ii)
        elif 'url' in data:
            # parse the url for source and sid
            print >>sys.stderr, "Parsing url: %s" % data['url']
            source = xapers.source.source_from_url(data['url'])

        if not source:
            print >>sys.stderr, 'No matching source module found.'

        bibtex = None
        bdata = None

        if bibfile:
            try:
                print >>sys.stderr, "Reading bibtex...",
                f = open(bibfile, 'r')
                bibtex = f.read()
                f.close()
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                raise
        elif source:
            try:
                print >>sys.stderr, "Retrieving bibtex...",
                bibtex = source.get_bibtex()
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                raise

        # now make the document
        db = Database(self.xdir, writable=True, create=True)

        doc = Document(db)

        if infile:
            path = os.path.abspath(infile)
            try:
                print >>sys.stderr, "Adding file '%s'..." % (path),
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
                doc.purge()
                raise

        if bibtex:
            try:
                print >>sys.stderr, "Adding bibtex...",
                doc.add_bibtex(bibtex)
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                doc.purge()
                raise

        if 'sources' in data:
            doc.add_sources(data['sources'])

        if 'tags' in data:
            doc.add_tags(data['tags'])

        try:
            print >>sys.stderr, "Syncing document...",
            doc.sync()
            print >>sys.stderr, "done (id:%s)." % doc.docid
        except:
            print >>sys.stderr, "\n"
            doc.purge()
            raise


    def delete(self, docid):
        resp = raw_input('Are you sure you want to delete documents ?: ' % docid)
        if resp != 'Y':
            print >>sys.stderr, "Aborting."
            sys.exit(1)
        db = Database(self.xdir, writable=True)
        db.delete_document(docid)


    def search(self, query_string, oformat='simple', limit=20):
        db = Database(self.xdir, writable=False)

        # FIXME: writing needs to be in a try to catch IOError
        # exception

        if oformat == 'tags' and query_string == '*':
            for tag in db.get_terms('tag'):
                print tag
            return
        if oformat == 'sources' and query_string == '*':
            for source in db.get_terms('source'):
                print source
            return

        for doc in db.search(query_string, limit=limit):
            docid = doc.get_docid()

            # FIXME: could this be multiple paths?
            fullpaths = doc.get_fullpaths()
            if fullpaths:
                fullpath = doc.get_fullpaths()[0]
            else:
                fullpath = None

            if oformat in ['file','files']:
                print "%s" % (fullpath)
                continue

            tags = doc.get_tags()
            sources = doc.get_sources_list()

            if oformat == 'simple':
                print "id:%s %s [%s] (%s)" % (docid,
                                              fullpath,
                                              ' '.join(sources),
                                              ' '.join(tags))
                continue

            if oformat == 'bibtex':
                bibtex = doc.get_bibtex()
                if not bibtex:
                    print >>sys.stderr, "No bibtex for doc id:%s." % docid
                else:
                    print bibtex
                    print
                continue

    def tag(self, query_string, add_tags, remove_tags):
        db = Database(self.xdir, writable=True)
        for doc in db.search(query_string):
            doc.add_tags(add_tags)
            doc.remove_tags(remove_tags)
        doc.sync()

    def dumpterms(self, query_string):
        db = Database(self.xdir)
        for doc in db.search(query_string):
            for term in doc.doc:
                print term.term

    def count(self, query_string):
        db = Database(self.xdir)
        count = db.count(query_string)
        print count

    def view(self, query_string):
        db = Database(self.xdir)
        for doc in db.search(query_string):
            path = doc.get_fullpaths()[0]
            call(' '.join(["okular", path]) + ' &', shell=True, stderr=open('/dev/null','w'))
            break
