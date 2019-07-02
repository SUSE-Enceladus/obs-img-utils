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

    def fetch_to_dir(self, base_name, regex, target_dir, callback=None):
        kwargs = {}
        if callback:
            kwargs['reporthook'] = callback

        for name in self.fetch_index_list(base_name):
            if re.match(regex, name):
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
