def parse_file(path):
    from subprocess import Popen, check_output, PIPE, CalledProcessError
    cmd = ['pdftotext', path, '-']
    #cmd = ['pdf2txt', path]
    # FIXME: figure out how to trap errors better
    text = check_output(' '.join(cmd), shell=True, stderr=open('/dev/null','w'))
    #p = Popen(' '.join(cmd), stdout=PIPE, shell=True)
    #text = p.communicate()[0]
    # FIXME: do something here?
    # if p.wait() != 0:
    #     raise IOerror

    return text
