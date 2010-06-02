%define ver @VERSION@
%define rel @RELEASE@

%define basedir /opt/linuxfoundation
 
# %{version}, %{rel} are provided by the Makefile
Summary: Linux Foundation deps checker
Name: deps-checker
Version: %{ver}
Release: %{rel}
License: LF
Group: Development/Tools
Source: %{name}-%{version}.tar.gz
URL: http://bzr.linux-foundation.org/lsb/devel/deps-checker
BuildRoot: %{_tmppath}/%{name}-root
AutoReqProv: no
Requires: python-django

%description
A compliance tool to explore FOSS dependencies in binaries/libraries

#==================================================
%prep
%setup -q

#==================================================
%build
  
#==================================================
%install

rm -rf ${RPM_BUILD_ROOT}
install -d ${RPM_BUILD_ROOT}%{basedir}
cp -ar bin ${RPM_BUILD_ROOT}%{basedir}
cp -ar compliance ${RPM_BUILD_ROOT}%{basedir}
install -d ${RPM_BUILD_ROOT}%{basedir}/share/icons/hicolor/16x16/apps
install desktop/lf_small.png ${RPM_BUILD_ROOT}%{basedir}/share/icons/hicolor/16x16/apps
install -d ${RPM_BUILD_ROOT}%{basedir}/share/applications
install desktop/%{name}.desktop ${RPM_BUILD_ROOT}%{basedir}/share/applications
install -d ${RPM_BUILD_ROOT}%{basedir}/doc/%{name}
install doc/Licence ${RPM_BUILD_ROOT}%{basedir}/doc/%{name}
install -d /var/opt/linuxfoundation/log/compliance

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
    useradd -d /home/compliance -s /bin/sh -c "compliance tester login" compliance -m -g compliance >/dev/null 2>&1
    
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
  xdg-desktop-menu install /opt/linuxfoundation/share/applications/deps-checker.desktop
fi

%preun
if [ -x /usr/bin/xdg-desktop-menu ];then
  xdg-desktop-menu uninstall /opt/linuxfoundation/share/applications/deps-checker.desktop
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
%doc %{basedir}/doc/%{name}/Licence

%changelog
* Wed Jun 02 2010 Stew Benedict <stewb@linux-foundation.org>
- initial packaging
