#!/usr/bin/env python

import os
import sys
import xapers

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

# query user for document metadata
def query_metadata(db):
    import readline

    url = None
    source = None
    sid = None
    tags = None

    while True:
        if url:
            readline.set_startup_hook(lambda: readline.insert_text(url))
        url = raw_input('url: ')
        
        readline.parse_and_bind("tab: complete")
        if source:
            readline.set_startup_hook(lambda: readline.insert_text(source))
        completer = Completer(db.get_all_sources())
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
        completer = Completer(db.get_all_tags())
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
        ret = raw_input("'r' to reenter, return to accept, C-c to cancel: ")
        if ret is not 'r':
            break

    sources = {source: sid}
    return url, sources, tags


########################################################################

def usage():
    prog = os.path.basename(sys.argv[0])
    print "Usage:", prog, "<command> [args...]"
    print """
  add [options] file                          add file to database
    --sources=source:sid[,...]
    --tags=tag[,...]
  search [options] <search-term>...           search the database
    --output=[full|simple|file]
  tag +tag|-tab [...] [--] <search-term>...   add/remove tags
  view <search-term>...                       display first result
  count <search-term>...                      count matches
  dump [<search-terms>...]                    dump tags to stdout
  restore                                     restore dump file on stdin
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

    ui = xapers.UI(xdir)

    ########################################
    if cmd == 'import':
        ui.import_file(sys.argv[2])
        
    ########################################
    elif cmd == 'add':
        if len(sys.argv) < 3:
            print >>sys.stderr, "Must specify a file to add."
            sys.exit()
        argc = 2
        sources = None
        if '--sources=' in sys.argv[argc]:
            sss = sys.argv[argc].split('=',1)[1].split(',')
            sources = {}
            for ss in sss:
                s,i = ss.split(':')
                sources[s] = i
            argc += 1
        tags = None
        if '--tags=' in sys.argv[argc]:
            tags = sys.argv[argc].split('=',1)[1].split(',')
            argc += 1
        url = None
        if '--url=' in sys.argv[argc]:
            url = sys.argv[argc].split('=',1)[1]
            argc += 1
        infile = sys.argv[argc]

        ui.add(infile, url=url, sources=sources, tags=tags)

    ########################################
    elif cmd == 'new':
        # try:
        #     os.makedirs(xdb)
        # except:
        #     pass
        # omindex = [
        #     '~/src/xapian/xapian/xapian-applications/omega/omindex',
        #     '--verbose',
	#     '--follow',
	#     '--db', xdb,
        #     '--url', '/',
        #     ]
        # for arg in sys.argv[2:]:
        #     omindex.append(arg)
        # omindex.append(xdir)
        # from subprocess import Popen, PIPE
        # print ' '.join(omindex)
        # p = Popen(' '.join(omindex), shell=True)
        # if p.wait() != 0:
        #     print >>sys.stderr, "There were some errors"
        print >>sys.stderr, "not implemented."

    ########################################
    elif cmd == 'search':
        if len(sys.argv) < 3:
            print >>sys.stderr, "Must specify a search term."
            sys.exit()
        argc = 2
        oformat = 'full'
        if '--output=' in sys.argv[argc]:
            oformat = sys.argv[argc].split('=')[1]
            argc += 1
        searchterms = sys.argv[argc:]

        ui.search(searchterms, oformat=oformat)

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

        ui.tag(searchterms, add_tags, remove_tags)

    ########################################
    elif cmd == 'view':
        searchterms = sys.argv[2:]

        ui.view(searchterms)

    ########################################
    elif cmd == 'count':
        searchterms = sys.argv[2:]

        ui.count(searchterms)

    ########################################
    elif cmd == 'sync':
        # searchterms = sys.argv[2:]
        # if not searchterms:
        #     searchterms = '*'
        
        # xapers = Xapers(xdir, writable=False)

        # matches = xapers.search(searchterms)

        # for m in matches:
        #     docid = doc_get_docid(m.document)
        #     tags = doc_get_terms(m.document, find_prefix('tag'))
        #     docdir = os.path.join(xdir,docname)
        #     f = open(sys.argv[3], 'rb')
        #     print "%s (%s)" % (docid, ' '.join(tags))
        print >>sys.stderr, "not implemented."

    ########################################
    elif cmd == 'dump':
        # searchterms = sys.argv[2:]
        # if not searchterms:
        #     searchterms = '*'

        # xapers = Xapers(xdir, writable=False)

        # matches = xapers.search(searchterms)

        # for m in matches:
        #     docid = doc_get_docid(m.document)
        #     tags = doc_get_terms(m.document, find_prefix('tag'))
        #     print "%s (%s)" % (docid, ' '.join(tags))
        print >>sys.stderr, "not implemented."

    ########################################
    elif cmd == 'restore':
        # xapers = Xapers(xdir, writable=True)

        # import re
        # regex = re.compile("^([^ ]+) \\(([^)]*)\\)$")
        # for line in sys.stdin:
        #     m = regex.match(line)
        #     if not m:
        #         continue
        #     docid = m.group(1)
        #     tags = m.group(2)

        #     print m.groups()
        #     continue

        #     doc = xapers.get_doc(docid)
        #     doc.set_terms(tags)
        #     xapers.xapian_db.replace_document(docid, doc)
        print >>sys.stderr, "not implemented."

    ########################################
    elif cmd == 'help':
        usage()
        sys.exit(0)

    ########################################
    else:
        print >>sys.stderr, "unknown sub cmd", cmd
        usage()
        sys.exit(1)
