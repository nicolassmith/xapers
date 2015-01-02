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

Copyright 2012-2014
Jameson Rollins <jrollins@finestructure.net>
"""

import os
import sys

from cli import UI, initdb
from source import Sources, SourceError
from bibtex import Bibtex, BibtexError
from parser import ParseError

########################################################################

# combine a list of terms with spaces between, so that simple queries
# don't have to be quoted at the shell level.
def make_query_string(terms, require=True):
    string = str.join(' ', terms)
    if string == '':
        if require:
            print >>sys.stderr, "Must specify a search term."
            sys.exit(1)
        else:
            string = '*'
    return string

def import_nci():
    try:
        import nci
    except ImportError:
        print >>sys.stderr, "The python-urwid package does not appear to be installed."
        print >>sys.stderr, "Please install to be able to use the curses UI."
        sys.exit(1)
    return nci

########################################################################

PROG = 'xapers'

def usage():
    print "Usage:", PROG, "<command> [args...]"
    print """
Commands:

  add [options] [<search-terms>]      Add a new document or update existing.
                                      If provided, search should match a single
                                      document.
    --source=[<sid>|<file>]             source id, for online retrieval, or
                                        bibtex file path
    --file=<file>                       PDF file to index and archive
    --tags=<tag>[,...]                  initial tags
    --prompt                            prompt for unspecified options
    --view                              view entry after adding
  import <bibtex-file>                Import entries from a bibtex database.
    --tags=<tag>[,...]                  tags to apply to all imported documents
  delete <search-terms>               Delete documents from database.
    --noprompt                          do not prompt to confirm deletion
  restore                             Restore database from xapers root.

  tag +<tag>|-<tag> [...] [--] <search-terms>
                                      Add/remove tags.

  search [options] <search-terms>     Search for documents.
    --output=[summary|bibtex|tags|sources|keys|files]
                                        output format (default is 'summary')
    --limit=N                           limit number of results returned
                                        (default is 20, use '0' for all)
  bibtex <search-terms>               Short for \"search --output=bibtex\".
  view <search-terms>                 View search in curses UI.
  count <search-terms>                Count matches.

  export <dir> <search-terms>         Export documents to a directory of files
                                      named for document titles.

  sources                             List available sources.
  source2url <sid> [...]              Output URLs for sources.
  source2bib <sid> [...]              Retrieve bibtex for sources and print to
                                      stdout.
  source2file <sid>                   Retrieve file for source and write to
                                      stdout.
  scandoc <file>                      Scan PDF file for source ids.

  version                             Print version number.
  help [search]                       This usage, or search term help.

The xapers document store is specified by the XAPERS_ROOT environment
variable, or defaults to '~/.xapers/docs' if not specified (the
directory is allowed to be a symlink).

See 'xapers help search' for more information on term definitions and
search syntax."""

def usage_search():
    print """Xapers supports a common syntax for search terms.

Search can consist of free-form text and quoted phrases.  Terms can be
combined with standard Boolean operators.  All terms are combined with
a logical OR by default.  Parentheses can be used to group operators,
but must be protect from shell interpretation.  The string '*' will
match all documents.

Additionally, the following prefixed terms are understood (where
<brackets> indicate user-supplied values):

  id:<docid>                   Xapers document id
  author:<string>              string in authors (also a:)
  title:<string>               string in title (also t:)
  tag:<tag>                    specific user tag
  <source>:<id>                specific source id (sid)
  source:<source>              specific Xapers source
  key:<key>                    specific bibtex citation key
  year:<year>                  specific publication year (also y:)
  year:<since>..<until>        publication year range (also y:)
  year:..<until>
  year:<since>..

Publication years must be four-digit integers.

See the following for more information on search terms:

  http://xapian.org/docs/queryparser.html"""

########################################################################

if __name__ == '__main__':

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = []

    xroot = os.getenv('XAPERS_ROOT',
                      os.path.expanduser(os.path.join('~','.xapers','docs')))

    ########################################
    if cmd in ['add','a']:
        cli = UI(xroot)

        tags = None
        infile = None
        sid = None
        prompt = False
        view = False
        query_string = None

        argc = 2
        while True:
            if argc >= len(sys.argv):
                break
            elif '--source=' in sys.argv[argc]:
                sid = sys.argv[argc].split('=',1)[1]
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

        if argc == (len(sys.argv) - 1):
            query_string = make_query_string(sys.argv[argc:])

        try:
            docid = cli.add(query_string, infile=infile, sid=sid, tags=tags, prompt=prompt)
        except KeyboardInterrupt:
            print >>sys.stderr, ''
            sys.exit(1)

        # dereference the cli object so that the database is flushed
        # FIXME: is there a better way to handle this?
        cli = None

        if view and docid:
            nci = import_nci()
            nci.UI(xroot, cmd=['search', 'id:'+docid])

    ########################################
    elif cmd in ['import','i']:
        cli = UI(xroot)

        tags = []

        argc = 2
        while True:
            if argc >= len(sys.argv):
                break
            elif '--tags=' in sys.argv[argc]:
                tags = sys.argv[argc].split('=',1)[1].split(',')
            elif '--overwrite' in sys.argv[argc]:
                overwrite = True
            else:
                break
            argc += 1

        try:
            bibfile = sys.argv[argc]
        except IndexError:
            print >>sys.stderr, "Must specify bibtex file to import."
            sys.exit(1)

        if not os.path.exists(bibfile):
            print >>sys.stderr, "File not found: %s" % bibfile
            sys.exit(1)

        try:
            cli.importbib(bibfile, tags=tags)
        except KeyboardInterrupt:
            print >>sys.stderr, ''
            sys.exit(1)

    ########################################
    elif cmd in ['update-all']:
        cli = UI(xroot)
        cli.update_all()

    ########################################
    elif cmd in ['delete']:
        prompt = True

        argc = 2
        while True:
            if argc >= len(sys.argv):
                break
            elif '--noprompt' in sys.argv[argc]:
                prompt = False
            else:
                break
            argc += 1

        cli = UI(xroot)
        try:
            cli.delete(make_query_string(sys.argv[argc:]), prompt=prompt)
        except KeyboardInterrupt:
            print >>sys.stderr, ''
            sys.exit(1)

    ########################################
    elif cmd in ['search','s']:
        cli = UI(xroot)

        oformat = 'summary'
        limit = 20

        argc = 2
        while True:
            if argc >= len(sys.argv):
                break
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
            print >>sys.stderr, ''
            sys.exit(1)

    ########################################
    elif cmd in ['bibtex','bib','b']:
        cli = UI(xroot)
        argc = 2
        query = make_query_string(sys.argv[argc:])
        try:
            cli.search(query, oformat='bibtex')
        except KeyboardInterrupt:
            print >>sys.stderr, ''
            sys.exit(1)

    ########################################
    elif cmd in ['nci','view','show','select']:
        nci = import_nci()

        if cmd == 'nci':
            args = sys.argv[2:]
        else:
            query = make_query_string(sys.argv[2:], require=False)
            args = ['search', query]

        try:
            nci.UI(xroot, cmd=args)
        except KeyboardInterrupt:
            print >>sys.stderr, ''
            sys.exit(1)

    ########################################
    elif cmd in ['tag','t']:
        cli = UI(xroot)

        add_tags = []
        remove_tags = []

        argc = 2
        for arg in sys.argv[argc:]:
            if argc >= len(sys.argv):
                break
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

        if not add_tags and not remove_tags:
            print >>sys.stderr, "Must specify tags to add or remove."
            sys.exit(1)

        if '' in add_tags:
            print >>sys.stderr, "Null tags not allowed."
            sys.exit(1)

        query = make_query_string(sys.argv[argc:])
        cli.tag(query, add_tags, remove_tags)

    ########################################
    elif cmd in ['dumpterms']:
        cli = UI(xroot)
        query = make_query_string(sys.argv[2:], require=False)
        cli.dumpterms(query)

    ########################################
    elif cmd in ['maxid']:
        db = initdb(xroot)
        docid = 0
        for doc in db.search('*'):
            docid = max(docid, int(doc.docid))
        print 'id:%d' % docid

    ########################################
    elif cmd in ['count']:
        cli = UI(xroot)
        query = make_query_string(sys.argv[2:], require=False)
        cli.count(query)

    ########################################
    elif cmd in ['export']:
        cli = UI(xroot)
        outdir = sys.argv[2]
        query = make_query_string(sys.argv[3:])
        cli.export(outdir, query)

    ########################################
    elif cmd in ['restore']:
        cli = UI(xroot)
        cli.restore()

    ########################################
    elif cmd in ['sources']:
        sources = Sources()
        w = 0
        for source in sources:
            w = max(len(source.name), w)
        format = '%'+str(w)+'s: %s[%s]'
        for source in sources:
            name = source.name
            desc = ''
            try:
                desc += '%s ' % source.description
            except AttributeError:
                pass
            try:
                desc += '(%s) ' % source.url
            except AttributeError:
                pass
            if source.is_builtin:
                path = 'builtin'
            else:
                path = source.path
            print format % (name, desc, path)

    ########################################
    elif cmd in ['source2bib', 's2b', 'source2url', 's2u', 'source2file', 's2f']:
        outraw = False

        argc = 2
        for arg in sys.argv[argc:]:
            if argc >= len(sys.argv):
                break
            elif sys.argv[argc] == '--raw':
                outraw = True
            else:
                break
            argc += 1

        try:
            sss = sys.argv[argc:]
        except IndexError:
            print >>sys.stderr, "Must specify source to retrieve."
            sys.exit(1)

        if cmd in ['source2file', 's2f']:
            if len(sss) > 1:
                print >>sys.stderr, "source2file can only retrieve file for single source."
                sys.exit(1)

        sources = Sources()

        for ss in sss:
            try:
                item = sources.match_source(ss)
            except SourceError as e:
                print >>sys.stderr, e
                sys.exit(1)

            if cmd in ['source2url', 's2u']:
                print item.url
                continue

            elif cmd in ['source2bib', 's2b']:
                try:
                    bibtex = item.fetch_bibtex()
                except SourceError as e:
                    print >>sys.stderr, "Could not retrieve bibtex: %s" % e
                    sys.exit(1)

                if outraw:
                    print bibtex
                else:
                    print Bibtex(bibtex)[0].as_string()

            elif cmd in ['source2file', 's2f']:
                try:
                    print item.fetch_file()
                except SourceError as e:
                    print >>sys.stderr, "Could not retrieve file: %s" % e
                    sys.exit(1)

    ########################################
    elif cmd in ['scandoc','sd']:
        try:
            infile = sys.argv[2]
        except IndexError:
            print >>sys.stderr, "Must specify document to scan."
            sys.exit(1)

        try:
            items = Sources().scan_file(infile)
        except ParseError as e:
            print >>sys.stderr, "Parse error: %s" % e
            print >>sys.stderr, "Is file '%s' a PDF?" % infile
            sys.exit(1)

        for item in items:
            print item

    ########################################
    elif cmd in ['version','--version','-v']:
        import version
        print 'xapers', version.__version__

    ########################################
    elif cmd in ['help','h','--help','-h']:
        if len(sys.argv) > 2:
            if sys.argv[2] == 'search':
                usage_search()
        else:
            usage()

    ########################################
    else:
        if cmd:
            print >>sys.stderr, "Unknown command '%s'." % cmd
        else:
            print >>sys.stderr, "Command not specified."
        print >>sys.stderr, "See \"help\" for more information."
        sys.exit(1)
