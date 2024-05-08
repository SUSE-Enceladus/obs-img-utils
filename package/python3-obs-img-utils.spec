#
# spec file for package python3-obs-img-utils
#
# Copyright (c) 2019 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


%bcond_without test
Name:           python3-obs-img-utils
Version:        1.3.0
Release:        0
Summary:        API and CLI utilities for images in OBS
License:        GPL-3.0-or-later
Group:          Development/Languages/Python
Url:            https://github.com/SUSE-Enceladus/obs-img-utils
Source:         https://files.pythonhosted.org/packages/source/o/obs-img-utils/obs-img-utils-%{version}.tar.gz
BuildRequires:  python-rpm-macros
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-click-man
BuildRequires:  python3-click
BuildRequires:  python3-PyYAML
BuildRequires:  python3-lxml
BuildRequires:  python3-xmltodict
%if %{with test}
BuildRequires:  python3-coverage
BuildRequires:  python3-pytest
BuildRequires:  python3-pytest-cov
%endif
Requires:       python3-PyYAML
Requires:       python3-click
Requires:       python3-lxml
Requires:       python3-xmltodict
BuildArch:      noarch

%description
API and CLI utilities for images in OBS.

Provides the following commands:

- Downloading images based on conditions
- Get list of packages in an image
- Get version info for a specific package

%prep
%setup -q -n obs-img-utils-%{version}

%build
python3 setup.py build
mkdir -p man/man1
python3 setup.py --command-packages=click_man.commands man_pages --target man/man1

%install
python3 setup.py install --prefix=%{_prefix} --root=%{buildroot}
install -d -m 755 %{buildroot}/%{_mandir}/man1
install -m 644 man/man1/*.1 %{buildroot}/%{_mandir}/man1

%check
%if %{with test}
export LC_ALL=en_US.utf-8
export LANG=en_US.utf-8
python3 -m pytest --cov=obs_img_utils
%endif

%files
%defattr(-,root,root)
%license LICENSE
%doc CHANGES.md CONTRIBUTING.md README.md
%{_mandir}/man1/*
%{_bindir}/obs-img-utils
%{python3_sitelib}/*

%changelog
