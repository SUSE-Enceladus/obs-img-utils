# Copyright (c) 2019 SUSE LLC, All rights reserved.
#
# This file is part of obs-img-downloader. obs-img-downloader provides
# an api and command line utilities for downloading images from OBS.
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

import hashlib
import logging
import os
import re

from collections import namedtuple
from distutils.dir_util import mkpath
from pkg_resources import parse_version
from tempfile import NamedTemporaryFile
from urllib.error import ContentTooShortError, URLError

from obs_img_downloader.exceptions import (
    ImageDownloadException,
    ImageDownloaderException,
    DownloadPackagesFileException,
    ImageConditionsException,
    PackageVersionException,
    ImageChecksumException,
    ImageVersionException
)
from obs_img_downloader.utils import defaults, retry
from obs_img_downloader.web_content import WebContent

extensions = {
    'azure': r'vhdfixed\.xz',
    'ec2': r'raw\.xz',
    'gce': r'tar\.gz',
    'oci': r'qcow2'
}

kiwi_version = r'(\d+\.\d+\.\d+)'
obs_build = r'(\d+\.\d+)'

package_type = namedtuple(
    'package_type', [
        'version', 'release', 'arch', 'checksum'
    ]
)

build_version = namedtuple(
    'build_version', [
        'kiwi_version', 'obs_build'
    ]
)


class ImageDownloader(object):
    """
        Implements image downloader.

        Attributes
        * :attr:`download_url`
          Buildservice URL
        * :attr:`image_name`
          Image name as specified in the KIWI XML description of the
          Buildservice project and package
        * :attr:`conditions`
          Criteria for the image build which is a list of hashes like
          the following example demonstrates:
          conditions=[
              # a package condition with version and release spec
              {
               'package_name': 'kernel-default',
               'version': '4.13.1',
               'build_id': '1.1'
              },
              # a image version condition
              {'image': '1.42.1'}
          ]
        * :attr:`arch`
          Buildservice package architecture, defaults to: x86_64
        * :attr:`download_directory`
          Download directory name, defaults to: /tmp
        """

    def __init__(
            self,
            download_url,
            image_name,
            cloud,
            conditions=None,
            arch='x86_64',
            download_directory=None,
            version_format=None,
            log_level=logging.INFO,
            log_callback=None,
            report_callback=None
    ):
        if log_callback:
            self.log_callback = log_callback
        else:
            logger = logging.getLogger('obs_img_downloader')
            logger.setLevel(log_level)
            self.log_callback = logger

        self.download_url = download_url
        self.image_name = image_name

        if cloud not in extensions.keys():
            raise ImageDownloaderException(
                '{cloud} is not supported. '
                'Valid values are azure, ec2, gce or oci'.format(
                    cloud=cloud
                )
            )
        else:
            self.cloud = cloud.lower()

        self.extension = extensions[self.cloud]
        self.arch = arch
        self.download_directory = os.path.expanduser(
            download_directory or defaults['download_dir']
        )
        self.image_metadata_name = None
        self.conditions = conditions
        self.version_format = version_format or defaults['version_format']
        self.version_format = self.version_format.format(
            kiwi_version=kiwi_version,
            obs_build=obs_build
        )

        self.remote = WebContent(self.download_url)
        self.report_callback = report_callback
        self.image_status = self._init_status()

    def _init_status(self):
        image_status = {
            'name': self.image_name,
            'job_status': 'prepared',
            'image_source': ['unknown'],
            'packages': {},
            'packages_checksum': 'unknown',
            'version': 'unknown',
            'conditions': []
        }
        if self.conditions:
            for condition in self.conditions:
                condition['status'] = None
            image_status['conditions'] = self.conditions
        return image_status

    @retry((
        ContentTooShortError,
        URLError,
        ImageDownloadException,
        ImageChecksumException
    ))
    def _download_image(self):
        """
        Download image and shasum to given file.
        """
        mkpath(self.download_directory)

        self._wait_on_image_conditions()

        regex = r''.join([
            r'^',
            self.image_metadata_name.replace('.packages', ''),
            r'\.',
            self.extension,
            r'$'
        ])

        image_file = self.remote.fetch_to_dir(
            self.image_name,
            regex,
            self.download_directory,
            self.report_callback
        )

        if not image_file:
            raise ImageDownloadException(
                'No {cloud} images found that match {regex} at {url}'.format(
                    cloud=self.cloud,
                    regex=regex,
                    url=self.download_url
                )
            )

        image_checksum = self.remote.fetch_to_dir(
            self.image_name,
            regex.replace('$', r'\.sha256$'),
            self.download_directory
        )

        if not image_checksum:
            raise ImageChecksumException(
                'No checksum file found that matches {regex} at {url}'.format(
                    regex=regex,
                    url=self.download_url
                )
            )

        image_hash = hashlib.sha256()
        with open(image_file, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b''):
                image_hash.update(byte_block)

        with open(image_checksum, 'r') as f:
            lines = f.readlines()
            expected_checksum = lines[3].strip()

        if image_hash.hexdigest() != expected_checksum:
            raise ImageChecksumException(
                'Image checksum does not match expected value'
            )

        return image_file

    def _get_build_number(self, name):
        build = re.search(self.version_format, name)

        if build:
            return build_version(
                kiwi_version=build.group(1),
                obs_build=build.group(2)
            )
        else:
            return build_version(
                kiwi_version='unknown',
                obs_build='unknown'
            )

    def _image_conditions_complied(self):
        for condition in self.image_status['conditions']:
            if condition['status'] is not True:
                return False
        return True

    def check_image_conditions(self):
        self._get_image_packages_metadata()
        self._get_image_version()

        for condition in self.image_status['conditions']:
            if 'image' in condition:
                if self.image_status['version'] == condition['image']:
                    condition['status'] = True
                else:
                    condition['status'] = False
            elif 'package_name' in condition:
                if self._lookup_package(
                        self.image_status['packages'], condition
                ):
                    condition['status'] = True
                else:
                    condition['status'] = False

        if not self._image_conditions_complied():
            raise ImageConditionsException('Image conditions not met')

    @retry(ImageConditionsException, tries=3, delay=300, backoff=1)
    def _wait_on_image_conditions(self):
        self.check_image_conditions()

    def get_image(self):
        self.image_status['image_source'] = self._download_image()
        return self.image_status['image_source']

    @retry(DownloadPackagesFileException)
    def _download_packages_file(self, packages_file_name):
        regex = r''.join([
            self.image_name,
            r'\.',
            self.arch,
            '-',
            self.version_format,
            r'\.packages'
        ])

        self.image_metadata_name = self.remote.fetch_file(
            self.image_name,
            regex,
            packages_file_name
        )

        if not self.image_metadata_name:
            raise DownloadPackagesFileException(
                'No image metadata found matching: {regex}, '
                'at {url}'.format(
                    regex=regex,
                    url=self.download_url
                )
            )

    def _get_image_version(self):
        # Extract image version information from .packages file name
        self.image_status['version'] = self._get_build_number(
            self.image_metadata_name
        ).kiwi_version

        if self.image_status['version'] == 'unknown':
            raise ImageVersionException(
                'No image version found using {formatter}. '
                'Unexpected image name format: {name}'.format(
                    formatter=self.version_format,
                    name=self.image_metadata_name
                )
            )

    def _get_image_packages_metadata(self):
        packages_file = NamedTemporaryFile()
        self._download_packages_file(packages_file.name)

        result_packages = {}
        with open(packages_file.name) as packages:
            for package in packages.readlines():
                package_digest = hashlib.md5()
                package_digest.update(package.encode())
                package_info = package.split('|')
                package_name = package_info[0]
                package_result = package_type(
                    version=package_info[2],
                    release=package_info[3],
                    arch=package_info[4],
                    checksum=package_digest.hexdigest()
                )
                result_packages[package_name] = package_result

        self.image_status['packages'] = result_packages

    def _version_compare(self, current, expected, condition):
        if condition == '>=':
            return parse_version(current) >= parse_version(expected)
        elif condition == '<=':
            return parse_version(current) <= parse_version(expected)
        elif condition == '==':
            return parse_version(current) == parse_version(expected)
        elif condition == '>':
            return parse_version(current) > parse_version(expected)
        elif condition == '<':
            return parse_version(current) < parse_version(expected)
        else:
            raise PackageVersionException(
                'Invalid version compare expression: "{0}"'.format(condition)
            )

    def _lookup_package(self, packages, condition):
        package_name = condition['package_name']

        if package_name not in packages:
            return False

        condition_eval = condition.get('condition', '>=')
        package_data = packages[package_name]

        if 'version' in condition:
            # we want to lookup a specific version
            match = self._version_compare(
                package_data.version,
                condition['version'],
                condition_eval
            )

            if not match:
                return False

        if 'build_id' in condition:
            # we want to lookup a specific build number
            match = self._version_compare(
                package_data.release,
                condition['build_id'],
                condition_eval
            )

            if not match:
                return False

        return True
