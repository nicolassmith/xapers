#!/bin/bash -e
dir=$(cd $(dirname $0) && pwd)

export XAPERS_DIR="$dir"/docs

xapers() {
    "$dir"/../xapers.py "$@"
}

# purge previous database
rm -rf $XAPERS_DIR/.xapers

trap 'echo; echo FAILED! a test' EXIT

echo '##########'
echo '# add documents'
echo

xapers add --source=ads:2009RPPh...72g6901A --tags=new,bar $XAPERS_DIR/2009RPPh...72g6901A.pdf
xapers add --source=physrevd:1234jlkj       --tags=new,foo $XAPERS_DIR/PhysRevD.82.044025.pdf
xapers add --source=arxiv:sdf2323           --tags=new,baz --url=http://asdf $XAPERS_DIR/j.1743-6109.2010.01935.x.pdf

echo
echo '##########'
echo '# add illegal path'
echo

# this needs to fail, since the file is already in db
(! xapers add 2009RPPh...72g6901A.pdf)

echo
echo '##########'
echo '# add non-existant'
echo

# this needs to fail, since the file is already in db
(! xapers add $XAPERS_DIR/2009.pdf)

echo
echo '##########'
echo '# add existing'
echo

# this needs to fail, since the file is already in db
(! xapers add $XAPERS_DIR/2009RPPh...72g6901A.pdf)

echo
echo '##########'
echo '# add interactive'
echo

echo 'test/sources/arxiv.html
arXiv
1208.5777
The Progenitors of Short Gamma-Ray Bursts
authors
2007
foo

' | xapers add --prompt $XAPERS_DIR/2007NJPh....9...17L.pdf
echo
echo
xapers search --output=full id:2

echo
echo '##########'
echo '# search all'
echo

xapers search --output=simple '*'

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
echo '# search sources'
echo

xapers search source:ads

echo
echo '##########'
echo '# search by terms'
echo

xapers search pubic hair

echo
echo '##########'
echo '# search by id (2), full'
echo

xapers search --output=full id:2

echo
echo '##########'
echo '# search by id (2), json'
echo

xapers search --output=json id:2

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
