PACKAGE=dep-checker
# version defined in site_settings.py
VERSION=$(shell grep gui_version ../compliance/linkage/site_settings.py | awk '{print $$3}' | sed 's|"||g')
RELEASE=2

# we can optionally bundle django
DJANGO_VERSION=1.2.1
DJANGO_URL=http://www.djangoproject.com/download/$(DJANGO_VERSION)/tarball/
ifdef WITH_DJANGO
WITH_ARGS=--with django
endif

# Derive date string for daily snapshots
ISO_DATE=$(shell date +"%Y%m%d")
PWD=$(shell pwd)

FULL_PACKAGE_NAME=$(PACKAGE)-$(VERSION)
RPM_BINARY_NAME=$(FULL_PACKAGE_NAME)-$(RELEASE).$(RPM_BUILD_ARCH).rpm
RPM_SOURCE_NAME=$(FULL_PACKAGE_NAME)-$(RELEASE).src.rpm

SOURCE1 = $(PACKAGE)-$(VERSION).tar.gz
SOURCE2 = Django-$(DJANGO_VERSION).tar.gz

# Temporary build directory
TMP_BUILD_DIR=/tmp/$(FULL_PACKAGE_NAME)

# Handle different version generation for snapshots than for official builds
# OFFICIAL_RELEASE should be set to the tag to extract from version control
ifdef OFFICIAL_RELEASE
VERSION_SUFFIX=
EXPORT_TAG=$(OFFICIAL_RELEASE)
else
VERSION_SUFFIX=.$(ISO_DATE)
EXPORT_TAG=HEAD
endif

# Determine whether to use rpm or rpmbuild to build the packages
ifeq ($(wildcard /usr/bin/rpmbuild),)
	RPM_BUILD_CMD=rpm
else
	RPM_BUILD_CMD=rpmbuild 
endif

# Get RPM configuration information
# NOTE THAT RPM_TMP_BUILD_DIR IS DELETED AFTER THE RPM BUILD IS COMPLETED
# The rpmrc file translates targets where there are multiple choices per
# architecture. On build, the derived RPM_BUILD_ARCH is given as the target
RCFILELIST="/usr/lib/rpm/rpmrc:./rpmrc"
RPM_TMP_BUILD_DIR=/var/tmp/rpm-build
# noarch package
RPM_BUILD_ARCH=noarch
RPM_BINARY_DIR=$(RPM_TMP_BUILD_DIR)/RPMS/noarch
#RPM_BUILD_ARCH=$(shell rpm --rcfile ${RCFILELIST} --eval=%{_target_cpu})
#RPM_BINARY_DIR=$(RPM_TMP_BUILD_DIR)/RPMS/$(RPM_BUILD_ARCH)
RPM_SRPM_DIR=$(RPM_TMP_BUILD_DIR)/SRPMS

# Default target
ifndef BUILD_NO_DEB
all: rpm_package deb_package
else
all: rpm_package
endif

clean:
	@rm -f *.rpm *.deb $(SOURCE1) $(SOURCE2) $(PACKAGE).spec
	@rm -rf $(PACKAGE)-$(VERSION) $(PACKAGE)-$(VERSION).orig

tarball: $(SOURCE1) 
ifdef WITH_DJANGO 
	$(shell if [ ! -f $(SOURCE2) ];then wget $(DJANGO_URL);fi)
endif

# Specfile generation rule
%.spec : %.spec.sed
	sed -e "s#@VERSION@#`echo $(VERSION)`#" -e "s#@RELEASE@#`echo $(RELEASE)`#" -e "s#@DJANGO_VERSION@#`echo $(DJANGO_VERSION)`#" < $< > $@

deb_package: rpm_package
	alien -gcdk $(RPM_BINARY_NAME)
	perl -pe 's/^(Depends:.*)/\1, python-django/' < $(PACKAGE)-$(VERSION)/debian/control > $(PACKAGE)-$(VERSION)/debian/control.new
	rm -f $(PACKAGE)-$(VERSION)/debian/control
	cd $(PACKAGE)-$(VERSION)/debian && mv control.new control
	cd $(PACKAGE)-$(VERSION) && fakeroot debian/rules binary
	rm -rf $(PACKAGE)-$(VERSION) $(PACKAGE)-$(VERSION).orig

rpm_package: $(RPM_BINARY_NAME) $(RPM_SOURCE_NAME) 

list_uploadable:
	@echo $(RPM_BINARY_NAME)
ifndef BUILD_NO_DEB
	@ls *.deb
endif

$(RPM_BINARY_NAME) $(RPM_SOURCE_NAME): $(PACKAGE).spec tarball
	@mkdir -p $(RPM_TMP_BUILD_DIR)/BUILD
	@mkdir -p $(RPM_TMP_BUILD_DIR)/RPMS
	@mkdir -p $(RPM_TMP_BUILD_DIR)/SRPMS
ifdef SIGN_PACKAGES
	@expect -c 'set timeout -1' -c 'spawn $(RPM_BUILD_CMD) --sign --rcfile ${RCFILELIST} --define=_sourcedir\ $(PWD) --define=_topdir\ $(RPM_TMP_BUILD_DIR) --define=_target_cpu\ $(RPM_BUILD_ARCH) $(WITH_ARGS) -ba $(PACKAGE).spec' -c 'expect -ex "Enter pass phrase:"' -c 'send "\n"' -c 'expect "Executing(%clean)"' -c 'expect "exit 0"' -c 'send "\n"'
else
	@$(RPM_BUILD_CMD) --rcfile ${RCFILELIST} --define="_sourcedir $(PWD)" --define="_topdir $(RPM_TMP_BUILD_DIR)" --define="_target_cpu $(RPM_BUILD_ARCH)" $(WITH_ARGS) -ba $(PACKAGE).spec
endif
	@mv $(RPM_SRPM_DIR)/$(RPM_SOURCE_NAME) .
	@mv $(RPM_BINARY_DIR)/$(RPM_BINARY_NAME) .
	@rm -rf $(RPM_TMP_BUILD_DIR)

$(SOURCE1):
	(cd .. && git archive --format=tar --prefix=$(PACKAGE)-$(VERSION)/ $(EXPORT_TAG)) \
	  | gzip -9 > $@

.PHONY : tarball rpm_package
