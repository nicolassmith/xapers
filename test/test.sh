#!/bin/bash -e
dir=$(cd $(dirname $0) && pwd)

export PATH="$dir"/../bin:$PATH
export PYTHONPATH="$dir"/../lib
export XAPERS_DIR="$dir"/tmp.test

TEST_DOC_DIR="$dir"/docs

# purge previous database
rm -rf "$XAPERS_DIR"
mkdir -p "$XAPERS_DIR"

trap 'echo; echo FAILED! a test' EXIT

echo '##########'
echo '# add documents'
echo

xapers add --tags=new,bar \
    --source=ads:2009RPPh...72g6901A \
    --file=$TEST_DOC_DIR/2009RPPh...72g6901A.pdf
xapers add --tags=new,foo \
    --file=$TEST_DOC_DIR/PhysRevD.82.044025.pdf
xapers add --tags=new,baz \
    --file=$TEST_DOC_DIR/j.1743-6109.2010.01935.x.pdf
#xapers add --tags=new,baz --url=2010NIMPA.624..223A.bib $TEST_DOC_DIR/j.1743-6109.2010.01935.x.pdf

# xapers add --tags=new,bar --bib=$TEST_DOC_DIR/2007NJPh....9...17L.bib $TEST_DOC_DIR/2007NJPh....9...17L.pdf

# xapers add --tags=new,bar \
#     --source=$TEST_DOC_DIR/2007NJPh....9...17L.bib \
#     --file=$TEST_DOC_DIR/2007NJPh....9...17L.pdf

xapers add --tags=new,bar \
    --source=$TEST_DOC_DIR/josaa-29-10-2092-1.bib \
    --file=$TEST_DOC_DIR/josaa-29-10-2092-1.pdf

#xapers add --bib=$TEST_DOC_DIR/josaa-29-10-2092-1.bib --file=$TEST_DOC_DIR/josaa-29-10-2092-1.pdf

# echo
# echo '##########'
# echo '# add illegal path'
# echo

# # this needs to fail, since the file is already in db
# (! xapers add 2009RPPh...72g6901A.pdf)

echo
echo '##########'
echo '# add non-existant'
echo

# this needs to fail, since the file is already in db
(! xapers add --file=foo.pdf)

# echo
# echo '##########'
# echo '# add existing'
# echo

# # this needs to fail, since the file is already in db
# (! xapers add $TEST_DOC_DIR/2009RPPh...72g6901A.pdf)

# echo
# echo '##########'
# echo '# add interactive'
# echo

# echo 'test/sources/arxiv.html
# arXiv
# 1208.5777
# The Progenitors of Short Gamma-Ray Bursts
# authors
# 2007
# foo

# ' | xapers add --prompt $TEST_DOC_DIR/2007NJPh....9...17L.pdf
# echo
# echo
# xapers search --output=full id:2

echo
echo '##########'
echo '# search all'
echo

xapers search '*'

echo
echo '##########'
echo '# search all output tags'
echo

xapers search --output=tags '*'

echo
echo '##########'
echo '# search all output sources'
echo

xapers search --output=sources '*'

echo
echo '##########'
echo '# search output bibtex'
echo

xapers search --output=bibtex tag:new

echo
echo '##########'
echo '# search sources (doi)'
echo

xapers search source:doi

echo
echo '##########'
echo '# search by terms (pubic hair)'
echo

xapers search pubic hair

echo
echo '##########'
echo '# search by id (id:2)'
echo

xapers search id:2

echo
echo '##########'
echo '# search by tags (foo)'
echo

xapers search tag:foo

echo
echo '##########'
echo '# add tag (qux)'
echo

xapers tag +qux id:3
xapers search id:3

echo
echo '##########'
echo '# remove tag (qux)'
echo

xapers tag -qux id:3 
xapers search id:3

trap EXIT
