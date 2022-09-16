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

import logging
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
    def __init__(self, uri, logger=None, log_level=logging.INFO):
        self.uri = uri
        self.namespace_map = dict(
            xhtml='http://www.w3.org/1999/xhtml'
        )
        if logger:
            self.logger = logger
        else:
            logger = logging.getLogger('obs_img_utils')
            logger.setLevel(log_level)
            self.log_callback = logger

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
        target_file = self._manage_fetch_to_dir(
            base_name,
            regex,
            target_dir,
            extensions,
            callback=callback
        )

        if target_file:
            return target_file
        else:
            self.logger.debug(
                f'No image was found with the expected format {str(regex)}.'
                f' Checking by name {base_name}'
            )
            target_file = self._manage_fetch_to_dir(
                base_name,
                '^' + re.escape(base_name),  # base_name as regex
                target_dir,
                extensions,
                callback=callback
            )

            if target_file:
                return target_file

    def _manage_fetch_to_dir(
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

    def fetch_file_name(
        self,
        base_name,
        regex,
        extensions
    ):
        matching_tuples = self._manage_fetch_file_name(
            base_name,
            regex,
            extensions
        )
        if matching_tuples:
            return matching_tuples[0]
        else:
            self.logger.debug(
                f'No image was found with the expected format {str(regex)}.'
                f' Checking by name {base_name}'
            )
            matching_tuples = self._manage_fetch_file_name(
                base_name,
                '^' + re.escape(base_name),  # provided base_name as regex
                extensions,
                return_on_first_match=False
            )

            if len(matching_tuples) == 1:
                self.logger.debug(
                    f'Found one filename matching {base_name}'
                    f' using {matching_tuples[0][0]}'
                )
                # Only 1 matching tuple we assume it's good
                return matching_tuples[0]
            else:
                matching_files = []
                for name, extension in matching_tuples:
                    matching_files.append(str(name) + str(extension))
                self.logger.error(
                    'More than one image matched the provided name '
                    f'{base_name}({str(matching_files)}) '
                )

        return None, None

    def _manage_fetch_file_name(
        self,
        base_name,
        regex,
        extensions,
        return_on_first_match=True
    ):
        matching_tuples = []
        matching_names_in_index = self.fetch_index_list(base_name)
        for name in matching_names_in_index:
            for extension in extensions:
                if name.endswith(extension) and re.match(regex, name):
                    matching_tuples.append(
                        (
                            name.replace(extension, ''),
                            extension
                        )
                    )
                    if return_on_first_match is True:
                        return matching_tuples
        return matching_tuples

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
