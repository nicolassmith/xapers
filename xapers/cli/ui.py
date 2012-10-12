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

    def prompt_add_simple(self, infile, source, tags):
        db = Database(self.xdir, writable=False)

        if not infile:
            readline.set_startup_hook()
            readline.parse_and_bind('')
            readline.set_completer()
            infile = raw_input('file: ')
            if infile == '':
                infile = None

        if not source:
            isources = db.get_terms('source')
            readline.set_startup_hook()
            readline.parse_and_bind("tab: complete")
            completer = Completer(isources)
            readline.set_completer(completer.terms)
            source = raw_input('source: ')
            if source == '':
                source = None

        if not tags:
            itags = db.get_terms('tag')
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

        return infile, source, tags

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


    def add(self, docid, infile=None, source=None, tags=None, prompt=False):
        if prompt:
            infile, source, tags = self.prompt_add_simple(infile, source, tags)

        if not docid and not infile and not source:
            print >>sys.stderr, "Must specify file or source to import, or docid to update."
            sys.exit(1)

        bibtex = None
        smod = None
        if source and os.path.exists(source):
            bibfile = source
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
            print >>sys.stderr, "Parsing source: %s" % source
            smod = xapers.source.source_from_string(source)
            if not smod:
                print >>sys.stderr, 'No matching source module found.'
            else:
                try:
                    print >>sys.stderr, "Retrieving bibtex...",
                    bibtex = smod.get_bibtex()
                    print >>sys.stderr, "done."
                except:
                    print >>sys.stderr, "\n"
                    raise

        # now make the document
        db = Database(self.xdir, writable=True, create=True)

        # if docid provided, update that doc, otherwise create a new one
        if docid:
            if docid.find('id:') == 0:
                docid = docid.split(':')[1]
            doc = db.doc_for_docid(docid)
            if not doc:
                print >>sys.stderr, "Failed to find document id:%s." % (docid)
                sys.exit(1)
        else:
            doc = Document(db)

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
            print >>sys.stderr, "done:"
            print "id:%s" % doc.docid
        except:
            print >>sys.stderr, "\n"
            if not docid:
                print >>sys.stderr, "error, purging..."
                doc.purge()
            raise

        return doc.docid


    def delete(self, docid):
        if docid.find('id:') == 0:
            docid = docid.split(':')[1]
        db = Database(self.xdir, writable=True)
        doc = db.doc_for_docid(docid)
        if not doc:
            print >>sys.stderr, "No document id:%s." % (docid)
            sys.exit(1)
        resp = raw_input('Are you sure you want to delete document id:%s?: ' % docid)
        if resp != 'Y':
            print >>sys.stderr, "Aborting."
            sys.exit(1)
        doc._rm_docdir()
        db.delete_document(docid)


    def update_all(self):
        db = Database(self.xdir, writable=True)
        for doc in db.search('*', limit=0):
            try:
                print >>sys.stderr, "Updating %s..." % doc.docid,
                doc.update_from_bibtex()
                doc.sync()
                print >>sys.stderr, "done."
            except:
                print >>sys.stderr, "\n"
                raise


    def search(self, query_string, oformat='simple', limit=None):
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
