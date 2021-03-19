%global srcname systemd-resolved-docker
%global eggname systemd_resolved_docker

Name:           python-%{srcname}
Version:        0.1.0
Release:        1%{?dist}
Summary:        systemd-resolved and docker DNS integration

License:        BSD
URL:            https://pypi.python.org/pypi/systemd_resolved_docker
#Source0:        ${pypi_source}
Source0:        %{srcname}-%{version}.tar.gz
Source1:        %{srcname}.service
Source2:        %{srcname}.sysconfig

BuildArch:      noarch

%global _description %{expand:
systemd-resolved and docker DNS integration}

%description %_description

%package -n python3-%{srcname}
Summary:        %{summary}
%if 0%{?el6}
BuildRequires: python34-devel
BuildRequires: python34-setuptools
%else
BuildRequires: python3-devel
BuildRequires: python3-setuptools
%endif
BuildRequires: systemd-rpm-macros

%description -n python3-%{srcname} %_description

#-- PREP, BUILD & INSTALL -----------------------------------------------------#
%prep
%autosetup -n %{srcname}-%{version}

%build
%py3_build

%install
%py3_install

# SystemdD services
install -dp %{buildroot}%{_unitdir}
install -p -m 644 %{SOURCE1} %{buildroot}%{_unitdir}

# Sysconfig
install -dp %{buildroot}%{_sysconfdir}/sysconfig
install -p -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/%{srcname}

# %%check
# %%{python3} setup.py test

%post
%systemd_post %{srcname}.service

%preun
%systemd_preun %{srcname}.service

%postun
%systemd_postun_with_restart %{srcname}.service


#-- FILES ---------------------------------------------------------------------#
# Note that there is no %%files section for the unversioned python module
%files -n python3-%{srcname}
%doc README.md
%{python3_sitelib}/%{eggname}-*.egg-info/
%{python3_sitelib}/%{eggname}/
%{_bindir}/%{srcname}
%{_unitdir}/%{srcname}.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{srcname}

#-- CHANGELOG -----------------------------------------------------------------#
	
%changelog
* Fri Mar 19 2021 Zsombor Welker <fedora@zdeqb.com> 0.1.0-1
- Initial Version

