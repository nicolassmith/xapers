#!/usr/bin/make -f

PREFIX := ~/opt/xapers

install:
	rm -rf $(PREFIX)
	mkdir -p $(PREFIX)
	cp -af xapers $(PREFIX)
	install xapers.py $(PREFIX)
