import sys
import urllib2

class Source():
    source = 'doi'
    netloc = 'dx.doi.org'

    def __init__(self, sid=None):
        self.sid = sid

    def gen_url(self):
        return 'http://%s/%s' % (self.netloc, self.sid)

    def parse_url(self, parsedurl):
        loc = parsedurl.netloc
        path = parsedurl.path
        if loc.find(self.netloc) >= 0:
            self.sid = path.strip('/')

    def get_bibtex(self):
        if 'file' in dir(self):
            f = open(self.file, 'r')
        else:
            # FIXME: dx.doi.org returns bad bibtex keys for long author lists!
            # url = self.gen_url()
            # headers = dict(Accept='text/bibliography; style=bibtex')
            # req = urllib2.Request(url, headers=headers)

            req = 'http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=' + self.sid + '&data_type=BIBTEXPLUS'
            #print >>sys.stderr, req

            f = urllib2.urlopen(req)
        bibtex = f.read()
        f.close

        # need to take care of broken bibtex entry key from DOI for
        # entries with 'et al' author lists
        #import re
        #re.compile('^.*{.*et al.*,')
        #bibtex = bibtex.replace('et al.', 'et_al.', 1)

        return bibtex
