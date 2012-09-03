name = 'dcc'

import sys
import cStringIO

def parse_url(parsedurl):
    sid = None
    loc = parsedurl.netloc
    path = parsedurl.path
    if loc.find('dcc.ligo.org') < 0:
        return None
    for query in parsedurl.query.split('&'):
        if 'docid=' in query:
            field, sid = query.split('=')
    return sid

def dccRetrieve(url):
    import pycurl
    curl = pycurl.Curl()
    # get the document
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
    curl.close()
    return doc

def dccXMLExtract(xmlfile):
    from xml.dom.minidom import parse, parseString
    xml = parseString(xmlfile.getvalue())
    title = xml.getElementsByTagName("title")[0].firstChild.data
    alist = xml.getElementsByTagName("author")
    authors = []
    for author in alist:
        authors.append(author.getElementsByTagName("fullname")[0].firstChild.data)
    abstract = xml.getElementsByTagName("abstract")[0].firstChild.data
    return title, authors, abstract

def get_data(sid, lfile=None):
    data = {}

    urlbase = 'dcc.ligo.org/cgi-bin/private/DocDB/'
    #doc['Url'] = 'https://' + urlbase + 'ShowDocument?docid=' + sid
    #print >>sys.stderr, doc['Url']

    # url = 'https://' + urlbase + 'RetrieveFile?docid=' + docid
    # pdf = dccRetrieve(url)
    # doc.addPDF(pdf)

    url = 'https://' + urlbase + 'ShowDocument?docid=' + sid + '&outformat=xml'
    xml = dccRetrieve(url)
    print xml.getvalue()
    title, authors, abstract = dccXMLExtract(xml)

    data['title'] = title
    data['authors'] = authors
    data['year'] = none
    data['abstract'] = abstract
    data['bibtex'] = abstract

    data = {
        'title':   title,
        'authors': bdata['authors'],
        'year':    bdata['year'],
        'bibtex':  bibtex,
        }

    return data
