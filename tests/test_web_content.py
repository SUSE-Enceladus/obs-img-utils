# Copyright (c) 2020 SUSE LLC, All rights reserved.
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

import os

from unittest.mock import patch

from obs_img_utils.web_content import WebContent


@patch('obs_img_utils.web_content.urlretrieve')
def test_fetch_to_dir(mock_url_retrieve):
    path = os.path.abspath('tests/data/index.html')
    wc = WebContent('file://{0}'.format(path))
    name = wc.fetch_to_dir(
        'SLES15-SP1-GCE',
        '^SLES15-SP1-GCE\\.x86_64-(\\d+\\.\\d+\\.\\d+)-Build(.*)',
        'tests/data',
        ['packages'])
    assert name == 'tests/data/SLES15-SP1-GCE.x86_64-1.0.2-Build1.6.packages'
