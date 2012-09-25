import sys
import cStringIO
import io
from pybtex.database.input import bibtex

def bibtrans(string):
    for char in ['{', '}']:
        string = string.replace(char,'')
    return string

def parse(bib):
    # bibfile = cStringIO.StringIO()
    # bibfile.write(bib)
    bibfile = io.StringIO(unicode(bib))

    parser = bibtex.Parser(encoding='UTF-8')
    bibdata = parser.parse_stream(bibfile)

    # for key in bibdata.entries.keys():
    #     print key
    #     for field, val in bibdata.entries[key].fields.iteritems():
    #         print '   ', field, '=', val
    #     print '   ', 'authors =', ' and '.join(bibdata.entries[key].persons['author'])

    bibentry = bibdata.entries.values()[0].fields

    authors = []
    for p in bibdata.entries.values()[0].persons['author']:
        authors.append('%s %s' % (p.first()[0], p.last()[0]))

    data = {
        'url': None,
        'title': None,
        'authors': None,
        'year': None,
        'abstract': None
        }

    if 'url' in bibentry:
        data['url'] = bibtrans(bibentry['url']).encode('utf-8')
    if 'title' in bibentry:
        data['title'] = bibtrans(bibentry['title']).encode('utf-8')
    data['authors'] = authors
    if 'year' in bibentry:
        data['year'] = bibentry['year'].encode('utf-8')
    if 'abstract' in bibentry:
        data['abstract'] = bibtrans(bibentry['abstract']).encode('utf-8')

    return data
