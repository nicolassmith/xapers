#!/usr/bin/make -f

PREFIX := ~/opt/xapers

install:
	git stash
	rm -rf $(PREFIX)
	mkdir -p $(PREFIX)
	cp -af xapers $(PREFIX)
	install xapers.py $(PREFIX)
	git stash pop
