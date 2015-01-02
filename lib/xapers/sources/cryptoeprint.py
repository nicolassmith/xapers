import urllib
from HTMLParser import HTMLParser

description = "Cryptology ePrint Archive"

url = "https://eprint.iacr.org/"

url_format = 'https://eprint.iacr.org/%s'

url_regex = 'https?://eprint.iacr.org/(\d{4,}/\d{3,})'

# don't know what a scan_regex looks like for IACR eprints. i don't
# think there is one, because i think the submission process happens
# after the pdf is formalized.


# custom definitions for IACR eprints:
bibtex_url = 'https://eprint.iacr.org/eprint-bin/cite.pl?entry=%s'
pdf_url = 'https://eprint.iacr.org/%s.pdf'

# html parser override to override handler methods
class IACRParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.pre = False
        self.data = None

    def handle_starttag(self, tag, attrs):
        if (tag == 'pre'):
            self.pre = True

    def handle_endtag(self, tag):
        if (tag == 'pre'):
            self.pre = False

    def handle_data(self, data):
        if (self.pre):
            self.data = data


def fetch_bibtex(id):
    url = bibtex_url % id

    f = urllib.urlopen(url)
    html = f.read()
    f.close()

    p = IACRParser()
    p.feed(html)
    return unicode(p.data)


def fetch_file(id):
    url = pdf_url % id

    f = urllib.urlopen(url)
    pdf = f.read()
    f.close()

    return (id.split('/').pop() + '.pdf', pdf)
