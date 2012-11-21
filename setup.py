#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'xapers',
    version = '0.0',
    description = 'Xapian article indexing system.',
    author = 'Jameson Rollins',
    author_email = 'jrollins@finestructure.net',
    url = '',

    package_dir = {'': 'lib'},
    packages = [
        'xapers',
        'xapers.parsers',
        'xapers.sources',
        'xapers.cli',
        'xapers.nci',
        ],
    scripts = ['bin/xapers'],

    requires = [
        'xapian',
        'pybtex',
        'urwid'
        ],
    )
