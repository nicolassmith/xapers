import urllib2

description = "Digital Object Identifier"

# produces URL string when supplied with valid source identifier
url_format = 'http://dx.doi.org/%s'

id_regex = '(10\.\d{4,}[\w\d\:\.\-\/]+)'

# for regex matching a supplied URL.  match group 1 should return the
# source identifier string
url_regex = url_format % id_regex

# for regex scanning of document text
#scan_regex = '[doi|DOI][\s\.\:]{0,2}(10\.\d{4}[\d\:\.\-\/a-z]+)[A-Z\s]'
#scan_regex = '\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])[[:graph:]])+)\b'
#scan_regex = '(doi|DOI)(10[.][0-9]{4,}(?:[.][0-9]+)*[\/\.](?:(?!["&\'<>])[[:graph:]])+)'
#scan_regex = '(?:doi|DOI)[\s\.\:]{0,2}(10\.\d{4,}[\w\d\:\.\-\/]+)'
scan_regex = '(?:doi|DOI)[\s\.\:]{0,2}' + id_regex

# function to fetch a bibtex entry for a given source identifier
def fetch_bibtex(id):
    # http://www.crossref.org/CrossTech/2011/11/turning_dois_into_formatted_ci.html
    url = url_format % id
    headers = dict(Accept='text/bibliography; style=bibtex')
    req = urllib2.Request(url, headers=headers)
    f = urllib2.urlopen(req)
    bibtex = f.read()
    f.close
    return bibtex
