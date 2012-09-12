import os
import sys
import xapian

from .documents import Document

# FIXME: add db schema documentation

class Database():
    """Represents a Xapers database"""

    # http://xapian.org/docs/omega/termprefixes.html
    BOOLEAN_PREFIX_INTERNAL = {
        'url': 'U',
        'file': 'P',

        # FIXME: use this
        'type': 'T',
        }
            
    BOOLEAN_PREFIX_EXTERNAL = {
        'id': 'Q',

        # user defined
        'tag': 'K',
        'source': 'XSOURCE:',
        'fulltitle': 'XTITLE:',
        'fullauthors': 'XAUTHORS:',

        'year': 'Y',
        #'added': ?
        #'viewed': ?
        }

    PROBABILISTIC_PREFIX = {
        'title': 'S',
        'subject': 'S',
        'author': 'A',
        }

    def _find_prefix(self, name):
        if name in self.BOOLEAN_PREFIX_INTERNAL:
            return self.BOOLEAN_PREFIX_INTERNAL[name]
        if name in self.BOOLEAN_PREFIX_EXTERNAL:
            return self.BOOLEAN_PREFIX_EXTERNAL[name]
        if name in self.PROBABILISTIC_PREFIX:
            return self.PROBABILISTIC_PREFIX[name]
        # FIXME: raise internal error for unknown name

    def _make_source_prefix(self, source):
        return 'X%s:' % (source.upper())

    def __init__(self, root, create=False, writable=False):
        # xapers root
        self.root = root

        # xapers db directory
        self.xapers_path = os.path.join(self.root, '.xapers')
        if create and not os.path.exists(self.xapers_path):
            os.makedirs(self.xapers_path)

        # FIXME: need a try/except here to catch db open errors

        # the Xapian db
        xapian_db = os.path.join(self.xapers_path, 'xapian')
        if writable:
            self.xapian_db = xapian.WritableDatabase(xapian_db, xapian.DB_CREATE_OR_OPEN)
        else:
            self.xapian_db = xapian.Database(xapian_db)

        stemmer = xapian.Stem("english")

        # The Xapian TermGenerator
        # http://trac.xapian.org/wiki/FAQ/TermGenerator
        self.term_gen = xapian.TermGenerator()
        self.term_gen.set_stemmer(stemmer)

        # The Xapian QueryParser
        self.query_parser = xapian.QueryParser()
        self.query_parser.set_database(self.xapian_db)
        self.query_parser.set_stemmer(stemmer)
        self.query_parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)

        # add boolean internal prefixes
        for name, prefix in self.BOOLEAN_PREFIX_EXTERNAL.iteritems():
            self.query_parser.add_boolean_prefix(name, prefix)

        # add probabalistic prefixes
        for name, prefix in self.PROBABILISTIC_PREFIX.iteritems():
            self.query_parser.add_prefix(name, prefix)

        # last docid in the database
        self.last_docid = self.xapian_db.get_lastdocid()

    # generate a new doc id, based on the last availabe doc id
    def _generate_docid(self):
        self.last_docid += 1
        return self.last_docid

    # return a list of terms for prefix
    # FIXME: is this the fastest way to do this?
    def _get_terms(self, prefix):
        list = []
        for term in self.xapian_db:
            if term.term.find(prefix) == 0:
                index = len(prefix)
                list.append(term.term[index:])
        return list

    def get_terms(self, name):
        """Get terms associate with name."""
        prefix = self._find_prefix(name)
        return self._get_terms(prefix)

    def add_document(self,
                     path,
                     data=None):
        """Add a document to the database

        :param path: should be a path relative to the path of the
            open database (see :meth:`get_path`), or else should be an
            absolute filename with initial components that match the
            path of the database.

            The file should be a single mail message (not a
            multi-message mbox) that is expected to remain at its
            current location, since the notmuch database will reference
            the filename, and will not copy the entire contents of the
            file.

        :param url: a url associated with the file.

        :param sources: a dictionary of source:id values.

        :param tags: initial tags to apply to document.
        """

        print >>sys.stderr, "adding '%s'..." % (path),

        # FIXME: check it path has already been indexed
        # search for an existing document given the path
        # if none exists do something
        # FIXME: THIS ISN"T WORKING!!!!
        doc = self._find_doc_for_path(path)
        if doc:
            print >>sys.stderr, " already indexed (id:%s)" % (doc.get_id())
            return

        doc = Document(self)

        doc._index_file(path)

        if 'url' in data:
            doc._set_url(data['url'])

        if 'sources' in data:
            for source,sid in data['sources'].items():
                doc._add_source(source, sid)

        if 'title' in data:
            doc._set_title(data['title'])

        if 'authors' in data:
            doc._set_authors(data['authors'])

        if 'tags' in data:
            for tag in data['tags']:
                doc._add_tag(tag)

        # FIXME: should these operations all sync themselves?  what is
        # the cost of that?
        doc._sync()

        print >>sys.stderr, " id:%s" % (doc.get_docid())

    def get_doc(self, docid):
        enquire = xapian.Enquire(self.xapian_db)
        query = self.query_parser.parse_query('id:' + str(docid))
        enquire.set_query(query)
        matches = enquire.get_mset(0, self.xapian_db.get_doccount())
        if len(matches) > 1:
            print >>sys.stderr, "Query does not match a single document."
            return None
        return Document(self, matches[0].document)

    def delete_document(self, docid):
        resp = raw_input('Are you sure you want to delete documents ?: ' % docid)
        if resp != 'Y':
            print >>sys.stderr, "Aborting."
            sys.exit(1)
        self.xapian_db.delete_document(docid)

    def replace_docfile(self, docid, file):
        print >>sys.stderr, "not implemented."
        return
        doc = enquire = xapian.Enquire(self.xapian_db)
        query = self.query_parser.parse_query('id:' + str(docid))
        enquire.set_query(query)
        matches = enquire.get_mset(0, self.xapian_db.get_doccount())
        if len(matches) > 1:
            print >>sys.stderr, "Query does not match a single document.  Aborting."
            sys.exit(1)
        self.xapian_db.delete_document(m.document.get_docid())

    def _find_doc_for_path(self, filename):
        query_string = self._find_prefix('file') + filename
        enquire = xapian.Enquire(self.xapian_db)
        query = self.query_parser.parse_query(query_string)
        matches = enquire.get_mset(0, self.xapian_db.get_doccount())
        if matches:
            return Document(matches[0].document)
        else:
            return None

    def _search(self, query_string, limit=0):
        enquire = xapian.Enquire(self.xapian_db)

        if query_string == "*":
            query = xapian.Query.MatchAll
        else:
            # parse the query string to produce a Xapian::Query object.
            query = self.query_parser.parse_query(query_string)

        #print >>sys.stderr, "parsed query: %s" % str(query)

        enquire.set_query(query)

        if limit > 0:
            matches = enquire.get_mset(0, limit)
        else:
            matches = enquire.get_mset(0, self.xapian_db.get_doccount())

        return matches

    def search(self, query_string, limit=0):
        """Search for documents in the database."""

        # FIXME: this should return an iterator over Documents
        #return Documents(self, self._search(terms, count))
        return self._search(query_string, limit)

    def count(self, query_string):
        """Count documents matching search terms."""
        return self._search(query_string, count=0).get_matches_estimated()
