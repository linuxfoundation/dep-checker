%define ver @VERSION@
%define rel @RELEASE@
%define django_ver @DJANGO_VERSION@

%define basedir /opt/linuxfoundation

# optionally bundle django
%define bundle_django 0
%{?_with_django: %{expand: %%global bundle_django 1}}
%{?_without_django: %{expand: %%global bundle_django 0}}
%if !%bundle_django
%endif
 
# %{version}, %{rel} are provided by the Makefile
Summary: Dependency Checker Tool
Name: dep-checker
Version: %{ver}
Release: %{rel}
License: LF
Group: Development/Tools
Source: %{name}-%{version}.tar.gz
%if %bundle_django
Source1: Django-%{django_ver}.tar.gz
%endif
URL: http://git.linux-foundation.org/dep-checker.git
BuildRoot: %{_tmppath}/%{name}-root
AutoReqProv: no
%if !%bundle_django
Requires: python-django
%endif
BuildRequires: python w3m

%description
A compliance tool to explore FOSS dependencies in binaries/libraries

If you don't get a menu entry, run the app with:
	%{basedir}/bin/dep-checker.py start

If a browser window or tab doesn't open, goto:
	http://127.0.0.1:8000/linkage

The command-line tool is: 
	%{basedir}/readelf.py

Note: This package can be built with django bundled, using '--with django'

#==================================================
%prep
%setup -q

#==================================================
%build
make
  
#==================================================
%install

rm -rf ${RPM_BUILD_ROOT}
install -d ${RPM_BUILD_ROOT}%{basedir}
cp -ar bin ${RPM_BUILD_ROOT}%{basedir}
cp -ar compliance ${RPM_BUILD_ROOT}%{basedir}
find ${RPM_BUILD_ROOT}%{basedir} -name '*.pyc' | xargs rm -f
rm -f ${RPM_BUILD_ROOT}%{basedir}/compliance/media/docs/*
install -m 644 compliance/media/docs/*.html ${RPM_BUILD_ROOT}%{basedir}/compliance/media/docs
install -d ${RPM_BUILD_ROOT}%{basedir}/share/icons/hicolor/16x16/apps
install -m 644 desktop/lf_small.png ${RPM_BUILD_ROOT}%{basedir}/share/icons/hicolor/16x16/apps
install -d ${RPM_BUILD_ROOT}%{basedir}/share/applications
install -m 644 desktop/%{name}.desktop ${RPM_BUILD_ROOT}%{basedir}/share/applications
install -d ${RPM_BUILD_ROOT}%{basedir}/doc/%{name}
install -m 644 doc/LICENSE doc/Contributing ${RPM_BUILD_ROOT}%{basedir}/doc/%{name}
install -m 644 AUTHORS Changelog README.txt README.apache-mod_wsgi ${RPM_BUILD_ROOT}%{basedir}/doc/%{name}
install -d ${RPM_BUILD_ROOT}/var%{basedir}/log/compliance
%if %bundle_django
  tar -xf %{SOURCE1}
  cp -ar Django-%{django_ver}/django ${RPM_BUILD_ROOT}%{basedir}/compliance
%endif

#==================================================
%clean
if [ -z "${RPM_BUILD_ROOT}"  -a "${RPM_BUILD_ROOT}" != "/" ]; then 
    rm -rf ${RPM_BUILD_ROOT}
fi

#==================================================
%pre
PATH=/usr/sbin:$PATH
groupadd compliance >/dev/null 2>&1 || true

id compliance >/dev/null 2>&1

if [ $? -ne 0 ]; then 
    useradd -d /home/compliance -s /bin/sh -p "" -c "compliance tester login" compliance -m -g compliance >/dev/null 2>&1
    
    if [ $? = 0 ]; then
        echo
    else
        echo "Failed to add user 'compliance'."
        echo "To be able to run the tests you should add this user manually."
        exit 1
    fi
fi

%post
if [ -x /usr/bin/xdg-desktop-menu ];then
  xdg-desktop-menu install /opt/linuxfoundation/share/applications/dep-checker.desktop
fi
%if %bundle_django
if [ ! -e %{basedir}/bin/django ];then
  cd %{basedir}/bin
  ln -sf ../compliance/django .
fi
%endif

%preun
if [ -x /usr/bin/xdg-desktop-menu ];then
  xdg-desktop-menu uninstall /opt/linuxfoundation/share/applications/dep-checker.desktop
fi

%postun
# don't mess with things on an upgrade, or if janitor is installed
if [ "$1" = "0" -a ! -f %{basedir}/bin/code-janitor.py ];then
    TESTER=compliance
    id $TESTER > /dev/null 2>/dev/null
    if [ $? -eq 0 ]; then
	userdel -r $TESTER > /dev/null 2>/dev/null
	if [ $? = 0 ]; then
		echo "User '$TESTER' was successfully deleted"
	else
		echo "Warning: failed to delete user '$TESTER'"
	fi
    fi

    TESTGROUP=compliance
    cat /etc/group | grep ^$TESTGROUP: > /dev/null 2>/dev/null
    if [ $? -eq 0 ]; then
	groupdel $TESTGROUP > /dev/null 2>/dev/null
	if [ $? = 0 ]; then
		echo "Group '$TESTGROUP' was successfully deleted."
	else
		echo "Warning: failed to delete group '$TESTGROUP'."
	fi
    fi
%if %bundle_django
    if [ -d %{basedir}/janitor/django ];then
        cd %{basedir}/bin
        ln -sf ../janitor/django .
    fi
%endif
fi

#==================================================
%files
%defattr(-,compliance,compliance)

%dir %{basedir}/bin
%dir %{basedir}/doc/%{name}
%dir %{basedir}/compliance
%dir %{basedir}/share/applications
%dir %{basedir}/share/icons/hicolor/16x16/apps
%dir /var/%{basedir}/log/compliance

%{basedir}/bin/*
%{basedir}/compliance/*
%{basedir}/share/icons/hicolor/16x16/apps/*
%{basedir}/share/applications/*
%doc %{basedir}/doc/%{name}/*

%changelog
* Fri Jun 25 2010 Jeff Licquia <licquia@linuxfoundation.org>
- move static checking db into the regular compliance db

* Thu Jun 24 2010 Jeff Licquia <licquia@linuxfoundation.org>
- switch to git from bzr for version control

* Mon Jun 07 2010 Jeff Licquia <licquia@linuxfoundation.org>
- add static checking database

* Fri Jun 04 2010 Stew Benedict <stewb@linux-foundation.org>
- fix compliance user/group setup for upgrade, v0.0.3
- add README.html s/Licence/License/

* Wed Jun 02 2010 Stew Benedict <stewb@linux-foundation.org>
- initial packaging
