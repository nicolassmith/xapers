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
        return Source(sid)
    except:
        return None

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

def source_from_url(url):
    source = None
    sid = None

    if os.path.exists(url):
        name = os.path.basename(url)
    
    for ss in list_sources():
        print >>sys.stderr, 'trying %s...' % ss,

        smod = get_source(ss)

        if os.path.exists(url):
            base, ext = os.path.splitext(os.path.basename(url))
            if base == ss:
                smod.sid = '1234'
                smod.file = url
        else:
            o = urlparse(url)
            smod.parse_url(o)

        if smod.sid:
            print >>sys.stderr, 'match!'
            break
        else:
            smod = None
            print >>sys.stderr, ''

    return smod

def source_from_string(string):
    o = urlparse(string)
    if o.scheme in ['http', 'https']:
        source = source_from_url(string)
    else:
        source = get_source(o.scheme, o.path)
    return source

def fetch_bibtex(string):
    source = source_from_string(string)
    return source.get_bibtex()
