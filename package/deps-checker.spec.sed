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
cp -ar bin ${RPM_BUILD_ROOT}%{basedir}
cp -ar compliance ${RPM_BUILD_ROOT}%{basedir}
install -d ${RPM_BUILD_ROOT}%{basedir}/doc/%{name}
install doc/License ${RPM_BUILD_ROOT}%{basedir}/doc/%{name}

#==================================================
%clean
if [ -z "${RPM_BUILD_ROOT}"  -a "${RPM_BUILD_ROOT}" != "/" ]; then 
    rm -rf ${RPM_BUILD_ROOT}
fi

#==================================================
%files
%defattr(-,root,root)

%dir %{basedir}/bin
%dir %{basedir}/doc/%{name}
%dir %{basedir}/compliance
%{basedir}/bin/*
%{basedir}/compliance/*
%doc %{basedir}/doc/%{name}/License

%changelog
* Wed Jun 02 2010 Stew Benedict <stewb@linux-foundation.org>
- initial packaging
