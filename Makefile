# Top-level Makefile for dep-checker.
# Copyright 2010 The Linux Foundation.  See LICENSE file for licensing.

default: staticdb/staticdb.sqlite README.txt

package:
	cd package && $(MAKE) rpm_package

staticdb/staticdb.sqlite:
	cd staticdb && $(MAKE)

README.txt: README.html
	w3m -dump $< > $@

clean:
	cd staticdb && $(MAKE) clean
	cd package && $(MAKE) clean
	rm -f README.txt

.PHONY: default clean package
