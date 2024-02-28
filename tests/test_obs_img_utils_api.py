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

import pytest

from unittest.mock import patch

from obs_img_utils.api import OBSImageUtil, package_type
from obs_img_utils.exceptions import PackageVersionExceptionOBS


class TestAPI:
    def setup_method(self, cls):
        self.downloader = OBSImageUtil(
            'https://provo-mirror.opensuse.org/repositories/',
            'openSUSE-Leap-15.0-Azure',
            arch='x86_64',
            target_directory='tests/data'
        )

    def test_version_compare(self):
        result = self.downloader._version_compare('1.0', '2.0', '<=')
        assert result

        result = self.downloader._version_compare('1.0', '1.0', '==')
        assert result

        result = self.downloader._version_compare('1.1', '1.0', '>')
        assert result

        result = self.downloader._version_compare('1.0', '2.0', '<')
        assert result

        with pytest.raises(PackageVersionExceptionOBS):
            self.downloader._version_compare('2.0', '1.0', '===')

    @patch.object(OBSImageUtil, '_get_image_checksum')
    @patch('obs_img_utils.api.time')
    def test_wait_for_new_image(self, mock_time, mock_get_checksum):
        self.downloader.image_checksum = 'ABC12345678890'
        mock_get_checksum.return_value = '12345678890ABC'
        self.downloader.wait_for_new_image()

    def test_lookup_package(self):
        packages = {'fake'}
        condition = {'package_name': 'test', 'version': '1.0'}

        # Package does not exist
        result = self.downloader._lookup_package(packages, condition)
        assert result is False

        package = package_type(
            name='test',
            version='0.2',
            release='1.1',
            arch='x86_64',
            license='MIT',
            checksum='ABC1234567890'
        )
        packages = {'test': package}

        # Version mismatch
        result = self.downloader._lookup_package(packages, condition)
        assert result is False

        condition = {'package_name': 'test', 'release': '1.2'}

        # release mismatch
        result = self.downloader._lookup_package(packages, condition)
        assert result is False
