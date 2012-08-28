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

from xapers.database import Database
from xapers.documents import Document
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
    def prompt_for_metadata(self, db):
        import readline

        url = None
        source = None
        sid = None
        tags = None

        sources = db.get_terms('source')
        tags = db.get_terms('tag')

        while True:
            if url:
                readline.set_startup_hook(lambda: readline.insert_text(url))
            url = raw_input('url: ')
        
            readline.parse_and_bind("tab: complete")
            if source:
                readline.set_startup_hook(lambda: readline.insert_text(source))
            completer = Completer(sources)
            readline.set_completer(completer.terms)
            source = raw_input('source: ')

            if sid:
                readline.set_startup_hook(lambda: readline.insert_text(sid))
            readline.set_completer()
            # FIXME: we don't want to tab complete here
            readline.parse_and_bind('')
            sid = raw_input('sid: ')

            # FIXME: remove 'new' from list
            readline.set_startup_hook()
            completer = Completer(tags)
            readline.set_completer(completer.terms)
            tags = []
            while True:
                tag = raw_input('tag: ')
                if tag:
                    tags.append(tag.strip())
                else:
                    break

            print
            print "Is this data correct?:"
            print """
   url: %s
source: %s
   sid: %s
  tags: %s
""" % (url, source, sid, ' '.join(tags))
            ret = raw_input("Enter to accept, 'r' to reenter, C-c to cancel: ")
            if ret is not 'r':
                break

        sources = {source: sid}
        return url, sources, tags


    def import_document(self, infile):
        # FIXME: don't open the database for writing, just get the
        # sources and tags and close it.
        db = Database(self.xdir, create=True, writable=True)

        try:
            url,sources,tags = self.prompt_for_metadata(db)
        except KeyboardInterrupt:
            print >>sys.stderr, "\nAborting.  Nothing imported."
            sys.exit()

        db.add_document(infile,
                        url=url,
                        sources=sources,
                        tags=tags)


    def add(self, infile, url=None, sources=None, tags=None):
        db = Database(self.xdir, create=True, writable=True)

        db.add_document(infile,
                        url=url,
                        sources=sources,
                        tags=tags)


    def search(self, query_string, oformat='simple'):
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

        matches = db.search(query_string)

        if oformat == 'json':
            pass
            #print '[',

        ii = 0
        for m in matches:
            ii += 1
            if ii == 20:
                break

            # FIXME: we shouldn't have to do this.  The iterator
            # should just return a xapers document
            doc = Document(db, doc=m.document)
            matchp = m.percent

            docid = doc.get_docid()
            # FIXME: this could be multiple paths?
            fullpath = doc.get_fullpaths()[0]

            if oformat in ['file','files']:
                print "%s" % (fullpath)
                continue

            tags = doc.get_tags()
            sources = doc.get_sources()

            if oformat == 'simple':
                print "id:%s %s [%s] (%s)" % (docid,
                                              fullpath,
                                              ' '.join(sources.keys()),
                                              ' '.join(tags))
                continue

            urls = doc.get_urls()
            data = doc.get_data()
            title = doc.get_title()

            # FIXME: need to deal with encoding issues

            if oformat == 'full':
                print "id:%s match:%i path:%s" % (docid, matchp, fullpath)
                print "url: %s" % (' '.join(urls))
                print "sources: %s" % (' '.join(sources))
                for source,sid in sources.items():
                    print " %s:%s" % (source, sid)
                print "tags: %s" % (' '.join(tags))
                if title:
                    print "title: %s" % (title)
                print "data: %s\n" % (data)
                continue

            if oformat == 'json':
                import json
                print json.dumps([{
                    'docid': docid,
                    'percent': matchp,
                    #'fullpath': fullpath,
                    #'urls': urls,
                    'year': 2010,
                    'tags': tags,
                    'title': 'foo',
                    #'sources': sources,
                    #'data': data
                    }],
                                 ),

        if oformat == 'json':
            pass
            #print ']'


    def select(self, query_string):
        nci.UI(self.xdb, query_string)


    def tag(self, query_string, add_tags, remove_tags):
        db = Database(self.xdir, writable=True)
        matches = db.search(query_string)
        for m in matches:
            # FIXME: we shouldn't have to do this.  The iterator
            # should just return a xapers document
            doc = Document(db, doc=m.document)
            doc.add_tags(add_tags)
            doc.remove_tags(remove_tags)

    def set(self, query_string, attribute, value):
        db = Database(self.xdir, writable=True)
        matches = db.search(query_string)

        if len(matches) > 1:
            print >>sys.stderr, "Query matches more than one document.  Aborting."
            sys.exit()

        doc = Document(db, doc=matches[0].document)

        if attribute == 'title':
            doc.set_title(value)
        if attribute in ['author', 'authors']:
            doc.set_authors(value)

    def dumpterms(self, query_string):
        db = Database(self.xdir, create=True, writable=True)
        matches = db.search(query_string)
        for m in matches:
            doc = Document(db, m.document)
            for term in doc.doc:
                print term.term

    def count(self, query_string):
        db = Database(self.xdir, writable=False)
        count = db.count(query_string)
        print count

    def view(self, query_string):
        db = Database(self.xdir, writable=False)
        matches = db.search(query_string)
        from subprocess import call
        for m in matches:
            doc = Document(db, m.document)
            path = doc.get_fullpaths()[0]
            call(' '.join(["okular", path]) + ' &', shell=True, stderr=open('/dev/null','w'))
            #os.system(' '.join(["okular", path]) + ' &')
            #os.execlp('okular', path)
            break

    def dump(self, query_string):
        import json
        db = Database(self.xdir, writable=False)
        matches = db.search(query_string)
        for m in matches:
            doc = Document(db, m.document)
            #fullpath = os.path.join(self.xdir,doc.get_urls()[0].lstrip('/'))
            fullpath = doc.get_fullpath()
            tags = doc.get_tags()
            sources = doc.get_sources()

            print json.dumps({'fullpath': fullpath,
                              'tags': tags,
                              'sources': sources},
                             sort_keys=True
                             )

    def restore(self):
        import json
        import urllib
        
        db = Database(self.xdir, writable=True)

        for line in sys.stdin:
            parsed =  json.loads(line)
            fullpath = urllib.unquote(parsed['fullpath'])
            sources = parsed['sources']
            tags = parsed['tags']

            # FIXME: add or append as needed
            # db.add_document(fullpath,
            #                 sources=sources,
            #                 tags=tags)
