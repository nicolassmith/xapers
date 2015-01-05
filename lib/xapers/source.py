import os
import re
import pkgutil
from urlparse import urlparse

import sources
from parser import parse_file

##################################################

class SourceError(Exception):
    pass

class SourceAttributeError(SourceError):
    def __init__(self, source, msg):
        self.source = source
        self.msg = msg
    def __str__(self):
        return "Source '%s' does not include a %s." % (self.source.name, self.msg)

##################################################

class Source(object):
    """Xapers class representing an online document source.

    The Source object is build from a source nickname (name) and
    possibly user-defined source module.

    """
    def __init__(self, name, module):
        self.name = name
        self.module = module

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__, self.name, self.module)

    def __str__(self):
        return self.name

    def __getitem__(self, id):
        return SourceItem(self, id)

    @property
    def path(self):
        return self.module.__file__

    @property
    def is_builtin(self):
        bpath = os.path.dirname(sources.__file__)
        spath = os.path.dirname(self.path)
        return os.path.commonprefix([bpath, spath]) == bpath

    @property
    def description(self):
        try:
            return self.module.description
        except AttributeError:
            raise SourceAttributeError(self, "'description' property")

    @property
    def url(self):
        try:
            return self.module.url
        except AttributeError:
            raise SourceAttributeError(self, "'url' property")

    @property
    def url_regex(self):
        try:
            return self.module.url_regex
        except AttributeError:
            raise SourceAttributeError(self, "'url_regex' property")

    @property
    def scan_regex(self):
        try:
            return self.module.scan_regex
        except AttributeError:
            raise SourceAttributeError(self, "'scan_regex' property")

    def fetch_bibtex(self, id):
        try:
            return self.module.fetch_bibtex(id)
        except AttributeError:
            raise SourceAttributeError(self, "fetch_bibtex() function")

    def fetch_file(self, id):
        try:
            return self.module.fetch_file(id)
        except AttributeError:
            raise SourceAttributeError(self, "fetch_file() function")

class SourceItem(Source):
    """Xapers class representing an item from an online source.

    """
    def __init__(self, source, id):
        super(SourceItem, self).__init__(source.name, source.module)
        self.id = id
        self.sid = '%s:%s' % (self.name, self.id)

    def __repr__(self):
        s = super(SourceItem, self).__repr__()
        return '%s(%s, %s)' % (self.__class__, s, self.id)

    def __hash__(self):
        return hash(self.sid)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.sid == other.sid
        return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.sid

    @property
    def url(self):
        try:
            return self.module.url_format % self.id
        except AttributeError:
            raise SourceAttributeError(self, "'url_format' property")

    def fetch_bibtex(self):
        return super(SourceItem, self).fetch_bibtex(self.id)

    def fetch_file(self):
        return super(SourceItem, self).fetch_file(self.id)

##################################################

class Sources(object):
    def __init__(self):
        self.sourcespath = sources.__path__
        extra = os.getenv('XAPERS_SOURCE_PATH', None)
        if extra:
            for path in extra.split(':'):
                if path:
                    sourcespath.insert(0, path)
        else:
            self.sourcespath.insert(0, os.path.expanduser(os.path.join('~','.xapers','sources')))

        self._sources = {}
        for (loader, name, ispkg) in pkgutil.walk_packages(self.sourcespath):
            if ispkg:
                continue
            #self._modules[name] = loader.find_module(name).load_module(name)
            module = loader.find_module(name).load_module(name)
            self._sources[name] = Source(name, module)

    def __repr__(self):
        return '%s(%s)' % (self.__class__, self.sourcespath)

    def get_source(self, name, id=None):
        try:
            source = self._sources[name]
        except KeyError:
            raise SourceError("unknown source: %s" % name)
        if id:
            return source[id]
        else:
            return source

    def __getitem__(self, sid):
        name = None
        id = None
        try:
            vals = sid.split(':')
        except ValueError:
            raise SourceError("could not parse sid string")
        name = vals[0]
        if len(vals) > 1:
            id = vals[1]
        return self.get_source(name, id)

    def __iter__(self):
        return self._sources.itervalues()

    def match_source(self, string):
        """Return Source object from URL or source identifier string.

        """
        o = urlparse(string)

        # if the scheme is http, look for source match
        if o.scheme in ['http', 'https']:
            for source in self:
                try:
                    match = re.match(source.url_regex, string)
                except SourceAttributeError:
                    # FIXME: warning?
                    continue
                if match:
                    return source[match.group(1)]

        elif o.scheme != '' and o.path != '':
            return self.get_source(o.scheme, o.path)

        raise SourceError('String matches no known source.')

    def scan_file(self, file):
        """Scan document file for source identifiers

        Source 'scan_regex' attributes are used.
        Returns a list of SourceItem objects.

        """
        text = parse_file(file)
        items = set()
        for source in self:
            try:
                regex = re.compile(source.scan_regex)
            except SourceAttributeError:
                # FIXME: warning?
                continue
            matches = regex.findall(text)
            if not matches:
                continue
            for match in matches:
                items.add(source[match])
        return list(items)

    def scan_bibentry(self, bibentry):
        """Scan bibentry for source identifiers.

        Bibentry keys are searched for source names, and bibentry
        values are assumed to be individual identifier strings.
        Returns a list of SourceItem objects.

        """
        fields = bibentry.get_fields()
        items = set()
        for field, value in fields.iteritems():
            for source in self:
                # FIXME: should we be case sensitive?
                if source.name.lower() == field.lower():
                    items.add(source[value])
        # FIXME: how do we get around special exception for this?
        if 'eprint' in fields:
            items.add(self.get_source('arxiv', fields['eprint']))
        return list(items)
