from xapers.parser import ParserBase

from subprocess import check_output

class Parser(ParserBase):
    def extract(self):
        cmd = ['pdftotext', self.path, '-']

        text = check_output(cmd, stderr=open('/dev/null','w'))

        return text
