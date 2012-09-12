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
    def prompt_for_metadata(self, url):
        import readline
        import xapers.source

        isources = None
        itags = None

        smod = None
        sid = None
        source = None
        title = None
        authors = None
        year = None
        tags = None

        # db = Database(self.xdir, writable=False)
        # isources = db.get_terms('source')
        # itags = db.get_terms('tag')

        first = True
        while True:
            # get url
            readline.parse_and_bind('')
            if not url or (url and not first):
                if url:
                    readline.set_startup_hook(lambda: readline.insert_text(url))
                url = raw_input('url: ')

            # parse the url for source and sid
            # returns a source module and sid
            try:
                smod, sid = xapers.source.source_from_url(url)
            except:
                print >>sys.stderr, "Failed to parse url."

            # get data from source
            if smod:
                try:
                    source = smod.name
                    sdata = smod.get_data(sid, lfile='test/sources/doi.bib')
                    # sdata = smod.get_data(sid)
                    if sdata:
                        title = sdata['title'].encode('utf-8')
                        authors = sdata['authors'].encode('utf-8')
                        year = sdata['year'].encode('utf-8')
                except:
                    print >>sys.stderr, "Could not retrieve data from source."

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
            if title:
                readline.set_startup_hook(lambda: readline.insert_text(title))
            else:
                readline.set_startup_hook()
            readline.parse_and_bind('')
            readline.set_completer()
            title = raw_input('title: ')

            # get authors
            if authors:
                readline.set_startup_hook(lambda: readline.insert_text(authors))
            else:
                readline.set_startup_hook()
            readline.parse_and_bind('')
            readline.set_completer()
            authors = raw_input('authors: ')

            # get year
            if year:
                readline.set_startup_hook(lambda: readline.insert_text(year))
            else:
                readline.set_startup_hook()
            readline.parse_and_bind('')
            readline.set_completer()
            year = raw_input('year: ')

            # get tags
            readline.set_startup_hook()
            readline.parse_and_bind("tab: complete")
            completer = Completer(itags)
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
  title: %s
authors: %s
   year: %s
   tags: %s
""" % (url, source, sid, title, authors, year, ' '.join(tags))
            ret = raw_input("Enter to accept, 'r' to reenter, C-c to cancel: ")
            if ret is not 'r':
                break
            first = False

        sources = {source: sid}

        data = {}
        #for field in ['url', 'sources', 'title', 'authors', 'year', 'tags']:
        if url:
            data['url'] = url
        if sources:
            data['sources'] = sources
        if title:
            data['title'] = title
        if authors:
            data['authors'] = authors
        if year:
            data['year'] = year
        if tags:
            data['tags'] = tags

        return data


    def add(self, infile, data, prompt=False):
        if infile.find('http') == 0:
            url = infile
        else:
            url = None

        # resolve relative path
        fpath = os.path.abspath(infile)
        if fpath.find(self.xdir) == 0:
            index = len(self.xdir)
            rpath = fpath[index:].lstrip('/')

        # FIXME: if file not in xdir, move it there (w/ prompt)

        if prompt:
            try:
                data = self.prompt_for_metadata(url)
            except KeyboardInterrupt:
                print >>sys.stderr, "\nAborting.  Nothing imported."
                sys.exit(-1)

        db = Database(self.xdir, create=True, writable=True)
        db.add_document(rpath, data)


    def delete(self, query_string):
        db = Database(self.xdir, writable=True)
        db.delete_document(query_string)


    def search(self, query_string, limit=20, oformat='simple'):
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

        matches = db.search(query_string, limit=limit)

        if oformat == 'json':
            pass
            #print '[',

        for m in matches:
            # FIXME: we shouldn't have to do this.  The iterator
            # should just return a xapers document
            doc = Document(db, doc=m.document)
            matchp = m.percent

            docid = doc.get_docid()
            # FIXME: could this be multiple paths?
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

            url = doc.get_url()
            title = doc.get_title()
            authors = doc.get_authors()
            year = doc.get_year()
            data = doc.get_data()

            # FIXME: need to deal with encoding issues

            if oformat == 'full':
                print "id:%s" % (docid)
                print "match: %s" % (matchp)
                print "fullpath: %s" % (fullpath)
                print "url: %s" % (url)
                print "sources: %s" % (' '.join(sources))
                for source,sid in sources.items():
                    print " %s:%s" % (source, sid)
                print "tags: %s" % (' '.join(tags))
                print "title: %s" % (title)
                print "authors: %s" % (authors)
                print "year: %s" % (year)
                print "data: %s\n" % (data)
                continue

            if oformat == 'json':
                import json
                print json.dumps({
                    'docid': docid,
                    'percent': matchp,
                    'fullpath': fullpath,
                    'url': url,
                    'sources': sources,
                    'tags': tags,
                    'title': title,
                    'authors': authors,
                    'year': year,
                    #'data': data
                    },
                                 )

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
            sys.exit(1)

        doc = Document(db, doc=matches[0].document)

        if attribute == 'title':
            doc.set_title(value)
        elif attribute in ['author', 'authors']:
            doc.set_authors(value)
        elif attribute in ['year']:
            doc.set_year(value)
        else:
            print >>sys.stderr, "Unknown attribute '%s'." % (attribute)
            sys.exit(1)

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
        self.search('*',
                    limit=0,
                    oformat='json')

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
