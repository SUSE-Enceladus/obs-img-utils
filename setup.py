#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Setup script."""

# Copyright (c) 2019 SUSE LLC, All rights reserved.
#
# This file is part of obs-img-utils. obs-img-utils provides
# an api and command line utilities for images in OBS.
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

with open('requirements-test.txt') as req_file:
    test_requirements = req_file.read().splitlines()[2:]

with open('requirements-dev.txt') as req_file:
    dev_requirements = test_requirements + req_file.read().splitlines()[2:]


setup(
    name='obs-img-utils',
    version='0.2.0',
    description="Package provides utils for images in Open Build Service.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="SUSE",
    author_email='public-cloud-dev@susecloud.net',
    url='https://github.com/SUSE-Enceladus/obs-img-utils',
    packages=find_packages(),
    package_dir={
        'obs_img_utils': 'obs_img_utils'
    },
    entry_points={
        'console_scripts': [
            'obs-img-utils=obs_img_utils.cli:main'
        ]
    },
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,
        'test': test_requirements
    },
    license='GPLv3+',
    zip_safe=False,
    keywords='obs-img-utils obs_img_utils',
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
