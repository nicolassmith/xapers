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
            url = self.gen_url()
            headers = dict(Accept='text/bibliography; style=bibtex')
            req = urllib2.Request(url, headers=headers)
            f = urllib2.urlopen(req)
        bibtex = f.read()
        f.close

        return bibtex
