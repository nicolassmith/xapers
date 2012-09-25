name = 'arxiv'

from HTMLParser import HTMLParser

def parse_url(parsedurl):
    loc = parsedurl.netloc
    path = parsedurl.path
    if loc.find('arxiv.org') < 0:
        return None
    for prefix in ['/abs/', '/pdf/', '/format/']:
        index = path.find(prefix)
        if index == 0:
            break
    index = len(prefix)
    # FIXME: strip anything else?
    sid = path[index:].strip('/')
    return sid

# html parser override to override handler methods
class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.lefthead = False
        self.title = None
        self.authors = []
        self.year = None
        self.sid = None

    def handle_starttag(self, tag, attrs):
        #print "Start tag:", tag

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
                    self.authors.append(attr[1])
                    #self.author = self.author.append(attr[1])
                if date:
                    self.year = attr[1]
                if sid:
                    self.sid = attr[1]

    def handle_endtag(self, tag):
        #print "Encountered an end tag :", tag
        if tag == 'head':
            self.lefthead = True

def get_data(sid, lfile=None):
    urlbase = "http://arxiv.org/abs"
    url = "%s/%s" % (urlbase, sid)

    if lfile:
        #f = open('test/sources/arxiv.html','r')
        f = open(lfile, 'r')
    else:
        import urllib
        f = urllib.urlopen(url)
    html = f.read()
    f.close()

    # instantiate the parser and fed it some HTML
    try:
        parser = MyHTMLParser()
        parser.feed(html)
    except:
        return None

    astring = ' and '.join(parser.authors),

    data = {
        'source':  'arxiv',
        'sid':     sid,
        'title':   parser.title,
        'authors': astring,
        'year':    parser.year,
        }

    return data
