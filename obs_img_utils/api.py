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

import hashlib
import fnmatch
import logging
import os
import re
import time

from collections import namedtuple
from distutils.dir_util import mkpath
from pkg_resources import parse_version
from tempfile import NamedTemporaryFile
from urllib.error import ContentTooShortError, URLError

from obs_img_utils.exceptions import (
    OBSImageDownloadException,
    DownloadPackagesFileExceptionOBS,
    OBSImageConditionsException,
    PackageVersionExceptionOBS,
    OBSImageChecksumException,
    OBSImageVersionException
)
from obs_img_utils.utils import (
    defaults,
    retry,
    get_hash_from_image,
    get_checksum_from_file,
    extensions,
    checksum_extensions
)
from obs_img_utils.web_content import WebContent

version_match = r'(.*)'
kiwi_version_match = r'(\d+\.\d+\.\d+)'

package_type = namedtuple(
    'package_type', [
        'version', 'release', 'arch', 'license', 'checksum'
    ]
)

build_version = namedtuple(
    'build_version', [
        'kiwi_version', 'obs_build'
    ]
)


class OBSImageUtil(object):
    """
    Implements image downloader.
    """
    def __init__(
        self,
        download_url,
        image_name,
        conditions=None,
        arch='x86_64',
        target_directory=None,
        profile=None,
        log_level=logging.INFO,
        conditions_wait_time=0,
        log_callback=None,
        report_callback=None,
        checksum_extension=None,
        extension=None,
        filter_licenses=None,
        filter_packages=None
    ):
        if log_callback:
            self.log_callback = log_callback
        else:
            logger = logging.getLogger('obs_img_utils')
            logger.setLevel(log_level)
            self.log_callback = logger

        self.download_url = download_url
        self.image_name = image_name
        self.conditions_wait_time = conditions_wait_time

        self.arch = arch
        self.target_directory = os.path.expanduser(
            target_directory or defaults['target_dir']
        )
        self.image_metadata_name = None
        self.image_checksum = None
        self.conditions = conditions
        self.filter_licenses = filter_licenses if filter_licenses else []
        self.filter_packages = filter_packages if filter_packages else []

        if checksum_extension:
            self.checksum_extensions = [checksum_extension]
        else:
            self.checksum_extensions = checksum_extensions

        if extension:
            self.extensions = [extension]
        else:
            self.extensions = extensions

        if profile:
            self.version_format = ''.join([
                kiwi_version_match,
                '-',
                profile,
                '-',
                'Build',
                version_match
            ])
        else:
            self.version_format = ''.join([
                kiwi_version_match,
                '-',
                'Build',
                version_match
            ])

        self.base_regex = r''.join([
            r'^',
            self.image_name,
            r'\.',
            self.arch,
            '-',
            self.version_format
        ])

        self.remote = WebContent(self.download_url)
        self.report_callback = report_callback
        self.image_status = self._init_status()

    def _init_status(self):
        image_status = {
            'name': self.image_name,
            'job_status': 'prepared',
            'image_source': 'unknown',
            'packages': {},
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
            OBSImageDownloadException,
            OBSImageChecksumException
    ))
    def _download_image(self):
        """
        Download image and shasum to given file.
        """
        mkpath(self.target_directory)

        self._wait_on_image_conditions()

        self.log_callback.debug(
            'Fetching image {name} from {url}'.format(
                name=self.image_name,
                url=self.download_url
            )
        )
        name = self.image_metadata_name.replace('.packages', '')
        image_file = self.remote.fetch_to_dir(
            name,
            self.base_regex,
            self.target_directory,
            self.extensions,
            self.report_callback
        )

        if not image_file:
            raise OBSImageDownloadException(
                'No images found that match {name} at {url}'.format(
                    name=name,
                    url=self.download_url
                )
            )

        expected_checksum = self._get_image_checksum(name)

        image_hash = get_hash_from_image(image_file)

        if image_hash.hexdigest() != expected_checksum:
            raise OBSImageChecksumException(
                'Image checksum does not match expected value'
            )

        self.image_checksum = expected_checksum
        self.image_status['image_source'] = image_file

    def _get_image_checksum(self, name=None):
        self.log_callback.debug('Fetching image checksum')
        name = name if name else self.image_name

        image_checksum = self.remote.fetch_to_dir(
            name,
            self.base_regex,
            self.target_directory,
            self.checksum_extensions
        )

        if not image_checksum:
            raise OBSImageChecksumException(
                'No checksum found that matches image {name} at {url}'.format(
                    name=name,
                    url=self.download_url
                )
            )

        expected_checksum = get_checksum_from_file(image_checksum)
        return expected_checksum

    def _get_build_number(self, name):
        regex = r''.join([
            self.base_regex,
            r'\.packages$'
        ])
        build = re.search(regex, name)

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
        self.image_status['packages'] = self.get_image_packages_metadata()

        version = self._get_image_version()
        self.image_status['version'] = version.kiwi_version
        self.image_status['release'] = version.obs_build

        for condition in self.image_status['conditions']:
            if 'package_name' in condition:
                if self._lookup_package(
                    self.image_status['packages'], condition
                ):
                    condition['status'] = True
                else:
                    condition['status'] = False
            else:
                if self._check_version_and_build_condition(
                    condition,
                    self.image_status['release'],
                    self.image_status['version'],
                    self.image_name
                ):
                    condition['status'] = True
                else:
                    condition['status'] = False

        if not self._image_conditions_complied():
            raise OBSImageConditionsException('Image conditions not met')

    def check_license_conditions(self):
        for package, pkg_data in self.image_status['packages'].items():
            if pkg_data.license in self.filter_licenses:
                raise OBSImageConditionsException(
                    'Package(s) found in the image that match '
                    'dis-allowed licenses. A full list can be provided'
                    ' using "obs-img-utils packages list '
                    '--filter-licenses"'.format(
                        name=package,
                        license=pkg_data.license
                    )
                )

    def _wait_on_image_conditions(self):
        start = time.time()
        end = start + self.conditions_wait_time

        while True:
            try:
                self.check_image_conditions()
                self.check_license_conditions()
                self.check_invalid_packages()
                break
            except OBSImageConditionsException as error:
                if time.time() < end:
                    wait = min(150, self.conditions_wait_time)
                    self.log_callback.warning(
                        '{error}, retrying in {wait} seconds...'.format(
                            error=error,
                            wait=wait
                        )
                    )
                    time.sleep(wait)
                else:
                    raise

    @retry((
            ContentTooShortError,
            URLError,
            OBSImageChecksumException
    ))
    def wait_for_new_image(self):
        self.log_callback.debug('Waiting for new image')

        while True:
            latest_checksum = self._get_image_checksum()
            if self.image_checksum != latest_checksum:
                return

            time.sleep(60)

    def get_image(self):
        self._download_image()
        return self.image_status['image_source']

    @retry(DownloadPackagesFileExceptionOBS)
    def _download_packages_file(self, packages_file_name):
        regex = r''.join([
            self.base_regex,
            r'\.packages$'
        ])

        self.log_callback.debug(
            'Fetching packages file for image {name} from {url}'.format(
                name=self.image_name,
                url=self.download_url
            )
        )
        self.image_metadata_name = self.remote.fetch_file(
            self.image_name,
            regex,
            packages_file_name
        )

        if not self.image_metadata_name:
            raise DownloadPackagesFileExceptionOBS(
                'No image metadata found matching: {regex}, '
                'at {url}'.format(
                    regex=regex,
                    url=self.download_url
                )
            )

    def _get_image_version(self):
        # Extract image version information from .packages file name
        version = self._get_build_number(
            self.image_metadata_name
        )

        if version.kiwi_version == 'unknown':
            raise OBSImageVersionException(
                'No image version found using {formatter}. '
                'Unexpected image name format: {name}'.format(
                    formatter=self.version_format,
                    name=self.image_metadata_name
                )
            )

        self.log_callback.debug(
            'Image version is {version}'.format(
                version=version.kiwi_version
            )
        )

        return version

    def get_image_packages_metadata(self):
        packages_file = NamedTemporaryFile()
        self._download_packages_file(packages_file.name)

        result_packages = {}
        with open(packages_file.name) as packages:
            for package in packages.readlines():
                # Packages file format:
                # name|{empty}|version|release|arch|uri|license
                package_digest = hashlib.md5()
                package_digest.update(package.encode())
                package_info = package.split('|')
                package_name = package_info[0]

                try:
                    # license is optional in packages file
                    package_license = package_info[6].strip()
                except IndexError:
                    package_license = 'unknown'

                package_result = package_type(
                    version=package_info[2],
                    release=package_info[3],
                    arch=package_info[4],
                    license=package_license,
                    checksum=package_digest.hexdigest()
                )
                result_packages[package_name] = package_result

        return result_packages

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
            raise PackageVersionExceptionOBS(
                'Invalid version compare expression: "{0}"'.format(condition)
            )

    def _lookup_package(self, packages, condition):
        package_name = condition['package_name']

        if package_name not in packages:
            self.log_callback.info(
                'Package {name} not in image'.format(name=package_name)
            )
            return False

        package_data = packages[package_name]
        return self._check_version_and_build_condition(
            condition,
            package_data.release,
            package_data.version,
            package_name
        )

    def check_invalid_packages(self):
        for package_name in self.filter_packages:
            if fnmatch.filter(self.image_status['packages'], package_name):
                raise OBSImageConditionsException(
                    'Package(s) matching {name} found in image. '
                    'A full list of packages can be provided using '
                    ' "obs-img-utils packages list '
                    '--filter-packages"'.format(
                        name=package_name
                    )
                )

    def _check_version_and_build_condition(
        self,
        condition,
        current_release,
        current_version,
        name
    ):
        condition_eval = condition.get('condition', '>=')

        if 'version' in condition:
            # we want to lookup a specific version
            match = self._version_compare(
                current_version,
                condition['version'],
                condition_eval
            )

            if not match:
                self.log_callback.info(
                    'Version condition failed: '
                    '{name} {cur_version} {eval} {exp_version}'.format(
                        name=name,
                        cur_version=current_version,
                        eval=condition_eval,
                        exp_version=condition['version']
                    )
                )
                return False

        if 'release' in condition:
            # we want to lookup a specific release number
            match = self._version_compare(
                current_release,
                condition['release'],
                condition_eval
            )

            if not match:
                self.log_callback.info(
                    'Release condition failed: '
                    '{name} {cur_release} {eval} {exp_release}'.format(
                        name=name,
                        cur_release=current_release,
                        eval=condition_eval,
                        exp_release=condition['release']
                    )
                )
                return False

        return True
