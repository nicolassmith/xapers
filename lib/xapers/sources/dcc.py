import sys
import pycurl
import cStringIO
import tempfile
from xapers.bibtex import data2bib

description = "LIGO Document Control Center"

url = 'https://dcc.ligo.org/'

url_format = 'https://dcc.ligo.org/%s'

url_regex = 'https://dcc.ligo.org/(?:LIGO-)?([^/]*)'

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

def fetch_bibtex(id):
    xml = dccRetrieveXML(id)

    try:
        title, authors, year, abstract = dccXMLExtract(xml)
    except:
        print >>sys.stderr, xml
        raise

    data = {
        'institution': 'LIGO Laboratory',
        'number': id,
        'dcc': id,
        'url': url_format % id
        }

    if title:
        data['title'] = title
    if authors:
        data['authors'] = authors
    if abstract:
        data['abstract'] = abstract
    if year:
        data['year'] = year

    key = 'dcc:%s' % id

    btype = '@techreport'
    return data2bib(data, key, type=btype)
