name = 'ads'

def parse_url(parsedurl):
    sid = None
    loc = parsedurl.netloc
    path = parsedurl.path
    if loc.find('dx.doi.org') < 0:
        return None
    sid = path.strip('/')
    return sid

def get_data(sid, lfile=None):
    # uri = 'http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode='
    # end = '&data_type=BIBTEX&db_key=AST%26nocookieset=1'

    # url = uri + bibcode + end
    # bib = urllib2.urlopen(url).readlines()
    #         # remove empty lines and query info
    # self.bibtex = ''.join(bib[5:-1])
    pass
