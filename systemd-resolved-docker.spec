%global srcname systemd-resolved-docker
%global eggname systemd_resolved_docker

Name:           %{srcname}
Version:        1.0.0
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
* Mon Jul 04 2022 Zsombor Welker <fedora@zdeqb.com> 1.0.0-1
 -  Support for docker compose projects
 -  Use a dummy interface (`srd-dummy`) for integrating with systemd-resolved so that DNS resolving works if the `docker0` interfaces is `DOWN`
 -  Add handling for the host network using `DEFAULT_HOST_IP`
 -  Allow specifying both the listen IPs and ports explicitly
 -  Use `SetLinkDNSEx()` where possible so that ports other then 53 may be used
 -  Add support for wildcard `--hostname` values
 -  Don't allow top-level only domains in `ALLOWED_DOMAINS`
 -  Automatically `DEFAULT_DOMAIN` to `ALLOWED_DOMAINS` if it is not present
 -  Add integration tests and GitHub Actions
* Sun Jun 26 2022 Zsombor Welker <fedora@zdeqb.com> 0.5.0-1
- Generate names for docker-compose projects
- Don't allow top-level only domains in ALLOWED_DOMAINS
- Add the DEFAULT_DOMAIN to ALLOWED_DOMAINS if it is not contained
- Add explicit handling for the host network using DEFAULT_HOST_IP
- Create a dummy interface to intergate with systemd-resolved
- Allow specifying both the listen IPs and ports
- Use SetLinkDNSEx so that the ip:port may be specified
- Add support for wildcard domains
- Add integration tests and Github Actions
* Sun Apr 25 2021 Zsombor Welker <fedora@zdeqb.com> 0.4.0-1
- Document unmanaging the docker0 interface
- Explicitly disable DNSSEC in systemd-resolved
- Use an explicit prefix check for container ids

* Sun Mar 21 2021 Zsombor Welker 0.3.0-1
- Only return NXDOMAIN of no records exist for a domain

* Sun Mar 21 2021 Zsombor Welker 0.2.1-1
- Restart the service whenever docker/systemd-resolved is restarted

* Sun Mar 21 2021 Zsombor Welker 0.2.0-1
- Clarify domain name generating logic

* Fri Mar 19 2021 Zsombor Welker <fedora@zdeqb.com> 0.1.1-1
- Cleanup README and spec

* Fri Mar 19 2021 Zsombor Welker <fedora@zdeqb.com> 0.1.0-1
- Initial Version
