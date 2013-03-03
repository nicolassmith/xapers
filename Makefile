# -*- makefile -*-

VERSION:=$(shell git describe --tags | sed -e s/_/~/ -e s/-/+/ -e s/-/~/)

.PHONY: all
all:

.PHONY: debian-snapshot
debian-snapshot:
	rm -rf build/deb
	mkdir -p build/deb/debian
	git archive HEAD | tar -x -C build/deb/
	git archive debian:debian | tar -x -C build/deb/debian/
	cd build/deb; dch -b -v $(VERSION) -D UNRELEASED 'test build, not for upload'
	cd build/deb; echo '3.0 (native)' > debian/source/format
	cd build/deb; debuild -us -uc
