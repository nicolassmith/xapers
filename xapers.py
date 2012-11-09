#!/usr/bin/env python

import os
import sys
import xapers

########################################################################

# combine a list of terms with spaces between, so that simple queries
# don't have to be quoted at the shell level.
def make_query_string(terms):
    return str.join(' ', terms)

########################################################################

def usage():
    prog = os.path.basename(sys.argv[0])
    print "Usage:", prog, "<command> [args...]"
    print """
  add [options]                               add new document
    --source=source                             specify source
    --file=file                                 file to index
    --tags=tag[,...]                            initial tags
    --prompt                                    prompt for unspecified options
    --view                                      view entry after adding
  update [options] docid                      update document
    --source=source                             specify source
    --file=file                                 file to index
  delete docid                                delete document from database

  tag +tag|-tab [...] [--] search-terms...    add/remove tags

  search [options] search-terms...            search the database
    --output=[files|summary|bibtex|sources|tags] output format
    --limit=N                                    limit number returned (20)
  bibtex search-terms...                      search --output=bibtex
  view search-terms...                        view search in selector UI
  count search-terms...                       count matches

  export dir search-terms...                  export documents to a directory,
                                              docs named based on contents

  source2bib source                           retrieve bibtex for source

  version
  help                                        this help

sources: sources can be either urls, or 'source:id' strings, or bibtex files.
search-terms: terms to search for, included prefixed terms:
  id:        document id
  source:    source type
  bib:       bibtex db entry key
  author:    author string
  title:     title string
  tag:       user tags
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
    if cmd in ['add','a']:
        tags = None
        infile = None
        source = None
        prompt = False
        view = False

        argc = 2
        while True:
            if argc >= len(sys.argv):
                break
            elif '--source=' in sys.argv[argc]:
                source = sys.argv[argc].split('=',1)[1]
            elif '--file=' in sys.argv[argc]:
                infile = sys.argv[argc].split('=',1)[1]
            elif '--tags=' in sys.argv[argc]:
                tags = sys.argv[argc].split('=',1)[1].split(',')
            elif '--prompt' in sys.argv[argc]:
                prompt = True
            elif '--view' in sys.argv[argc]:
                view = True
            else:
                break
            argc += 1

        docid = cli.add(None, infile=infile, source=source, tags=tags, prompt=prompt)
        if view and docid:
            xapers.selector.UI(xdir, 'search', 'id:'+docid)

    ########################################
    elif cmd in ['update','u']:
        infile = None
        source = None

        argc = 2
        while True:
            if argc >= len(sys.argv):
                break
            elif '--source=' in sys.argv[argc]:
                source = sys.argv[argc].split('=',1)[1]
            elif '--file=' in sys.argv[argc]:
                infile = sys.argv[argc].split('=',1)[1]
            else:
                break
            argc += 1

        docid = sys.argv[argc]

        cli.add(docid, infile=infile, source=source)

    ########################################
    elif cmd == 'update-all':
        cli.update_all()

    ########################################
    elif cmd == 'delete':
        cli.delete(make_query_string(sys.argv[2:]))

    ########################################
    elif cmd == 'new':
        print >>sys.stderr, "not implemented."

    ########################################
    elif cmd in ['search','s']:
        if len(sys.argv) < 3:
            print >>sys.stderr, "Must specify a search term."
            sys.exit()

        oformat = 'simple'
        limit = 20

        argc = 2
        while True:
            if '--output=' in sys.argv[argc]:
                oformat = sys.argv[argc].split('=')[1]
            elif '--limit=' in sys.argv[argc]:
                limit = int(sys.argv[argc].split('=')[1])
            else:
                break
            argc += 1

        query = make_query_string(sys.argv[argc:])
        try:
            cli.search(query, oformat=oformat, limit=limit)
        except KeyboardInterrupt:
            sys.exit()

    ########################################
    elif cmd in ['bibtex','bib','b']:
        if len(sys.argv) < 3:
            print >>sys.stderr, "Must specify a search term."
            sys.exit()

        argc = 2
        query = make_query_string(sys.argv[argc:])
        try:
            cli.search(query, oformat='bibtex')
        except KeyboardInterrupt:
            sys.exit()

    ########################################
    elif cmd in ['select','view','v','show']:
        query = make_query_string(sys.argv[2:])
        if not query or query == '':
            query = 'tag:inbox'
        try:
            xapers.selector.UI(xdir, 'search', query)
        except KeyboardInterrupt:
            sys.exit()

    ########################################
    elif cmd in ['tag','t']:
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
    elif cmd == 'dumpterms':
        query = make_query_string(sys.argv[2:])
        cli.dumpterms(query)

    ########################################
    elif cmd == 'count':
        query = make_query_string(sys.argv[2:])
        cli.count(query)

    ########################################
    elif cmd == 'export':
        outdir = sys.argv[2]
        query = make_query_string(sys.argv[3:])
        cli.export(outdir, query)

    ########################################
    elif cmd in ['source2bib','s2b']:
        string = sys.argv[2]
        import xapers.source
        bibtex = xapers.source.fetch_bibtex(string)
        try:
            print xapers.bibtex.Bibentry(bibtex).as_string()
        except:
            print >>sys.stderr, "Problem parsing bibtex.  Outputting raw bibtex..."
            print bibtex

    ########################################
    elif cmd == 'version':
        print "Ha!"

    ########################################
    elif cmd in ['help','h']:
        usage()
        sys.exit(0)

    ########################################
    else:
        print >>sys.stderr, "unknown sub command '%s'." % cmd
        usage()
        sys.exit(1)
