import os
import sys
import xapian

from .documents import Documents, Document

# FIXME: add db schema documentation

##################################################

class DatabaseError(Exception):
    """Base class for Xapers database exceptions."""
    pass

##################################################

class Database():
    """Represents a Xapers database"""

    # http://xapian.org/docs/omega/termprefixes.html
    BOOLEAN_PREFIX_INTERNAL = {
        'url': 'U',
        'file': 'P',

        # FIXME: use this for doc mime type
        'type': 'T',
        }
            
    BOOLEAN_PREFIX_EXTERNAL = {
        'id': 'Q',

        'source': 'XSOURCE:',
        'tag': 'K',
        'fulltitle': 'XTITLE:',
        'fullauthors': 'XAUTHORS:',

        'year': 'Y',
        }

    PROBABILISTIC_PREFIX = {
        'title': 'S',
        'author': 'A',
        }

    # FIXME: need to set the following value fields:
    # publication date
    # added date
    # modified date

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

    def __init__(self, root, writable=False, create=False):
        # xapers root
        self.root = os.path.abspath(root)

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

    # generate a new doc id, based on the last availabe doc id
    def _generate_docid(self):
        return self.xapian_db.get_lastdocid() + 1

    # Return the xapers-relative path for a path
    # If the the specified path is not in the xapers root, return None.
    def _basename_for_path(self, path):
        if path.find('/') == 0:
            if path.find(self.root) == 0:
                index = len(self.root) + 1
                base = path[index:]
            else:
                # FIXME: should this be an exception?
                base = None
        else:
            base = path

        full = None
        if base:
            full = os.path.join(self.root, base)

        return base, full

    ########################################

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

    ########################################

    # search for documents based on query string
    def _search(self, query_string, limit=0):
        enquire = xapian.Enquire(self.xapian_db)

        if query_string == "*":
            query = xapian.Query.MatchAll
        else:
            # parse the query string to produce a Xapian::Query object.
            query = self.query_parser.parse_query(query_string)

        # FIXME: need to catch Xapian::Error when using enquire
        enquire.set_query(query)

        # FIXME: can set how the mset is ordered
        if limit > 0:
            mset = enquire.get_mset(0, limit)
        else:
            mset = enquire.get_mset(0, self.xapian_db.get_doccount())

        return mset

    def search(self, query_string, limit=0):
        """Search for documents in the database."""
        mset = self._search(query_string, limit)
        return Documents(self, mset)

    def count(self, query_string):
        """Count documents matching search terms."""
        return self._search(query_string, count=0).get_matches_estimated()

    def _doc_for_term(self, term):
        enquire = xapian.Enquire(self.xapian_db)
        query = xapian.Query(term)
        enquire.set_query(query)
        mset = enquire.get_mset(0, 2)
        # FIXME: need to throw an exception if more than one match found
        if mset:
            return Document(self, mset[0].document)
        else:
            return None

    def doc_for_docid(self, docid):
        """Return document for specified docid."""
        term = self._find_prefix('id') + docid
        return self._doc_for_term(term)

    def doc_for_path(self, path):
        """Return document for specified path."""
        term = self._find_prefix('file') + path
        return self._doc_for_term(term)

    ########################################

    def delete_document(self, docid):
        self.xapian_db.delete_document(docid)
