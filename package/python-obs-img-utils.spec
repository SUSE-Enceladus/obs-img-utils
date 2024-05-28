#
# spec file for package python-obs-img-utils
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

%define upstream_name obs-img-utils
%define python python
%{?sle15_python_module_pythons}
%bcond_without test

%if 0%{?suse_version} > 1500
%bcond_without libalternatives
%else
%bcond_with libalternatives
%endif

Name:           python-obs-img-utils
Version:        1.4.0
Release:        0
Summary:        API and CLI utilities for images in OBS
License:        GPL-3.0-or-later
Group:          Development/Languages/Python
Url:            https://github.com/SUSE-Enceladus/obs-img-utils
Source:         https://files.pythonhosted.org/packages/source/o/obs-img-utils/obs-img-utils-%{version}.tar.gz
BuildRequires:  python-rpm-macros
BuildRequires:  fdupes
BuildRequires:  %{python_module devel}
BuildRequires:  %{python_module pip}
BuildRequires:  %{python_module setuptools}
BuildRequires:  %{python_module wheel}
BuildRequires:  %{python_module click-man}
BuildRequires:  %{python_module click}
BuildRequires:  %{python_module PyYAML}
BuildRequires:  %{python_module lxml}
BuildRequires:  %{python_module xmltodict}
%if %{with test}
BuildRequires:  %{python_module pytest}
%endif
Requires:       python-PyYAML
Requires:       python-click
Requires:       python-lxml
Requires:       python-xmltodict

%if %{with libalternatives}
BuildRequires:  alts
Requires:       alts
%else
Requires(post): update-alternatives
Requires(postun): update-alternatives
%endif

BuildArch:      noarch
Provides:       python3-obs-img-utils = %{version}
Obsoletes:      python3-obs-img-utils < %{version}
%python_subpackages

%description
API and CLI utilities for images in OBS.

Provides the following commands:

- Downloading images based on conditions
- Get list of packages in an image
- Get version info for a specific package

%prep
%autosetup -n obs-img-utils-%{version}

%build
%pyproject_wheel
mkdir -p man/man1
%python_exec setup.py --command-packages=click_man.commands man_pages --target man/man1

%install
%pyproject_install
install -d -m 755 %{buildroot}/%{_mandir}/man1
install -m 644 man/man1/*.1 %{buildroot}/%{_mandir}/man1
%python_clone -a %{buildroot}%{_bindir}/obs-img-utils
%{python_expand %fdupes %{buildroot}%{$python_sitelib}}

%pre
%python_libalternatives_reset_alternative obs-img-utils

%post
%{python_install_alternative obs-img-utils}

%postun
%{python_uninstall_alternative obs-img-utils}

%check
%if %{with test}
export LC_ALL=en_US.utf-8
export LANG=en_US.utf-8
%pytest
%endif

%files %{python_files}
%defattr(-,root,root)
%license LICENSE
%doc CHANGES.md CONTRIBUTING.md README.md
%{_mandir}/man1/*
%python_alternative %{_bindir}/obs-img-utils
%{python_sitelib}/*

%changelog
