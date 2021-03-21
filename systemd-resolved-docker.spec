%global srcname systemd-resolved-docker
%global eggname systemd_resolved_docker

Name:           %{srcname}
Version:        0.2.1
Release:        1%{?dist}
Summary:        systemd-resolved and docker DNS integration

License:        MIT
URL:            https://github.com/flaktack/systemd-resolved-docker
# Sources can be obtained by
# git clone https://github.com/flaktack/systemd-resolved-docker
# cd systemd-resolved-docker
# tito build --tgz
Source0:        %{srcname}-%{version}.tar.gz
Source1:        %{srcname}.service
Source2:        %{srcname}.sysconfig

BuildArch:      noarch

%if 0%{?el6}
BuildRequires: python34-devel
BuildRequires: python34-setuptools
%else
BuildRequires: python3-devel
BuildRequires: python3-setuptools
%endif
BuildRequires: systemd-rpm-macros

%description
Provides systemd-resolved and docker DNS integration.

A DNS server is configured to listen on each docker interface's IP address. This is used to:
1. expose the systemd-resolved DNS service (127.0.0.53) to docker containers by proxying DNS requests, since the systems
   loopback IPs can't be accessed from containers.
2. adds the created DNS servers to the docker interface using systemd-resolved so that docker containers may be
   referenced by hostname. This uses --hostname and --domainname, --network or a default of .docker to create the domains.

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
%files
%doc README.md
%{python3_sitelib}/%{eggname}-*.egg-info/
%{python3_sitelib}/%{eggname}/
%{_bindir}/%{srcname}
%{_unitdir}/%{srcname}.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{srcname}

#-- CHANGELOG -----------------------------------------------------------------#
	
%changelog
* Sun Mar 21 2021 Zsombor Welker 0.2.1-1
- Restart the service whenever docker/systemd-resolved is restarted

* Sun Mar 21 2021 Zsombor Welker 0.2.0-1
- Clarify domain name generating logic

* Fri Mar 19 2021 Zsombor Welker <fedora@zdeqb.com> 0.1.1-1
- Cleanup README and spec

* Fri Mar 19 2021 Zsombor Welker <fedora@zdeqb.com> 0.1.0-1
- Initial Version
