#!/usr/bin/env python

import os
import sys
import xapian

########################################################################
# TODO:

# proper docid
#   how to search by docid?

# doc class

# index here, instead of relying on omindex

# store bibtex in data
#   - want add_bibtex function, that parses the bibtex to add terms:
#     - author
#     - title
#     - pub date
#   - add ability to modify data for document
#   - dump file --> dump directories, in git!

########################################################################

# these should match what is defined in omindex
boolean_prefix = {
    # FIXME: this should map to something better, somehow
    'id': 'U',
    'tag': 'K',
    'day': 'D',
    'month': 'M',
    'year': 'Y',
    'url': 'U',
    'file': 'U',
    }
probabilistic_prefix = {
    'title': 'S',
    'author': 'A',
    'type': 'T',
    'dir': 'P',
    }

def find_prefix(name):
    if name in boolean_prefix:
        return boolean_prefix[name]
    if name in probabilistic_prefix:
        return probabilistic_prefix[name]

class Xapers():
    def __init__(self, path, writable=False):
        self.xapers_path = os.path.join(path, '.xapers')

        xapian_db = os.path.join(self.xapers_path, 'xapian')
        if writable:
            self.xapian_db = xapian.WritableDatabase(xapian_db, xapian.DB_CREATE_OR_OPEN)
        else:
            self.xapian_db = xapian.Database(xapian_db)

        stemmer = xapian.Stem("english")

        self.term_gen = xapian.TermGenerator()
        self.term_gen.set_stemmer(stemmer)

        self.query_parser = xapian.QueryParser()
        self.query_parser.set_database(self.xapian_db)
        self.query_parser.set_stemmer(stemmer)
        self.query_parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)

        for name, prefix in boolean_prefix.iteritems():
            self.query_parser.add_boolean_prefix(name, prefix)

        for name, prefix in probabilistic_prefix.iteritems():
            self.query_parser.add_prefix(name, prefix)

    def search(self, terms, count=0):
        # start an enquire session.
        enquire = xapian.Enquire(self.xapian_db)

        # combine the with spaces between them, so that simple queries
        # don't have to be quoted at the shell level.
        # FIXME: is this the best way to form query?
        query_string = str.join(' ', terms)

        if query_string == "*":
            query = xapian.Query.MatchAll
        else:
            # parse the query string to produce a Xapian::Query object.
            query = self.query_parser.parse_query(query_string)

        #print >>sys.stderr, "parsed query: %s" % str(query)

        enquire.set_query(query)

        if count > 0:
            matches = enquire.get_mset(0, count)
        else:
            matches = enquire.get_mset(0, self.xapian_db.get_doccount())

        return matches


########################################################################

# return a list of terms for prefix
def doc_get_terms(doc, prefix):
    list = []
    for term in doc:
        if term.term[0] == prefix:
            list.append(term.term.lstrip(prefix))
    return list

# FIXME: we output the relative path as an ad-hoc doc id.
# this should really just be the actual docid, and we need
# a way to access docs by docid directly (via "id:")
def doc_get_docid(doc):
    return doc_get_terms(doc, find_prefix('file'))[0]

def doc_get_tags(doc):
    return doc_get_terms(m.document, find_prefix('tag'))

def doc_get_full_path(doc, xdir):
    paths = doc_get_terms(m.document, find_prefix('file'))
    return [os.path.abspath(xdir+f) for f in paths]

def parse_omega_data(data):
    return data

########################################################################

def usage():
    prog = os.path.basename(sys.argv[0])
    print "Usage:", prog, "<command> [args...]"
    print """
  new [--verbose]                             update database
  search [--output=] <search-term>...         search the database
    output = [full|simple|file]
  tag +tag|-tab [...] [--] <search-term>...   add/remove tags
  see <search-term>...                        display first result
  count <search-term>...                      count matches
  dump [<search-terms>...]                    dump tags to stdout
  help                                        this help
"""

if __name__ == '__main__':

    try:
        xdir = os.environ['XAPERS_DIR']
    except:
        print >>sys.stderr, "XAPERS_DIR environment variable not specified."
        sys.exit(1)
    if not os.path.isdir(xdir):
        print >>sys.stderr, "XAPERS_DIR '%s' does not exist." % (xdir)
        sys.exit(2)
    if 'XAPERS_DB' in os.environ:
        xdb = os.environ['XAPERS_DB']
    else:
        xdb = os.path.join(xdir,'.xapers','xapian')

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = []

    ########################################
    if cmd == 'new':
        try:
            os.makedirs(xdb)
        except:
            pass
        omindex = [
            '~/src/xapian/xapian/xapian-applications/omega/omindex',
	    '--follow',
	    '--db', xdb,
            '--url', '/',
            ]
        for arg in sys.argv[2:]:
            omindex.append(arg)
        omindex.append(xdir)
        from subprocess import Popen, PIPE
        p = Popen(' '.join(omindex), shell=True)
        if p.wait() != 0:
            print "There were some errors"

    ########################################
    elif cmd == 'search':
        argc = 2
        oformat = 'full'
        if '--output=' in sys.argv[argc]:
            oformat = sys.argv[argc].split('=')[1]
            argc += 1
        searchterms = sys.argv[argc:]

        xapers = Xapers(xdir, writable=False)

        matches = xapers.search(searchterms)

        for m in matches:
            docid = doc_get_docid(m.document)

            if oformat in ['file','files']:
                for fullpath in doc_get_full_path(m.document, xdir):
                    print "%s" % (fullpath)
                    continue

            tags = doc_get_tags(m.document)

            if oformat == 'simple':
                print "id:%s %i (%s)" % (docid, m.percent, ' '.join(tags))
                continue

            if oformat == 'full':
                fullpath = doc_get_full_path(m.document, xdir)[0]
                data = parse_omega_data(m.document.get_data())
                print "id:%s %i %s (%s) \"%s\"" % (docid, m.percent, fullpath, ' '.join(tags), data)
                continue

    ########################################
    elif cmd == 'tag':
        add_tags = []
        remove_tags = []
        argc = 2
        for arg in sys.argv[argc:]:
            if arg == '--':
                argc += 1
                continue
            if arg[0] == '+':
                add_tags.append(arg[1:])
            elif arg[0] == '-':
                remove_tags.append(arg[1:])
            else:
                break
            argc += 1

        searchterms = sys.argv[argc:]

        xapers = Xapers(xdir, writable=True)

        matches = xapers.search(searchterms)

        prefix = find_prefix('tag')

        for m in matches:
            for tag in add_tags:
                try:
                    m.document.add_term(prefix+tag)
                except:
                    pass
            for tag in remove_tags:
                try:
                    m.document.remove_term(prefix+tag)
                except:
                    pass
            xapers.xapian_db.replace_document(m.docid, m.document)

    ########################################
    elif cmd == 'see':
        searchterms = sys.argv[2:]

        xapers = Xapers(xdir, writable=False)

        matches = xapers.search(searchterms)

        from subprocess import call
        for m in matches:
            path = doc_get_full_path(m.document, xdir)[0]
            sts = call(' '.join(["see", path]), shell=True)
            sys.exit()

    ########################################
    elif cmd == 'count':
        searchterms = sys.argv[2:]

        xapers = Xapers(xdir, writable=False)

        # count = 0 to retrieve all entries
        matches = xapers.search(searchterms, count=0)

	count = matches.get_matches_estimated();

        print count

    ########################################
    elif cmd == 'dump':
        searchterms = sys.argv[2:]
        if not searchterms:
            searchterms = '*'

        xapers = Xapers(xdir, writable=False)

        matches = xapers.search(searchterms)

        for m in matches:
            docid = doc_get_docid(m.document)
            tags = doc_get_terms(m.document, find_prefix('tag'))
            print "%s (%s)" % (docid, ' '.join(tags))

    ########################################
    elif cmd == 'help':
        usage()
        sys.exit(0)

    ########################################
    else:
        print >>sys.stderr, "unknown sub cmd", cmd
        usage()
        sys.exit(1)
