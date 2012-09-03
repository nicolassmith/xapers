import sys

def source_from_url(url):
    source = None
    sid = None

    from urlparse import urlparse
    o = urlparse(url)
    # ParseResult(scheme='http', netloc='www.cwi.nl:80', path='/%7Eguido/Python.html',
    #             params='', query='', fragment='')
    
    import xapers.sources

    for ss in dir(xapers.sources):
        if '__' in ss:
            continue
        print >>sys.stderr, 'trying', ss, '...', 
        exec('import xapers.sources.' + ss + ' as smod')
        sid = smod.parse_url(o)
        if sid:
            source = ss
            print >>sys.stderr, 'match!'
            break
        else:
            smod = None
            print >>sys.stderr, ''

    if not smod:
        print >>sys.stderr, 'no matching source module found.'

    return smod, sid


def get_source(source):
    try:
        exec('import xapers.sources.' + ss + ' as smod')
        return smod
    except:
        return None
