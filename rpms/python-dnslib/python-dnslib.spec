%global srcname dnslib

Name:           python-%{srcname}
Version:        0.9.14
Release:        1%{?dist}
Summary:        dnslib python module

License:        BSD
URL:            https://pypi.python.org/pypi/dnslib
Source0:        %{pypi_source}

BuildArch:      noarch

%global _description %{expand:
A library to encode/decode DNS wire-format packets supporting both
Python 2.7 and Python 3.2+.}

%description %_description

%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires:  python3-devel

%description -n python3-%{srcname} %_description

%prep
%autosetup -n %{srcname}-%{version}

%build
%py3_build

%install
%py3_install

# %check
# %{python3} setup.py test

# Note that there is no %%files section for the unversioned python module
%files -n python3-%{srcname}
%license LICENSE
%doc README
%{python3_sitelib}/%{srcname}-*.egg-info/
%{python3_sitelib}/%{srcname}/
