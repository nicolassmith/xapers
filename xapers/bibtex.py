import sys
import io
from pybtex.database.input import bibtex as bibparser

def clean_string(string):
    for char in ['{', '}']:
        string = string.replace(char,'')
    return string

def bib2data(bibtex):
    """Parse a bibtex string for indexable data fields."""

    # io produces a stream object that pybtex can handle
    # FIXME: need to worry about encodings!
    bibfile = io.StringIO(bibtex.decode('UTF-8'))

    parser = bibparser.Parser(encoding='UTF-8')

    bibdata = parser.parse_stream(bibfile)

    # for key in bibdata.entries.keys():
    #     print key
    #     for field, val in bibdata.entries[key].fields.iteritems():
    #         print '   ', field, '=', val
    #     print '   ', 'authors =', ' and '.join(bibdata.entries[key].persons['author'])

    bibentry = bibdata.entries.values()[0].fields

    # parse crazy authors entries
    authors = []
    for p in bibdata.entries.values()[0].persons['author']:
        authors.append('%s %s' % (p.first()[0], p.last()[0]))

    data = {
        'url': None,
        'title': None,
        'authors': None,
        'year': None,
        }

    if 'url' in bibentry:
        data['url'] = clean_string(bibentry['url']).encode('utf-8')

    if 'title' in bibentry:
        data['title'] = clean_string(bibentry['title']).encode('utf-8')

    data['authors'] = authors

    if 'year' in bibentry:
        data['year'] = bibentry['year'].encode('utf-8')

    return data

def data2bib(data):
    pass
