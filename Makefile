# -*- makefile -*-

VERSION:=$(shell git describe --tags | sed -e s/_/~/ -e s/-/+/ -e s/-/~/)

PV_FILE=lib/xapers/version.py

.PHONY: all
all:

.PHONY: test
test:
	./test/xapers-test

.PHONY: update-version
update-version:
	echo "__version__ = '$(VERSION)'" >$(PV_FILE)

.PHONY: release
ifdef V
update-version: VERSION:=$(V)
release: VERSION:=$(V)
release: update-version
	make test
	git commit -m "Update version for release $(VERSION)." $(PV_FILE)
	git tag --sign -m "Xapers $(VERSION) release." $(VERSION)
else
release:
	git tag -l | grep -v debian/
endif

.PHONY: deb-snapshot
deb-snapshot:
	rm -rf build/snapshot
	mkdir -p build/snapshot/debian
	git archive HEAD | tar -x -C build/snapshot/
	git archive debian:debian | tar -x -C build/snapshot/debian/
	cd build/snapshot; make update-version
	cd build/snapshot; dch -b -v $(VERSION) -D UNRELEASED 'test build, not for upload'
	cd build/snapshot; echo '3.0 (native)' > debian/source/format
	cd build/snapshot; debuild -us -uc

.PHONY: clean
clean:
	rm -rf build
	rm -rf test/test-results
	rm -rf test/tmp.*
	debuild clean 2>/dev/null || true
