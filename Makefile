# Top-level Makefile for dep-checker.
# Copyright 2010 The Linux Foundation.  See LICENSE file for licensing.

default: staticdb/staticdb.sqlite

staticdb/staticdb.sqlite:
	cd staticdb && $(MAKE)

clean:
	cd staticdb && $(MAKE) clean

.PHONY: default clean
