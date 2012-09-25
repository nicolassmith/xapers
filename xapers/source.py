import os
import sys
from urlparse import urlparse

import xapers.sources

def list_sources():
    sources = []
    return ['doi']
    for s in dir(xapers.sources):
        # skip the __init__ file when finding sources
        if '__' in s:
            continue
        sources.append(s)
    return sources

def source_from_url(url):
    source = None
    sid = None

    if os.path.exists(url):
        name = os.path.basename(url)

    # ParseResult(scheme='http', netloc='www.cwi.nl:80', path='/%7Eguido/Python.html',
    #             params='', query='', fragment='')
    
    for ss in list_sources():
        print >>sys.stderr, 'trying', ss, '...', 
        #exec('import xapers.sources.' + ss + ' as smod')
        exec('from xapers.sources.' + ss + ' import Source')

        smod = Source()

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

    if not smod:
        print >>sys.stderr, 'no matching source module found.'

    return smod


def get_source(source):
    try:
        exec('import xapers.sources.' + ss + ' as smod')
        return smod
    except:
        return None
