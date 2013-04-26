# Top-level Makefile for dep-checker.
# Copyright 2010 The Linux Foundation.  See LICENSE file for licensing.

default: compliance/compliance compliance/media/docs/index.html README.txt

package:
	cd package && $(MAKE)

compliance/compliance: compliance/linkage/models.py compliance/linkage/fixtures/initial_data.xml
	rm -f compliance/compliance
	cd compliance && python manage.py syncdb --noinput

fixture_regen:
	(cd compliance && python manage.py dumpdata --format xml linkage) | \
	  xmllint --format - > compliance/linkage/fixtures/initial_data.xml

compliance/media/docs/index.html:
	cd compliance/media/docs && $(MAKE)

README.txt: compliance/media/docs/index.html
	w3m -dump $< > $@

clean:
	cd package && $(MAKE) clean
	cd compliance/media/docs && $(MAKE) clean
	rm -f README.txt
	rm -f compliance/compliance

.PHONY: default clean package fixture_regen
