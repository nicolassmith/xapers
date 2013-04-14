# -*- makefile -*-

VERSION:=$(shell git describe --tags | sed -e s/_/~/ -e s/-/+/ -e s/-/~/)

.PHONY: all
all:

.PHONY: test
test:
	./test/xapers-test

.PHONY: debian-snapshot
debian-snapshot:
	rm -rf build/snapshot
	mkdir -p build/snapshot/debian
	git archive HEAD | tar -x -C build/snapshot/
	git archive debian:debian | tar -x -C build/snapshot/debian/
	cd build/snapshot; dch -b -v $(VERSION) -D UNRELEASED 'test build, not for upload'
	cd build/snapshot; echo '3.0 (native)' > debian/source/format
	cd build/snapshot; debuild -us -uc
