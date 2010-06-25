# Top-level Makefile for dep-checker.
# Copyright 2010 The Linux Foundation.  See LICENSE file for licensing.

default: staticdb compliance/media/docs/index.html README.txt

package:
	cd package && $(MAKE) rpm_package

staticdb:
	compliance/load_static.py

compliance/media/docs/index.html:
	cd compliance/media/docs && $(MAKE)

README.txt: compliance/media/docs/index.html
	w3m -dump $< > $@

clean:
	cd package && $(MAKE) clean
	cd compliance/media/docs && $(MAKE) clean
	rm -f README.txt

.PHONY: default clean package staticdb
