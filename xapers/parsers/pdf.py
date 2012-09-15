# def _pdf2text(self, pdf):
#     from subprocess import Popen, PIPE
#     cmd = ['pdftotext', '-', '-']
#     p = Popen(' '.join(cmd), stdin=PIPE, stdout=PIPE, shell=True)
#     text = p.communicate(pdf.getvalue())[0]
#     if p.wait() != 0:
#         raise IOerror
#     return text

def parse_file(path):
    # extract text from pdf
    # import cStringIO
    # pdf = cStringIO.StringIO()
    # fi = open(os.path.join(self.xapers.root, path), 'rb')
    # #fi = open(path, 'rb')
    # pdf.write(fi.read())
    # fi.close()
    # text = self._pdf2text(pdf)

    from subprocess import Popen, PIPE
    cmd = ['pdftotext', path, '-']
    p = Popen(' '.join(cmd), stdout=PIPE, shell=True)
    text = p.communicate()[0]
    if p.wait() != 0:
        raise IOerror

    return text
