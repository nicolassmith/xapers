import os
import sys
import io
import json
import pybtex
from pybtex.core import Entry, Person
from pybtex.bibtex.utils import split_name_list
from pybtex.database.input import bibtex as inparser
from pybtex.database.output import bibtex as outparser


def clean_bib_string(string):
    for char in ['{', '}']:
        string = string.replace(char,'')
    return string

class BibentryError(Exception):
    """Base class for Xapers bibentry exceptions."""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class Bibentry():
    def __init__(self, bibtex=None, entry=None, key=None):
        if entry and key:
            self.entry = entry
            self.key = key
        elif bibtex:
            parser = inparser.Parser(encoding='UTF-8')
            if os.path.exists(bibtex):
                self.bibdata = parser.parse_file(bibtex)
            else:
                stream = io.StringIO(unicode(bibtex.decode('utf-8')))
                self.bibdata = parser.parse_stream(stream)
                stream.close()
            self.key = self.bibdata.entries.keys()[0]
            self.entry = self.bibdata.entries.values()[0]
        else:
            # FIXME: do something here?
            pass

    def _entry2db(self):
        db = pybtex.database.BibliographyData()
        db.add_entry(self.key, self.entry)
        return db

    def get_authors(self):
        """Return a list of authors."""
        authors = []
        if 'author' in self.entry.persons:
            for p in self.entry.persons['author']:
                authors.append(clean_bib_string(unicode(p)))
        return authors

    def get_fields(self):
        """Return a dict of non-author fields."""
        bibfields = self.entry.fields
        # entry.fields is actually already a dict, but we want to
        # clean the strings first
        fields = {}
        for field in bibfields:
            fields[field] = unicode(clean_bib_string(bibfields[field]))
        return fields

    def as_string(self):
        """Return entry as formatted bibtex string."""
        writer = outparser.Writer()
        f = io.StringIO()
        writer.write_stream(self._entry2db(), f)
        string = f.getvalue()
        f.close()
        string = string.strip()
        return string

    def to_file(self, path):
        """Write entry bibtex to file."""
        writer = outparser.Writer()
        writer.write_file(self._entry2db(), path)


def data2bib(data, key):
    """Convert a python dict into a Bibentry object."""

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

    return Bibentry(entry=entry, key=key)


def json2bib(jsonstring, key):
    """Convert a json string into a Bibentry object."""

    if not json:
        return

    data = json.loads(jsonstring)

    # FIXME: determine this somehow
    btype = 'article'

    # need to remove authors field from data
    authors = None
    if 'author' in data:
        authors = data['author']
        del data['author']

    if 'issued' in data:
        data['year'] = str(data['issued']['date-parts'][0][0])
        del data['issued']

    # delete other problematic fields
    del data['editor']

    entry = Entry(btype, fields=data)

    if authors:
        for author in authors:
            entry.add_person(Person(first=author['given'], last=author['family']), 'author')

    return Bibentry(entry=entry, key=key)
