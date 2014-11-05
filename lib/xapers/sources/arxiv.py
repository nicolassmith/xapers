import urllib
from HTMLParser import HTMLParser
from xapers.bibtex import data2bib

description = "Open access e-print service"

url_format = 'http://arxiv.org/abs/%s'

url_regex = 'http://arxiv.org/(?:abs|pdf|format)/([^/]*)'

# html parser override to override handler methods
class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.lefthead = False
        self.title = None
        self.author = []
        self.year = None
        self.sid = None

    def handle_starttag(self, tag, attrs):
        title = False
        author = False
        date = False
        sid = False

        if self.lefthead:
            return

        if tag != 'meta':
            return

        for attr in attrs:
            if attr[0] == 'name':
                if attr[1] == 'citation_title':
                    title = True
                if attr[1] == 'citation_author':
                    author = True
                if attr[1] == 'citation_date':
                    date = True
                if attr[1] == 'citation_arxiv_id':
                    sid = True

            if attr[0] == 'content':
                if title:
                    self.title = attr[1]
                if author:
                    self.author.append(attr[1])
                if date:
                    self.year = attr[1].split('/')[0]
                if sid:
                    self.sid = attr[1]

    def handle_endtag(self, tag):
        if tag == 'head':
            self.lefthead = True

def fetch_bibtex(id):
    url = url_format % id

    f = urllib.urlopen(url)
    html = f.read()
    f.close()

    # instantiate the parser and fed it some HTML
    try:
        parser = MyHTMLParser()
        parser.feed(html)
    except:
        return None

    data = {
        'arxiv':   id,
        'title':   parser.title,
        'authors': parser.author,
        'year':    parser.year,
        'eprint':  id,
        'url':     url_format % id,
        }

    bibentry = data2bib(data, 'arxiv:%s' % id)
    return bibentry.as_string()
