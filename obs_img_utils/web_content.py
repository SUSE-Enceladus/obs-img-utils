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

import os
import re

from lxml import html

from urllib.request import (
    urlretrieve,
    urlopen,
    Request
)


class WebContent(object):
    """
    Web Content Scanner and Download interface
    """
    def __init__(self, uri):
        self.uri = uri
        self.namespace_map = dict(
            xhtml='http://www.w3.org/1999/xhtml'
        )

    def fetch_index_list(self, base_name):
        request = Request(self.uri)
        location = urlopen(request)
        tree = html.fromstring(location.read())
        index_list = tree.xpath(
            '//a[starts-with(@href, "{0}")]/@href'.format(base_name),
            namespaces=self.namespace_map
        )
        return sorted(list(set(index_list)))

    def fetch_file(self, base_name, regex, target_file):
        for name in self.fetch_index_list(base_name):
            if re.match(regex, name):
                urlretrieve(
                    os.sep.join([self.uri, name]),
                    target_file
                )
                return name

    def fetch_to_dir(
        self,
        base_name,
        regex,
        target_dir,
        extensions,
        callback=None
    ):
        kwargs = {}
        if callback:
            kwargs['reporthook'] = callback

        for name in self.fetch_index_list(base_name):
            for extension in extensions:
                if name.endswith(extension) and re.match(regex, name):
                    target_file = os.sep.join([target_dir, name])

                    try:
                        urlretrieve(
                            os.sep.join([self.uri, name]),
                            target_file,
                            **kwargs
                        )
                    finally:
                        if callback:
                            callback(0, 0, 0, True)

                    return target_file
