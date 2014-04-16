from xapers.parser import ParserBase

from pipes import quote
from subprocess import check_output

class Parser(ParserBase):
    def extract(self):
        path = quote(self.path)

        cmd = ['pdftotext', path, '-']

        text = check_output(cmd, stderr=open('/dev/null','w'))

        return text
