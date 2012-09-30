import sys
import io
import pybtex
from pybtex.core import Entry, Person
from pybtex.bibtex.utils import split_name_list
from pybtex.database.input import bibtex as inparser
from pybtex.database.output import bibtex as outparser

def clean_bib_string(string):
    for char in ['{', '}']:
        string = string.replace(char,'')
    return string


class Bibentry():
    def __init__(self, bibtex):
        parser = inparser.Parser(encoding='UTF-8')

        stream = io.StringIO(bibtex.decode('UTF-8'))
        self.bibdata = parser.parse_stream(stream)

        self.key = self.bibdata.entries.keys()[0]
        self.entry = self.bibdata.entries.values()[0]

    def get_authors(self):
        """Return a list of authors."""
        authors = []
        for p in self.entry.persons['author']:
            authors.append(clean_bib_string(unicode(p)))
        return authors

    def get_fields(self):
        """Return a dict of entry fields."""
        bibfields = self.entry.fields
        fields = {}
        for field in bibfields:
            fields[field] = unicode(clean_bib_string(bibfields[field]))
        return fields

    def get_data(self):
        """Return entire entry as a dict."""
        data = self.get_fields()
        data['authors'] = self.get_authors()
        return data

    def as_string(self):
        """Return entry as formatted bibtex string."""
        bibdata = pybtex.database.BibliographyData()
        bibdata.add_entry(self.key, self.entry)
        writer = outparser.Writer()
        f = io.StringIO()
        writer.write_stream(self.bibdata, f)
        string = f.getvalue()
        f.close()
        string = string.strip()
        return string


def data2bib(data, key):
    """Convert data fields into a Bibentry object."""

    if not data:
        return

    # FIXME: what should this be for undefined?
    btype = 'article'

    # need to remove authors field from data
    authors = None
    if 'authors' in data:
        authors = data['authors']
        if isinstance(authors, str):
            authors = split_name_list(authors)
            if len(authors) == 1:
                authors = authors[0].split(',')
        del data['authors']

    entry = Entry(btype, fields=data)
    if authors:
        for p in authors:
            entry.add_person(Person(p), 'author')

    # make a full bibdb with the single entry
    bibdata = pybtex.database.BibliographyData()
    bibdata.add_entry(key, entry)

    # FIXME: how do we make this output {}-wrapped fields?
    writer = outparser.Writer()

    # now write the db to a bibtex entry string
    f = io.StringIO()
    writer.write_stream(bibdata, f)
    text = f.getvalue()
    f.close()
    return Bibentry(text)
