#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Setup script."""

# Copyright (c) 2019 SUSE LLC
#
# This file is part of img-downloader. img-downloader provides an api and
# command line utilities for downloading images from OBS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import find_packages, setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as req_file:
    requirements = req_file.read().splitlines()


setup(
    name='img-downloader',
    version='0.0.1',
    description="Package for downloading images from Open Build Service.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="SUSE",
    author_email='public-cloud-dev@susecloud.net',
    url='https://github.com/SUSE-Enceladus/img-downloader',
    packages=find_packages(),
    package_dir={
        'img_downloader': 'img_downloader'
    },
    entry_points={
        'console_scripts': [
            'img-downloader=img_downloader.cli:main'
        ]
    },
    include_package_data=True,
    python_requires='>=3.4',
    install_requires=requirements,
    license='GPLv3+',
    zip_safe=False,
    keywords='img-downloader img_downloader',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
