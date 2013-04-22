import io
import urllib2
from xapers.bibtex import json2bib

class Source():
    source = 'doi'
    netloc = 'dx.doi.org'
    #scan_regex = '[doi|DOI][\s\.\:]{0,2}(10\.\d{4}[\d\:\.\-\/a-z]+)[A-Z\s]'
    #scan_regex = '\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])[[:graph:]])+)\b'
    #scan_regex = '(doi|DOI)(10[.][0-9]{4,}(?:[.][0-9]+)*[\/\.](?:(?!["&\'<>])[[:graph:]])+)'
    scan_regex = '(?:doi|DOI)[\s\.\:]{0,2}(10\.\d{4,}[\w\d\:\.\-\/]+)'

    def __init__(self, id=None):
        self.id = id

    def get_sid(self):
        if self.id:
            return '%s:%s' % (self.source, self.id)

    def gen_url(self):
        if self.id:
            return 'http://%s/%s' % (self.netloc, self.id)

    def match(self, netloc, path):
        if netloc.find(self.netloc) >= 0:
            self.id = path.strip('/')
            return True
        else:
            return False

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
        return self._clean_bibtex_key(bibtex)

    def _get_bib_doi_json(self):
        # http://www.crossref.org/CrossTech/2011/11/turning_dois_into_formatted_ci.html
        url = self.gen_url()
        headers = dict(Accept='application/citeproc+json')
        req = urllib2.Request(url, headers=headers)
        f = urllib2.urlopen(req)
        json = f.read()
        f.close
        bibentry = json2bib(json, self.get_sid())
        return bibentry.as_string()

    def _get_bib_ads(self):
        req = 'http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=' + self.sid + '&data_type=BIBTEXPLUS'
        f = urllib2.urlopen(req)
        bibtex = f.read()
        f.close
        return bibtex

    def get_bibtex(self):
        return self._get_bib_doi_json()
