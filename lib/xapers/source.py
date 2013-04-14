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

    def __init__(self, id=None):
        self.id = id

    def get_sid(self):
        if self.id:
            return '%s:%s' % (self.source, self.id)

    def gen_url(self):
        """Return url string for source ID."""
        if self.netloc and self.id:
            return 'http://%s/%s' % (self.netloc, self.id)

    def match(self, netloc, path):
        """Return True if netloc/path belongs to this source and a sid can be determined."""

    def get_bibtex(self):
        """Download source bibtex, and return as string."""

##################################################

def list_sources():
    """List all available source modules."""
    sources = []
    for s in dir(xapers.sources):
        # skip the __init__ file when finding sources
        if '__' in s:
            continue
        sources.append(s)
    return sources

def _load_source(source):
    try:
        mod = __import__('xapers.sources.' + source, fromlist=['Source'])
        return getattr(mod, 'Source')
    except ImportError:
        raise SourceError("Unknown source '%s'." % source)

def get_source(string):
    """Return Source class object for URL or source identifier string. """
    smod = None

    o = urlparse(string)

    # if the scheme is http, look for source match
    if o.scheme in ['http', 'https']:
        for source in list_sources():
            smod = _load_source(source)()
            # if matches, id will be set
            if smod.match(o.netloc, o.path):
                break
            else:
                smod = None
        if not smod:
            raise SourceError('URL matches no known source.')

    elif o.scheme == '':
        source = o.path
        smod = _load_source(source)()

    else:
        source = o.scheme
        oid = o.path
        smod = _load_source(source)(oid)

    return smod

def scan_for_sources(file):
    """Scan document file and return a list of source strings found
    therein."""
    from .parsers import pdf as parser
    text = parser.parse_file(file)
    sources = []
    for source in list_sources():
        smod = _load_source(source)()
        if 'scan_regex' not in dir(smod):
            continue
        prog = re.compile(smod.scan_regex)
        matches = prog.findall(text)
        if matches:
            for match in matches:
                sources.append('%s:%s' % (smod.source.lower(), match))
    return sources
