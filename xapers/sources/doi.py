import io
import sys
import urllib2
import xapers.bibtex as bibparse

class Source():
    source = 'doi'
    netloc = 'dx.doi.org'
    #scan_regex = '[doi|DOI][\s\.\:]{0,2}(10\.\d{4}[\d\:\.\-\/a-z]+)[A-Z\s]'
    #scan_regex = '\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])[[:graph:]])+)\b'
    #scan_regex = '(doi|DOI)(10[.][0-9]{4,}(?:[.][0-9]+)*[\/\.](?:(?!["&\'<>])[[:graph:]])+)'
    scan_regex = '(?:doi|DOI)[\s\.\:]{0,2}(10\.\d{4,}[\/\.][\w\d\:\.\-]+)'

    def __init__(self, sid=None):
        self.sid = sid

    def gen_url(self):
        return 'http://%s/%s' % (self.netloc, self.sid)

    def parse_url(self, parsedurl):
        loc = parsedurl.netloc
        path = parsedurl.path
        if loc.find(self.netloc) >= 0:
            self.sid = path.strip('/')

    def _get_bib_file(self):
        f = open(self.file, 'r')
        bibtex = f.read()
        f.close
        return bibtex

    def _clean_bibtex_key(self, bibtex):
        # FIXME: there must be a better way of doing this
        stream = io.StringIO()
        i = True
        for c in bibtex:
            if c == ',':
                i = False
            if i and c == ' ':
                c = u'_'
            else:
                c = unicode(c)
            stream.write(c)
        bibtex = stream.getvalue()
        stream.close()
        return bibtex

    def _get_bib_doi(self):
        # http://www.crossref.org/CrossTech/2011/11/turning_dois_into_formatted_ci.html
        url = self.gen_url()
        headers = dict(Accept='text/bibliography; style=bibtex')
        req = urllib2.Request(url, headers=headers)
        f = urllib2.urlopen(req)
        bibtex = f.read()
        f.close
        # FIXME: this is a doi hack
        return self._clean_bibtex_key(bibtex), url

    def _get_bib_doi_json(self):
        # http://www.crossref.org/CrossTech/2011/11/turning_dois_into_formatted_ci.html
        url = self.gen_url()
        headers = dict(Accept='application/citeproc+json')
        req = urllib2.Request(url, headers=headers)
        f = urllib2.urlopen(req)
        json = f.read()
        f.close
        key = '%s:%s' % (self.source, self.sid)
        bibentry = bibparse.json2bib(json, key)
        return bibentry.as_string(), url

    def _get_bib_ads(self):
        req = 'http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=' + self.sid + '&data_type=BIBTEXPLUS'
        f = urllib2.urlopen(req)
        bibtex = f.read()
        f.close
        return bibtex, req

    def get_bibtex(self):
        if 'file' in dir(self):
            bibtex = self._get_bib_file()
            url = None
        else:
            bibtex, url = self._get_bib_doi_json()
        return bibtex, url
