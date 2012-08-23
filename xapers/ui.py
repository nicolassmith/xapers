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

from .database import Database
from .documents import Document

class UI():
    """Xapers command-line UI."""

    def __init__(self, xdir):
        self.xdir = xdir


    def import_file(self, infile):
        # open the database for update, creating a new database if necessary.
        db = Database(self.xdir, create=True, writable=True)

        url,sources,tags = query_metadata(db)
        print url,sources,tags

        db.add_document(infile,
                        url=url,
                        sources=sources,
                        tags=tags.append('new'))


    def add(self, infile, url=None, sources=None, tags=None):
        # open the database for update, creating a new database if necessary.
        db = Database(self.xdir, create=True, writable=True)

        db.add_document(infile,
                        url=url,
                        sources=sources,
                        tags=tags)


    def search(self, searchterms, oformat='full'):
        db = Database(self.xdir, writable=False)

        query_string = db.make_query_string(searchterms)

        if (oformat == 'tags') and (query_string == '*'):
            for tag in db.get_all_tags():
                print tag
            return

        if (oformat == 'sources') and (query_string == '*'):
            for tag in db.get_all_sources():
                print tag
            return

        matches = db.search(query_string)

        for m in matches:
            # FIXME: we shouldn't have to do this.  The iterator
            # should just return a xapers document
            doc = Document(db, doc=m.document)
            matchp = m.percent

            docid = doc.get_id()
            # FIXME: this could be multiple paths?
            fullpath = doc.get_full_path()[0]

            if oformat in ['file','files']:
                print "%s" % (fullpath)
                continue

            tags = doc.get_tags()
            sources = doc.get_sources()

            if oformat == 'simple':
                print "id:%s %s [%s] (%s)" % (docid, fullpath, ' '.join(sources), ' '.join(tags))
                continue

            if oformat == 'full':
                urls = doc.get_urls()
                data = doc.get_data()
                print "id:%s match:%i path:%s" % (docid, matchp, fullpath)
                print "url: %s" % (' '.join(urls))
                print "sources: %s" % (' '.join(sources))
                for source in sources:
                    sid = doc.get_source_id(source)
                    print " %s:%s" % (source, sid)
                print "tags: %s" % (' '.join(tags))
                print "data: %s\n" % (data)
                continue


    def tag(self, searchterms, add_tags, remove_tags):
        db = Database(self.xdir, create=True, writable=True)

        query_string = db.make_query_string(searchterms)

        matches = db.search(query_string)

        for m in matches:
            # FIXME: we shouldn't have to do this.  The iterator
            # should just return a xapers document
            doc = Document(db, doc=m.document)
            doc.add_tags(add_tags)
            doc.remove_tags(remove_tags)


    def count(self, searchterms):
        if not searchterms:
            searchterms = '*'

        db = Database(self.xdir, writable=False)

        query_string = db.make_query_string(searchterms)

        count = db.count(query_string)

        print count


    def view(self, searchterms):
        db = Database(self.xdir, writable=False)

        query_string = db.make_query_string(searchterms)

        matches = db.search(query_string)

        from subprocess import call
        for m in matches:
            doc = Document(db, m.document)
            path = doc.get_full_path()[0]
            print path
            sts = call(' '.join(["okular", path]), shell=True)
            break
