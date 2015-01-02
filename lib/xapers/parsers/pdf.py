from ..parser import ParserBase

import subprocess

def extract(data):
    cmd = ['pdftotext', '-', '-']
    proc = subprocess.Popen(cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=open('/dev/null','w'),
                            )
    (stdout, stderr) = proc.communicate(input=data)
    proc.wait()
    return stdout

class Parser(ParserBase):
    def extract(self):
        cmd = ['pdftotext', self.path, '-']

        text = subprocess.check_output(cmd, stderr=open('/dev/null','w'))

        return text
