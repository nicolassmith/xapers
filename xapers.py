#!/usr/bin/env python

import os
import sys
import xapers

########################################################################
# TODO:

# source fetch modules
#  - url parser
#  - bibtex fetch

# doc parser modules

# better atomic opening of database

# store bibtex in data
#   - want add_bibtex function, that parses the bibtex to add terms:
#     - author
#     - title
#     - pub date
#   - add ability to modify data for document
#   - dump file --> dump directories, in git!

########################################################################

# Combine a list of terms with spaces between, so that simple queries
# don't have to be quoted at the shell level.
def make_query_string(terms):
    return str.join(' ', terms)

########################################################################

def usage():
    prog = os.path.basename(sys.argv[0])
    print "Usage:", prog, "<command> [args...]"
    print """
  add [options] file                          add file to database
    --prompt
    --sources=source:sid[,...]
    --tags=tag[,...]
  search [options] <search-term>...           search the database
    --output=[simple|full|files|sources|tags]
    --limit=N
  tag +tag|-tab [...] [--] <search-term>...   add/remove tags
  set <attribute> <value> <docid>             set a document attribute with value
  show <search-term>...                       display first result
  count <search-term>...                      count matches
  dump [<search-terms>...]                    dump tags to stdout
  restore                                     restore dump file on stdin
  version
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

    cli = xapers.cli.UI(xdir)

    ########################################
    if cmd == 'add':
        if len(sys.argv) < 3:
            print >>sys.stderr, "Must specify a file to add."
            sys.exit()
        argc = 2

        prompt = False
        if '--prompt' in sys.argv[argc]:
            prompt = True
            argc += 1

        data = {}
        if '--sources=' in sys.argv[argc]:
            sss = sys.argv[argc].split('=',1)[1].split(',')
            data['sources'] = {}
            for ss in sss:
                s,i = ss.split(':')
                data['sources'][s] = i
            argc += 1
        if '--tags=' in sys.argv[argc]:
            data['tags'] = sys.argv[argc].split('=',1)[1].split(',')
            argc += 1
        infile = sys.argv[argc]

        cli.add(infile, data, prompt=prompt)

    ########################################
    elif cmd == 'delete':
        cli.delete(make_query_string(sys.argv[2:]))

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
        oformat = 'simple'
        limit = 20
        if '--output=' in sys.argv[argc]:
            oformat = sys.argv[argc].split('=')[1]
            argc += 1
        if '--limit=' in sys.argv[argc]:
            limit = int(sys.argv[argc].split('=')[1])
            argc += 1

        query = make_query_string(sys.argv[argc:])

        cli.search(query, limit=limit, oformat=oformat)

    ########################################
    elif cmd == 'select':
        query = make_query_string(sys.argv[2:])
        if not query or query == '':
            query = '*'

        xapers.selector.UI(xdir, query_string=query)

    ########################################
    elif cmd in ['view','show']:
        query = make_query_string(sys.argv[2:])

        cli.view(query)

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
        query = make_query_string(sys.argv[argc:])

        cli.tag(query, add_tags, remove_tags)

    ########################################
    elif cmd == 'set':
        attribute = sys.argv[2]
        value = sys.argv[3]
        query = make_query_string(sys.argv[4:])

        cli.set(query, attribute, value)

    ########################################
    elif cmd == 'dumpterms':
        query = make_query_string(sys.argv[2:])

        cli.dumpterms(query)

    ########################################
    elif cmd == 'count':
        query = make_query_string(sys.argv[2:])

        cli.count(query)

    ########################################
    elif cmd == 'dump':
        query = make_query_string(sys.argv[2:])
        if not query or query == '':
            query = '*'

        cli.dump(query)

    ########################################
    elif cmd == 'restore':
        cli.restore()

    ########################################
    elif cmd == 'version':
        print "Ha!"

    ########################################
    elif cmd == 'help':
        usage()
        sys.exit(0)

    ########################################
    else:
        print >>sys.stderr, "unknown sub cmd", cmd
        usage()
        sys.exit(1)
