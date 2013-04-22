import os

##################################################

class ParseError(Exception):
    """Base class for Xapers parser exceptions."""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

##################################################

class ParserBase():
    """Base class for Xapers document parsering."""
    def __init__(self, path):
        self.path = os.path.expanduser(path)

        if not os.path.exists(self.path):
            raise ParseError("File %s not found." % self.path)

    def extract(self):
        pass

##################################################

def parse_file(path):
    # FIXME: determine mime type
    mimetype = 'pdf'

    try:
        mod = __import__('xapers.parsers.' + mimetype, fromlist=['Parser'])
        pmod = getattr(mod, 'Parser')
    except ImportError:
        raise ParseError("Unknown parser '%s'." % mimetype)

    try:
        text = pmod(path).extract()
    except Exception, e:
        raise ParseError("Could not parse file: %s" % e)

    return text
