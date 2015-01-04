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

Copyright 2012, 2013
Jameson Rollins <jrollins@finestructure.net>
"""

import os
import sys
import sets
import shutil
import readline

import database
from documents import Document
from source import Sources, SourceError
from parser import ParseError
from bibtex import Bibtex, BibtexError

############################################################

def initdb(writable=False, create=False, force=False):
    xroot = os.getenv('XAPERS_ROOT',
                      os.path.expanduser(os.path.join('~','.xapers','docs')))
    try:
        return database.Database(xroot, writable=writable, create=create, force=force)
    except database.DatabaseUninitializedError as e:
        print >>sys.stderr, e
        print >>sys.stderr, "Import a document to initialize."
        sys.exit(1)
    except database.DatabaseInitializationError as e:
        print >>sys.stderr, e
        print >>sys.stderr, "Either clear the directory and add new files, or use 'retore' to restore from existing data."
        sys.exit(1)
    except database.DatabaseError as e:
        print >>sys.stderr, e
        sys.exit(1)

############################################################

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

def prompt_for_file(infile):
    if infile:
        print >>sys.stderr, 'file: %s' % infile
    else:
        readline.set_startup_hook()
        readline.parse_and_bind('')
        readline.set_completer()
        infile = raw_input('file: ')
        if infile == '':
            infile = None
    return infile

def prompt_for_source(db, sources):
    if sources:
        readline.set_startup_hook(lambda: readline.insert_text(sources[0]))
    elif db:
        sources = db.get_terms('source')
    readline.parse_and_bind("tab: complete")
    completer = Completer(sources)
    readline.set_completer(completer.terms)
    readline.set_completer_delims(' ')
    source = raw_input('source: ')
    if source == '':
        source = None
    return source

def prompt_for_tags(db, tags):
    # always prompt for tags, and append to initial
    if tags:
        print >>sys.stderr, 'initial tags: %s' % ' '.join(tags)
    else:
        tags = []
    if db:
        itags = db.get_terms('tag')
    else:
        itags = None
    readline.set_startup_hook()
    readline.parse_and_bind("tab: complete")
    completer = Completer(itags)
    readline.set_completer(completer.terms)
    readline.set_completer_delims(' ')
    while True:
        tag = raw_input('tag: ')
        if tag and tag != '':
            tags.append(tag.strip())
        else:
            break
    return tags

############################################################

def print_doc_summary(doc):
    docid = doc.get_docid()
    title = doc.get_title()
    if not title:
        title = ''
    tags = doc.get_tags()
    sources = doc.get_sids()
    keys = doc.get_keys()

    print "id:%s [%s] {%s} (%s) \"%s\"" % (
        docid,
        ' '.join(sources),
        ' '.join(keys),
        ' '.join(tags),
        title,
    )

############################################################

def add(db, query_string, infile=None, sid=None, tags=None, prompt=False):

    doc = None
    bibtex = None

    sources = Sources()
    doc_sid = sid
    source = None
    file_data = None

    if infile and infile is not True:
        infile = os.path.expanduser(infile)

    ##################################
    # if query provided, find single doc to update

    if query_string:
        if db.count(query_string) != 1:
            print >>sys.stderr, "Search '%s' did not match a single document." % query_string
            print >>sys.stderr, "Aborting."
            sys.exit(1)

        for doc in db.search(query_string):
            break

    ##################################
    # do fancy option prompting

    if prompt:
        doc_sids = []
        if doc_sid:
            doc_sids = [doc_sid]
        # scan the file for source info
        if infile is not True:
            infile = prompt_for_file(infile)

            print >>sys.stderr, "Scanning document for source identifiers..."
            try:
                ss = sources.scan_file(infile)
            except ParseError as e:
                print >>sys.stderr, "\n"
                print >>sys.stderr, "Parse error: %s" % e
                sys.exit(1)
            if len(ss) == 0:
                print >>sys.stderr, "0 source ids found."
            else:
                if len(ss) == 1:
                    print >>sys.stderr, "1 source id found:"
                else:
                    print >>sys.stderr, "%d source ids found:" % (len(ss))
                for sid in ss:
                    print >>sys.stderr, "  %s" % (sid)
                doc_sids += [s.sid for s in ss]
        doc_sid = prompt_for_source(db, doc_sids)
        tags = prompt_for_tags(db, tags)

    if not query_string and not infile and not doc_sid:
        print >>sys.stderr, "Must specify file or source to import, or query to update existing document."
        sys.exit(1)

    ##################################
    # process source and get bibtex

    # check if source is a file, in which case interpret it as bibtex
    if doc_sid and os.path.exists(doc_sid):
        bibtex = doc_sid

    elif doc_sid:
        # get source object for sid string
        try:
            source = sources.match_source(doc_sid)
        except SourceError as e:
            print >>sys.stderr, e
            sys.exit(1)

        # check that the source doesn't match an existing doc
        sdoc = db.doc_for_source(source.sid)
        if sdoc:
            if doc and sdoc != doc:
                print >>sys.stderr, "A different document already exists for source '%s'." % (doc_sid)
                print >>sys.stderr, "Aborting."
                sys.exit(1)
            print >>sys.stderr, "Source '%s' found in database.  Updating existing document..." % (doc_sid)
            doc = sdoc

        try:
            print >>sys.stderr, "Retrieving bibtex...",
            bibtex = source.fetch_bibtex()
            print >>sys.stderr, "done."
        except SourceError as e:
            print >>sys.stderr, "\n"
            print >>sys.stderr, "Could not retrieve bibtex: %s" % e
            sys.exit(1)

        if infile is True:
            try:
                print >>sys.stderr, "Retrieving file...",
                file_name, file_data = source.fetch_file()
                print >>sys.stderr, "done."
            except SourceError as e:
                print >>sys.stderr, "\n"
                print >>sys.stderr, "Could not retrieve file: %s" % e
                sys.exit(1)

    elif infile is True:
        print >>sys.stderr, "Must specify source with retrieve file option."
        sys.exit(1)

    if infile and not file_data:
        with open(infile, 'r') as f:
            file_data = f.read()
        file_name = os.path.basename(infile)

    ##################################

    # if we still don't have a doc, create a new one
    if not doc:
        doc = Document(db)

    ##################################
    # add stuff to the doc

    if bibtex:
        try:
            print >>sys.stderr, "Adding bibtex...",
            doc.add_bibtex(bibtex)
            print >>sys.stderr, "done."
        except BibtexError as e:
            print >>sys.stderr, "\n"
            print >>sys.stderr, e
            print >>sys.stderr, "Bibtex must be a plain text file with a single bibtex entry."
            sys.exit(1)
        except:
            print >>sys.stderr, "\n"
            raise

    # add source sid if it hasn't been added yet
    if source and not doc.get_sids():
        doc.add_sid(source.sid)

    if infile:
        try:
            print >>sys.stderr, "Adding file...",
            doc.add_file_data(file_name, file_data)
            print >>sys.stderr, "done."
        except ParseError as e:
            print >>sys.stderr, "\n"
            print >>sys.stderr, "Parse error: %s" % e
            sys.exit(1)
        except:
            print >>sys.stderr, "\n"
            raise

    if tags:
        try:
            print >>sys.stderr, "Adding tags...",
            doc.add_tags(tags)
            print >>sys.stderr, "done."
        except:
            print >>sys.stderr, "\n"
            raise

    ##################################
    # sync the doc to db and disk

    try:
        print >>sys.stderr, "Syncing document...",
        doc.sync()
        print >>sys.stderr, "done.\n",
    except:
        print >>sys.stderr, "\n"
        raise

    print_doc_summary(doc)
    return doc.docid

############################################

def importbib(db, bibfile, tags=[], overwrite=False):
    errors = []

    sources = Sources()

    for entry in sorted(Bibtex(bibfile), key=lambda entry: entry.key):
        print >>sys.stderr, entry.key

        try:
            docs = []

            # check for doc with this bibkey
            bdoc = db.doc_for_bib(entry.key)
            if bdoc:
                docs.append(bdoc)

            # check for known sids
            for source in sources.scan_bibentry(entry):
                sdoc = db.doc_for_source(source.sid)
                # FIXME: why can't we match docs in list?
                if sdoc and sdoc.docid not in [doc.docid for doc in docs]:
                    docs.append(sdoc)

            if len(docs) == 0:
                doc = Document(db)
            elif len(docs) > 0:
                if len(docs) > 1:
                    print >>sys.stderr, "  Multiple distinct docs found for entry.  Using first found."
                doc = docs[0]
                print >>sys.stderr, "  Updating id:%s..." % (doc.docid)

            doc.add_bibentry(entry)

            filepath = entry.get_file()
            if filepath:
                print >>sys.stderr, "  Adding file: %s" % filepath
                doc.add_file(filepath)

            doc.add_tags(tags)

            doc.sync()

        except BibtexError as e:
            print >>sys.stderr, "  Error processing entry %s: %s" % (entry.key, e)
            print >>sys.stderr
            errors.append(entry.key)

    if errors:
        print >>sys.stderr
        print >>sys.stderr, "Failed to import %d" % (len(errors)),
        if len(errors) == 1:
            print >>sys.stderr, "entry",
        else:
            print >>sys.stderr, "entries",
        print >>sys.stderr, "from bibtex:"
        for error in errors:
            print >>sys.stderr, "  %s" % (error)
        sys.exit(1)
    else:
        sys.exit(0)

############################################

def search(db, query_string, oformat='summary', limit=None):
    if query_string == '*' and oformat in ['tags','sources','keys']:
        if oformat == 'tags':
            for tag in db.get_terms('tag'):
                print tag
        elif oformat == 'sources':
            for source in db.get_sids():
                print source
        elif oformat == 'keys':
            for key in db.get_terms('key'):
                print key
        return

    otags = set([])
    osources = set([])
    okeys = set([])

    for doc in db.search(query_string, limit=limit):
        if oformat in ['summary']:
            print_doc_summary(doc)
            continue

        elif oformat in ['file','files']:
            for path in doc.get_fullpaths():
                print "%s" % (path)
            continue

        elif oformat == 'bibtex':
            bibtex = doc.get_bibtex()
            if not bibtex:
                print >>sys.stderr, "No bibtex for doc id:%s." % doc.docid
            else:
                print bibtex
                print
            continue

        if oformat == 'tags':
            otags = otags | set(doc.get_tags())
        elif oformat == 'sources':
            osources = osources | set(doc.get_sids())
        elif oformat == 'keys':
            okeys = okeys | set(doc.get_keys())

    if oformat == 'tags':
        for tag in otags:
            print tag
    elif oformat == 'sources':
        for source in osources:
            print source
    elif oformat == 'keys':
        for key in okeys:
            print key

############################################

def export(db, outdir, query_string):
    try:
        os.makedirs(outdir)
    except:
        pass
    import pipes
    for doc in db.search(query_string):
        title = doc.get_title()
        origpaths = doc.get_fullpaths()
        nfiles = len(origpaths)
        for path in origpaths:
            if not title:
                name = os.path.basename(os.path.splitext(path)[0])
            else:
                name = '%s' % (title.replace(' ','_'))
            ind = 0
            if nfiles > 1:
                name += '.%s' % ind
                ind += 1
            name += '.pdf'
            outpath = os.path.join(outdir,name)
            print outpath
            shutil.copyfile(path, outpath.encode('utf-8'))
