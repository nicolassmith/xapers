import sys
import pycurl
import cStringIO
import xapers.bibtex as bibparse

def dccRetrieve(url):
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    # --negotiate --cookie foo --cookie-jar foo --user : --location-trusted --insecure
    curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_GSSNEGOTIATE)
    #curl.setopt(pycurl.COOKIEFILE, 'foo')
    #curl.setopt(pycurl.COOKIEJAR, 'foo')
    curl.setopt(pycurl.USERPWD, ':')
    curl.setopt(pycurl.FOLLOWLOCATION, 1)
    curl.setopt(pycurl.UNRESTRICTED_AUTH, 1)
    doc = cStringIO.StringIO()
    curl.setopt(pycurl.WRITEFUNCTION, doc.write)
    try:
        curl.perform()
    except:
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
    # FIXME: check return code
    curl.close()
    return doc.getvalue()

def dccXMLExtract(xmlstring):
    from xml.dom.minidom import parse, parseString
    xml = parseString(xmlstring)
    title = xml.getElementsByTagName("title")[0].firstChild.data
    alist = xml.getElementsByTagName("author")
    authors = []
    for author in alist:
        authors.append(author.getElementsByTagName("fullname")[0].firstChild.data)
    abstract = xml.getElementsByTagName("abstract")[0].firstChild.data
    # FIXME: find year
    year = None
    return title, authors, year, abstract

class Source():
    source = 'dcc'
    netloc = 'dcc.ligo.org'

    def __init__(self, sid=None):
        self.sid = sid

    def gen_url(self):
        return 'http://%s/cgi-bin/private/DocDB/ShowDocument?docid=%s' % (self.netloc, self.sid)

    def parse_url(self, parsedurl):
        loc = parsedurl.netloc
        path = parsedurl.path
        if loc.find(self.netloc) >= 0:
            for query in parsedurl.query.split('&'):
                if 'docid=' in query:
                    field, self.sid = query.split('=')
                    break

    def get_data(self):
        # url = 'http://%s/cgi-bin/private/DocDB/RetrieveFile?docid=' % (self.netloc, self.sid)
        # pdf = dccRetrieve(url)

        if 'file' in dir(self):
            f = open(self.file, 'r')
            xml = f.read()
            f.close()
        else:
            url = self.gen_url() + '&outformat=xml'
            xml = dccRetrieve(url)

        try:
            title, authors, year, abstract = dccXMLExtract(xml)
        except:
            print >>sys.stderr, xml
            return None

        data = {
            'dcc':      self.sid,
            'title':    title,
            'authors':  authors,
            'abstract': abstract,
            'url':      self.gen_url()
            }

        if year:
            data['year'] = year

        return data

    def get_bibtex(self):
        data = self.get_data()
        if not data:
            return
        key = '%s:%s' % (self.source, self.sid)
        bibentry = bibparse.data2bib(data, key)
        return bibentry.as_string()
