# Copyright (c) 2022 SUSE LLC, All rights reserved.
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

import collections
import io

from contextlib import suppress
from unittest.mock import patch, MagicMock

from obs_img_utils.utils import (
    retry,
    echo_package_json,
    echo_package_text,
    echo_packages_text,
    get_checksum_from_file,
    get_hash_from_image,
)


@retry(Exception)
def fake_method():
    raise Exception('Fail!')


@patch('obs_img_utils.utils.time')
def test_retry_decorator(mock_time):
    with suppress(Exception):
        fake_method()


def test_echo_package_text_empty():
    echo_package_text('package', {}, False)


def test_echo_package_json_empty():
    echo_package_json('package', {}, False)


def test_get_checksum_from_file():
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value = MagicMock(spec=io.IOBase)
        file_handle = mock_open.return_value.__enter__.return_value
        file_handle.readlines.return_value = ['', '', '', 'ABC1234567890']
        output = get_checksum_from_file(
            'tests/data/openSUSE-Leap-15.0-Azure'
            '.x86_64-1.0.0-Build1.133.packages'
        )

    assert output == 'ABC1234567890'


def test_get_hash_from_image():
    output = get_hash_from_image(
        'tests/data/openSUSE-Leap-15.0-Azure'
        '.x86_64-1.0.0-Build1.133.packages'
    )
    assert output.hexdigest() == \
        'f71d1050f3b3b1c02b3f420866e4539c9ab482d9a0497de4c40b9d3afbc99b55'


def test_echo_packages_text(capsys):
    headers = ["name", "version", "release", "arch", "license", "checksum"]
    Pkg_info = collections.namedtuple("Pkg_info", headers)
    pkg1 = Pkg_info(
        "zypper-lifecycle-plugin",
        "0.6.1601367426.843fe7a",
        "1.60",
        "x86_64",
        "GPL-2.0",
        "332dd2f09402e8e411184f7b27ef469c"
    )
    data = {}
    data["zypper-lifecycle-plugin"] = pkg1

    pkg2 = Pkg_info(
            "zypper",
            "1.14.55",
            "150400.3.6.1",
            "x86_64",
            "GPL-2.0-or-later",
            "595cbdc5262afb29ad1baeb155635325"
    )
    data["zypper"] = pkg2

    echo_packages_text(data, True, no_headers=False)

    captured = capsys.readouterr()

    expected_header = "name                    version                release      arch   license          checksum                        "   # noqa: E501
    expected_separator = "----------------------- ---------------------- ------------ ------ ---------------- --------------------------------"   # noqa: E501
    expected_data1 = "zypper-lifecycle-plugin 0.6.1601367426.843fe7a 1.60         x86_64 GPL-2.0          332dd2f09402e8e411184f7b27ef469c"   # noqa: E501
    expected_data2 = "zypper                  1.14.55                150400.3.6.1 x86_64 GPL-2.0-or-later 595cbdc5262afb29ad1baeb155635325"   # noqa: E501

    assert expected_header in captured.out
    assert expected_separator in captured.out
    assert expected_data1 in captured.out
    assert expected_data2 in captured.out


def test_echo_package_text(capsys):
    headers = ["name", "version", "release", "arch", "license", "checksum"]
    Pkg_info = collections.namedtuple("Pkg_info", headers)
    pkg1 = Pkg_info(
        "zypper-lifecycle-plugin",
        "0.6.1601367426.843fe7a",
        "1.60",
        "x86_64",
        "GPL-2.0",
        "332dd2f09402e8e411184f7b27ef469c"
    )
    data = {}
    data["zypper-lifecycle-plugin"] = pkg1

    pkg2 = Pkg_info(
            "zypper",
            "1.14.55",
            "150400.3.6.1",
            "x86_64",
            "GPL-2.0-or-later",
            "595cbdc5262afb29ad1baeb155635325"
    )
    data["zypper"] = pkg2

    echo_package_text("zypper", data, True, no_headers=False)

    captured = capsys.readouterr()

    expected_header = "name   version release      arch   license          checksum                        "   # noqa: E501
    expected_separator = "------ ------- ------------ ------ ---------------- --------------------------------"   # noqa: E501
    expected_data1 = "zypper 1.14.55 150400.3.6.1 x86_64 GPL-2.0-or-later 595cbdc5262afb29ad1baeb155635325"   # noqa: E501

    assert expected_header in captured.out
    assert expected_separator in captured.out
    assert expected_data1 in captured.out
