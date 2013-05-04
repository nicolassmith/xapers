import sys
import pycurl
import cStringIO
import tempfile
from xapers.bibtex import data2bib

def dccRetrieveXML(docid):
    url = 'https://dcc.ligo.org/Shibboleth.sso/Login?target=https%3A%2F%2Fdcc.ligo.org%2Fcgi-bin%2Fprivate%2FDocDB%2FShowDocument?docid=' + docid + '%26outformat=xml&entityID=https%3A%2F%2Flogin.ligo.org%2Fidp%2Fshibboleth'

    curl = pycurl.Curl()
    cookies = tempfile.NamedTemporaryFile()

    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.UNRESTRICTED_AUTH, 1)
    curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_GSSNEGOTIATE)
    curl.setopt(pycurl.COOKIEJAR, cookies.name)
    curl.setopt(pycurl.USERPWD, ':')
    curl.setopt(pycurl.FOLLOWLOCATION, 1)

    doc = cStringIO.StringIO()
    curl.setopt(pycurl.WRITEFUNCTION, doc.write)
    try:
        curl.perform()
    except:
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()

    xml = doc.getvalue()

    curl.close()
    cookies.close()
    doc.close()

    return xml

def dccXMLExtract(xmlstring):
    from xml.dom.minidom import parse, parseString
    xml = parseString(xmlstring)
    etitle = xml.getElementsByTagName("title")[0].firstChild
    if etitle:
        title = etitle.data
    else:
        title = None
    alist = xml.getElementsByTagName("author")
    authors = []
    for author in alist:
        authors.append(author.getElementsByTagName("fullname")[0].firstChild.data)
    eabstract = xml.getElementsByTagName("abstract")[0].firstChild
    if eabstract:
        abstract = eabstract.data
    else:
        abstract = None
    # FIXME: find year/date
    year = None
    return title, authors, year, abstract


class Source():
    source = 'dcc'
    netloc = 'dcc.ligo.org'

    def __init__(self, id=None):
        self.id = id

    def get_sid(self):
        if self.id:
            return '%s:%s' % (self.source, self.id)

    def gen_url(self):
        if self.id:
            return 'http://%s/%s' % (self.netloc, self.id)

    def match(self, netloc, path):
        if netloc != self.netloc:
            return False
        fullid = path.split('/')[1]
        dccid, vers = fullid.replace('LIGO-', '').split('-')
        self.id = dccid
        if self.id:
            return True
        else:
            return False

    def get_data(self):
        if 'file' in dir(self):
            f = open(self.file, 'r')
            xml = f.read()
            f.close()
        else:
            xml = dccRetrieveXML(self.id)

        try:
            title, authors, year, abstract = dccXMLExtract(xml)
        except:
            print >>sys.stderr, xml
            raise

        data = {
            'institution': 'LIGO Laboratory',
            'number': self.id,
            'dcc': self.id,
            'url': self.gen_url()
            }

        if title:
            data['title'] = title
        if authors:
            data['authors'] = authors
        if abstract:
            data['abstract'] = abstract
        if year:
            data['year'] = year

        return data

    def get_bibtex(self):
        data = self.get_data()
        key = self.get_sid()
        btype = '@techreport'
        bibentry = data2bib(data, key, type=btype)
        return bibentry.as_string()
