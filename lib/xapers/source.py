import os
import sys
import re
from urlparse import urlparse

import xapers.sources
import xapers.bibtex

##################################################

class SourceError(Exception):
    """Base class for Xapers source exceptions."""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

##################################################

class Source():
    source = None
    netloc = None
    scan_regex = None

    def __init__(self, sid=None):
        self.sid = sid

    def gen_url(self):
        """Return url string for source ID."""
        if self.netloc and self.sid:
            return 'http://%s/%s' % (self.netloc, self.sid)

    def match(self, netloc, path):
        """Return True if netloc/path belongs to this source and a sid can be determined."""

    def get_bibtex(self):
        """Download source bibtex, and return as string."""

##################################################

def list_sources():
    sources = []
    for s in dir(xapers.sources):
        # skip the __init__ file when finding sources
        if '__' in s:
            continue
        sources.append(s)
    return sources


def get_source(source, sid=None):
    try:
        exec('from xapers.sources.' + source + ' import Source')
    except ImportError:
        raise SourceError("Unknown source '%s'." % source)
    return Source(sid)


def scan_for_sources(file):
    from .parsers import pdf as parser
    text = parser.parse_file(file)
    sources = []
    for ss in list_sources():
        smod = get_source(ss)
        if 'scan_regex' not in dir(smod):
            continue
        prog = re.compile(smod.scan_regex)
        matches = prog.findall(text)
        if matches:
            for match in matches:
                #sources.append((smod.source, match))
                # FIXME: this should be a set
                sources.append('%s:%s' % (smod.source.lower(), match))
    return sources


def source_from_string(string, log=False):
    """Return Source class for string identifier.  A SourceError is
    raised in case string can not be parsed into a known source."""

    o = urlparse(string)

    # if the scheme is http, look for source match
    if o.scheme in ['http', 'https']:
        if log:
            print >>sys.stderr, 'Matching source from URL:'

        for ss in list_sources():
            if log:
                print >>sys.stderr, ' trying %s...' % ss,

            source = get_source(ss)

            if source.match(o.netloc, o.path):
                if log:
                    print >>sys.stderr, 'match!'
                break
            else:
                if log:
                    print >>sys.stderr, ''
                source = None

        if not source:
            raise SourceError('URL matches no known source.')

    # otherwise, assume scheme is source
    else:
        source = get_source(o.scheme, o.path)

    if log:
        print >>sys.stderr, "Source: %s:%s" % (source.source, source.sid)
        print >>sys.stderr, "URL: %s" % (source.gen_url())

    return source

def fetch_bibtex(string):
    source = source_from_string(string)
    return source.get_bibtex()
