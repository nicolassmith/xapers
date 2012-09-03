name = 'doi'
urlbase = 'dx.doi.org'

def parse_url(parsedurl):
    sid = None
    loc = parsedurl.netloc
    path = parsedurl.path
    if loc.find(urlbase) < 0:
        return None
    sid = path.strip('/')
    return sid

def get_data(sid, lfile=None):
    import urllib2

    if lfile:
        f = open(lfile, 'r')
    else:
        url = 'http://' + urlbase + '/' + sid
        headers = dict(Accept='text/bibliography; style=bibtex')
        req = urllib2.Request(url, headers=headers)
        f = urllib2.urlopen(req)
    bibtex = f.read()
    f.close

    import xapers.bibtex
    bdata = xapers.bibtex.parse(bibtex)

    data = {
        'title':   bdata['title'],
        'authors': bdata['authors'],
        'year':    bdata['year'],
        'bibtex':  bibtex,
        }

    return data
