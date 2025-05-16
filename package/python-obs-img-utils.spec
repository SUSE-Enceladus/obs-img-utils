#
# spec file for package python-obs-img-utils
#
# Copyright (c) 2025 SUSE LLC
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
%if 0%{?suse_version} >= 1600
%define pythons %{primary_python}
%else
%{?sle15_python_module_pythons}
%endif
%global _sitelibdir %{%{pythons}_sitelib}

Name:           python-obs-img-utils
Version:        1.7.0
Release:        0
Summary:        API and CLI utilities for images in OBS
License:        GPL-3.0-or-later
Group:          Development/Languages/Python
Url:            https://github.com/SUSE-Enceladus/obs-img-utils
Source:         https://files.pythonhosted.org/packages/source/o/obs-img-utils/obs-img-utils-%{version}.tar.gz
BuildRequires:  python-rpm-macros
BuildRequires:  fdupes
BuildRequires:  %{pythons}-devel
BuildRequires:  %{pythons}-packaging
BuildRequires:  %{pythons}-pip
BuildRequires:  %{pythons}-setuptools
BuildRequires:  %{pythons}-wheel
BuildRequires:  %{pythons}-click-man
BuildRequires:  %{pythons}-click
BuildRequires:  %{pythons}-PyYAML
BuildRequires:  %{pythons}-lxml
BuildRequires:  %{pythons}-xmltodict
%if %{with test}
BuildRequires:  %{pythons}-pytest
%endif
Requires:       %{pythons}-PyYAML
Requires:       %{pythons}-click
Requires:       %{pythons}-lxml
Requires:       %{pythons}-xmltodict
Requires:       %{pythons}-packaging

BuildArch:      noarch
Provides:       python3-obs-img-utils = %{version}
Obsoletes:      python3-obs-img-utils < %{version}

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
%fdupes %{buildroot}%{_sitelidir}

%check
%if %{with test}
export LC_ALL=en_US.utf-8
export LANG=en_US.utf-8
%pytest
%endif

%files
%defattr(-,root,root)
%license LICENSE
%doc CHANGES.md CONTRIBUTING.md README.md
%{_mandir}/man1/*
%{_bindir}/obs-img-utils
%{_sitelibdir}/obs_img_utils/
%{_sitelibdir}/obs_img_utils-*.dist-info/

%changelog
