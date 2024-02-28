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
import os
import re

from lxml import html

from urllib.request import (
    urlretrieve,
    urlopen,
    Request
)
import packaging.version as pv


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
        index_list = self._manage_fetch_index_list(base_name)
        if not index_list:
            # Newer OBS web interface prefixes links with "./"
            # Trying it out in case index_list is empty
            index_list = self._manage_fetch_index_list(
                base_name,
                href_prefix='./'
            )
        return index_list

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

        # Previous search did not find the target file
        # Trying to search through the json listing
        # per new MirrorCache web interface used in opensuse.org
        for name in self.fetch_json_list(base_name):
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

    def fetch_file_name(
        self,
        base_name,
        regex,
        extensions
    ):
        possible_filenames = []
        for name in self.fetch_index_list(base_name):
            for extension in extensions:
                if name.endswith(extension) and re.match(regex, name):
                    possible_filenames.append(
                        (name.replace(extension, ''), extension)
                    )
        if possible_filenames:
            return self._pick_highest_version_release(
                possible_filenames,
                regex
            )
        return None, None

    def _manage_fetch_index_list(self, base_name, href_prefix=''):
        request = Request(self.uri)
        location = urlopen(request)
        tree = html.fromstring(location.read())
        xpath_filter = '//a[starts-with(@href, "{0}")]/@href'.format(
                href_prefix + base_name
            )
        index_list = tree.xpath(
            xpath_filter,
            namespaces=self.namespace_map
        )

        new_index_list = []

        if href_prefix:
            pref_len = len(href_prefix)
            for myindex in index_list:
                new_index_list.append(myindex[pref_len:])
        else:
            new_index_list = index_list

        return sorted(list(set(new_index_list)))

    def fetch_json_list(self, base_name):
        index_list = self._manage_fetch_json_list(base_name)
        return index_list

    def _manage_fetch_json_list(self, base_name, urlparam='jsontable'):
        request = Request(self.uri + '?' + urlparam)
        location = urlopen(request)
        index_list = []
        try:
            links = json.loads(location.read())['data']
            for link in links:
                index_list.append(link['name'])
        except Exception:
            pass
        return sorted(list(set(index_list)))

    def _pick_highest_version_release(self, possible_filenames, regex):
        chosen_tuple = (None, None)
        highest_version = None
        for filename, extension in possible_filenames:
            version = re.search(regex, filename)
            if version:
                new_version = ".".join([version.group(1), version.group(2)])
                if new_version[-1] == ".":
                    new_version = new_version[:-1]

                if highest_version is None:
                    highest_version = new_version
                    chosen_tuple = (filename, extension)
                    continue

                if pv.Version(new_version) > pv.Version(highest_version):
                    highest_version = new_version
                    chosen_tuple = (filename, extension)
        return chosen_tuple
