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

import io

from contextlib import suppress
from unittest.mock import patch, MagicMock

from obs_img_utils.utils import (
    retry,
    echo_package,
    get_checksum_from_file,
    get_hash_from_image
)


@retry(Exception)
def fake_method():
    raise Exception('Fail!')


@patch('obs_img_utils.utils.time')
def test_retry_decorator(mock_time):
    with suppress(Exception):
        fake_method()


def test_echo_package():
    echo_package('package', {}, False)


def test_get_checksum_from_file():
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value = MagicMock(spec=io.IOBase)
        file_handle = mock_open.return_value.__enter__.return_value
        file_handle.readlines.return_value = ['', '', '', 'ABC1234567890']
        output = get_checksum_from_file('tests/data/packages')

    assert output == 'ABC1234567890'


def test_get_hash_from_image():
    output = get_hash_from_image('tests/data/packages')
    assert output.hexdigest() == \
        'f71d1050f3b3b1c02b3f420866e4539c9ab482d9a0497de4c40b9d3afbc99b55'
