import sys
import io
import pybtex
from pybtex.core import Entry, Person
from pybtex.database.input import bibtex as inparser
from pybtex.database.output import bibtex as outparser
#from pybtex.database.output import bibtexml as outparser

def clean_bib_string(string):
    for char in ['{', '}']:
        string = string.replace(char,'')
    return string

def bib2data(bibtex):
    """Parse a bibtex string for indexable data fields."""

    # io produces a stream object that pybtex can handle
    # FIXME: need to worry about encodings!
    bibfile = io.StringIO(bibtex.decode('UTF-8'))

    parser = inparser.Parser(encoding='UTF-8')
    bibdata = parser.parse_stream(bibfile)

    key = bibdata.entries.keys()[0]
    bibentry = bibdata.entries.values()[0]

    data = {}

    bibfields = bibentry.fields
    for field in bibfields:
        data[field] = unicode(clean_bib_string(bibfields[field]))

    # parse crazy authors entries into list
    authors = []
    for p in bibentry.persons['author']:
        authors.append(unicode(p))

    data['authors'] = authors

    return data, key

def data2bib(data, key):
    """Convert data fields into a bibtex entry."""

    # need to remove authors field from data
    authors = None
    if 'authors' in data:
        authors = data['authors']
        del data['authors']

    # FIXME: what should this be for undefined?  specify
    btype = 'article'

    entry = Entry(btype, fields=data)
    if authors:
        for p in authors:
            entry.add_person(Person(p), 'author')

    bibdata = pybtex.database.BibliographyData()
    bibdata.add_entry(key, entry)

    # FIXME: this is not ouputting the right format
    writer = outparser.Writer()

    f = io.StringIO()
    writer.write_stream(bibdata, f)
    text = f.getvalue()
    f.close()

    return text
