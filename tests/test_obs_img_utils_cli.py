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

import json

from obs_img_utils.api import OBSImageUtil, WebContent
from obs_img_utils.cli import main
from obs_img_utils.exceptions import DownloadMetadataFileExceptionOBS

from click.testing import CliRunner

from unittest.mock import MagicMock, patch

import pytest

urlopen_response = (
    b'<a href="openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.133.packages">'
    b'openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.13..&gt;</a>'
    b'<a href="openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.133.vhdfixed.xz">'
    b'openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.13..&gt;</a>'
    b'<a href="openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.133.'
    b'vhdfixed.xz.sha256">'
    b'openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.13..&gt;</a>'
)


def test_cli_main_help():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'The command line interface provides obs ' \
           'image utilities.' in result.output


@pytest.mark.parametrize(
    "endpoint,value",
    [('download',
      'Download image from OBS repository specified by `download-url`'),
     ('packages',
      'Package commands')],
    ids=['obs-img-utils-download', 'obs-img-utils-packages']
)
def test_cli_subcommand_help(endpoint, value):
    runner = CliRunner()
    result = runner.invoke(main, [endpoint, '--help'])
    assert result.exit_code == 0
    assert value in result.output


@patch('obs_img_utils.web_content.urlopen')
@patch.object(WebContent, 'fetch_to_dir')
def test_packages_list(mock_fetch_file, mock_url_open):
    mock_fetch_file.return_value = 'tests/data/report'

    location = MagicMock()
    location.read.return_value = urlopen_response
    mock_url_open.return_value = location

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            'packages', 'list',
            '--filter-licenses',
            '--image-name', 'openSUSE-Leap-15.0-Azure',
            '--download-url',
            'https://provo-mirror.opensuse.org/repositories/'
            'Cloud:/Images:/Leap_15.0/images/',
            '--target-dir', 'tests/data',
            '--output', 'json'
        ],
        input='y\n'
              'MIT\n'
              'n\n'
    )
    assert result.exit_code == 0

    data = result.output.split('\n')
    data = json.loads(''.join(data[3:]))

    assert 'apparmor-parser' in data
    assert data['apparmor-parser']['version'] == '2.12.2'
    assert data['apparmor-parser']['release'] == 'lp150.6.14.1'
    assert data['apparmor-parser']['arch'] == 'x86_64'


@patch.object(OBSImageUtil, 'parse_report_file')
@patch('obs_img_utils.web_content.urlopen')
@patch.object(WebContent, 'fetch_to_dir')
def test_filter_packages_list(
    mock_fetch_file,
    mock_url_open,
    mock_parse_report_file
):
    mock_parse_report_file.side_effect = DownloadMetadataFileExceptionOBS(
        'Not found!'
    )

    mock_fetch_file.return_value = \
        'tests/data/openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.133.packages'

    location = MagicMock()
    location.read.return_value = urlopen_response
    mock_url_open.return_value = location

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            'packages', 'list',
            '--filter-packages',
            '--image-name', 'openSUSE-Leap-15.0-Azure',
            '--download-url',
            'https://provo-mirror.opensuse.org/repositories/'
            'Cloud:/Images:/Leap_15.0/images/',
            '--target-dir', 'tests/data',
            "--output", "json"
        ],
        input='y\n'
              'apparmor-parser\n'
              'n\n'
    )
    assert result.exit_code == 0

    data = result.output.split('\n')
    data = json.loads(''.join(data[3:]))

    assert 'apparmor-parser' in data
    assert data['apparmor-parser']['version'] == '2.12.2'
    assert data['apparmor-parser']['release'] == 'lp150.6.14.1'
    assert data['apparmor-parser']['arch'] == 'x86_64'


@patch.object(OBSImageUtil, 'parse_report_file')
@patch('obs_img_utils.web_content.urlopen')
@patch.object(WebContent, 'fetch_to_dir')
def test_packages_show(
    mock_fetch_file,
    mock_url_open,
    mock_parse_report_file
):
    mock_parse_report_file.side_effect = DownloadMetadataFileExceptionOBS(
        'Not found!'
    )

    mock_fetch_file.return_value = \
        'tests/data/openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.133.packages'

    location = MagicMock()
    location.read.return_value = urlopen_response
    mock_url_open.return_value = location

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            'packages', 'show',
            '--image-name', 'openSUSE-Leap-15.0-Azure',
            '--download-url',
            'https://provo-mirror.opensuse.org/repositories/'
            'Cloud:/Images:/Leap_15.0/images/',
            '--target-dir', 'tests/data',
            '--package-name', 'apparmor-parser',
            '--output', 'json'
        ]
    )
    assert result.exit_code == 0

    data = json.loads(result.output)

    assert data['version'] == '2.12.2'
    assert data['release'] == 'lp150.6.14.1'


@patch('obs_img_utils.api.get_checksum_from_file')
@patch('obs_img_utils.api.get_hash_from_image')
@patch('obs_img_utils.web_content.urlopen')
@patch('obs_img_utils.web_content.urlretrieve')
@patch.object(WebContent, 'fetch_to_dir')
def test_image_download(
    mock_fetch_file, mock_url_retrieve, mock_url_open,
    mock_get_hash_from_image, mock_get_checksum
):
    mock_fetch_file.side_effect = [
        None,
        'tests/data/'
        'openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.133.packages',
        'tests/data/'
        'openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.133.vhdfixed.xz',
        'tests/data/'
        'openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.133.vhdfixed.xz.sha256',
        None
    ]

    location = MagicMock()
    location.read.return_value = urlopen_response
    mock_url_open.return_value = location

    hash_val = MagicMock()
    hash_val.hexdigest.return_value = 'ABC1234567890'
    mock_get_hash_from_image.return_value = hash_val
    mock_get_checksum.return_value = 'ABC1234567890'

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            'download',
            '--image-name', 'openSUSE-Leap-15.0-Azure',
            '--download-url',
            'https://provo-mirror.opensuse.org/repositories/'
            'Cloud:/Images:/Leap_15.0/images/',
            '--target-dir', 'tests/data/', '--add-conditions',
            '--disallow-licenses', '--disallow-packages'
        ],
        input='y\n'
              '\n'
              '==\n'
              '1.0.0\n'
              '\n'
              'y\n'
              'apparmor-parser\n'
              '\n'
              '2.12.2\n'
              '\n'
              'n\n'
              'y\n'
              'GPL\n'
              'n\n'
              'y\n'
              '*-mini\n'
              'n\n'
    )

    assert result.exit_code == 0
    assert 'Image downloaded: tests/data/openSUSE-Leap-15.0-Azure.x86_64' \
        '-1.0.0-Build1.133.vhdfixed.xz' in result.output


@patch.object(OBSImageUtil, 'parse_report_file')
@patch('obs_img_utils.api.time')
@patch('obs_img_utils.api.get_checksum_from_file')
@patch('obs_img_utils.api.get_hash_from_image')
@patch('obs_img_utils.web_content.urlopen')
@patch.object(WebContent, 'fetch_to_dir')
def test_image_download_failed_conditions(
    mock_fetch_file, mock_url_open,
    mock_get_hash_from_image, mock_get_checksum, mock_time,
    mock_parse_report_file
):
    mock_parse_report_file.side_effect = DownloadMetadataFileExceptionOBS(
        'Not found!'
    )

    mock_fetch_file.return_value = \
        'tests/data/openSUSE-Leap-15.0-Azure.x86_64-1.0.0-Build1.133.packages'

    location = MagicMock()
    location.read.return_value = urlopen_response
    mock_url_open.return_value = location

    hash_val = MagicMock()
    hash_val.hexdigest.return_value = 'ABC1234567890'
    mock_get_hash_from_image.return_value = hash_val
    mock_get_checksum.return_value = 'ABC1234567890'

    mock_time.time.side_effect = [0, 0, 1]

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            'download',
            '--image-name', 'openSUSE-Leap-15.0-Azure',
            '--download-url',
            'https://provo-mirror.opensuse.org/repositories/'
            'Cloud:/Images:/Leap_15.0/images/',
            '--target-dir', 'tests/data/', '--add-conditions',
            '--conditions-wait-time', '1'
        ],
        input='y\n'
              '\n'
              '==\n'
              '1.1.0\n'
              '\n'
              'n\n'
    )

    assert result.exit_code == 1
    assert 'Version condition failed: ' \
           'openSUSE-Leap-15.0-Azure 1.0.0 == 1.1.0' in result.output
    assert 'ImageConditionsException: Image conditions not met' \
        in result.output
