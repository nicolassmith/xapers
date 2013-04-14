import urllib
from HTMLParser import HTMLParser
import xapers.bibtex as bibparse

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
            #print "     attr:", attr
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
                    #self.author = self.author.append(attr[1])
                if date:
                    self.year = attr[1].split('/')[0]
                if sid:
                    self.sid = attr[1]

    def handle_endtag(self, tag):
        if tag == 'head':
            self.lefthead = True

class Source():
    source = 'arxiv'
    netloc = 'arxiv.org'

    def __init__(self, id=None):
        self.id = id

    def get_sid(self):
        if self.id:
            return '%s:%s' % (self.source, self.id)

    def gen_url(self):
        if self.id:
            return 'http://%s/abs/%s' % (self.netloc, self.id)

    def match(self, netloc, path):
        if netloc.find(self.netloc) < 0:
            return False
        for prefix in ['/abs/', '/pdf/', '/format/']:
            index = path.find(prefix)
            if index == 0:
                break
        index = len(prefix)
        # FIXME: strip anything else?
        self.id = path[index:].strip('/')
        return True

    def get_data(self):
        if 'file' in dir(self):
            url = None
            f = open(self.file, 'r')
        else:
            url = self.gen_url()
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
            'arxiv':   self.id,
            'title':   parser.title,
            'authors': parser.author,
            'year':    parser.year,
            'eprint':  self.id,
            'url':     self.gen_url(),
            }

        return data

    def get_bibtex(self):
        data, url = self.get_data()
        bibentry = bibparse.data2bib(data, self.get_sid())
        return bibentry.as_string()
