import sys
import cStringIO
from pybtex.database.input import bibtex

def bibtrans(string):
    for char in ['{', '}']:
        string = string.replace(char,'')
    return string

def parse(bib):
    bibfile = cStringIO.StringIO()
    bibfile.write(bib)
    parser = bibtex.Parser()
    bibdata = parser.parse_file('test/sources/doi.bib')
    #bibdata = parser.parse_file('/home/jrollins/ligo/src/papers/multiColorMetrology/GWreferences.bib')
    # try:
    #     bib_data = parser.parse_stream(bib)
    # except:
    #     print >>sys.stderr, "Unable to parse bibtex."
    #     return None

    bibentry = bibdata.entries.values()[0].fields
    # for key in bibdata.entries.keys():
    #     print key
    #     for field, val in bibdata.entries[key].fields.iteritems():
    #         print '   ', field, '=', val

    data = {
        'title': None,
        'authors': None,
        'year': None,
        'abstract': None
        }

    if 'title' in bibentry:
        data['title'] = bibtrans(bibentry['title'])
    if 'authors' in bibentry:
        data['authors'] = bibtrans(bibentry['author'])
    if 'year' in bibentry:
        data['year'] = bibentry['year']
    if 'abstract' in bibentry:
        data['abstract'] = bibtrans(bibentry['abstract'])

    return data
