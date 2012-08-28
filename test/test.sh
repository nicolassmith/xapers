#!/bin/bash -e
dir=$(dirname $0)
export XAPERS_DIR=$dir/docs

xapers() {
    ./xapers.py "$@"
}

# purge previous database
rm -rf $XAPERS_DIR/.xapers


echo '##########'
echo '# add documents'
echo

# for file in $(ls -1 "$XAPERS_DIR"/*.pdf); do
# done
xapers add --sources=ads:2007NJPh....9...17L --tags=new,foo 2007NJPh....9...17L.pdf
xapers add --sources=ads:2009RPPh...72g6901A --tags=new,bar 2009RPPh...72g6901A.pdf
xapers add --sources=physrevd:1234jlkj       --tags=new,foo PhysRevD.82.044025.pdf
xapers add --sources=arxiv:sdf2323           --tags=new,baz --url=http://asdf j.1743-6109.2010.01935.x.pdf

echo
echo '##########'
echo '# search all'
echo

xapers search --output=simple '*'
#xapers search '*'

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
echo '# search by id (2)'
echo

xapers search --output=full id:2

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
