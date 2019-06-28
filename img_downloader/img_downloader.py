import hashlib
import logging
import os
import re

from collections import namedtuple
from distutils.dir_util import mkpath
from pkg_resources import parse_version
from tempfile import NamedTemporaryFile
from urllib.error import ContentTooShortError, URLError

from img_downloader.exceptions import (
    ImageDownloaderException,
    DownloadPackagesFileException,
    ImageConditionsException,
    PackageVersionException,
    ImageChecksumException
)
from img_downloader.utils import retry
from img_downloader.web_content import WebContent

extensions = {
    'azure': r'vhdfixed\.xz',
    'ec2': r'raw\.xz',
    'gce': r'tar\.gz',
    'oci': r'qcow2'
}

kiwi_version = r'(\d+\.\d+\.\d+)'
obs_build = r'(\d+\.\d+)'

package_type = namedtuple(
    'package_type', [
        'version', 'release', 'arch', 'checksum'
    ]
)

build_version = namedtuple(
    'build_version', [
        'kiwi_version', 'obs_build'
    ]
)


class ImageDownloader(object):
    """
        Implements image downloader.

        Attributes
        * :attr:`download_url`
          Buildservice URL
        * :attr:`image_name`
          Image name as specified in the KIWI XML description of the
          Buildservice project and package
        * :attr:`conditions`
          Criteria for the image build which is a list of hashes like
          the following example demonstrates:
          conditions=[
              # a package condition with version and release spec
              {
               'package_name': 'kernel-default',
               'version': '4.13.1',
               'build_id': '1.1'
              },
              # a image version condition
              {'image': '1.42.1'}
          ]
        * :attr:`arch`
          Buildservice package architecture, defaults to: x86_64
        * :attr:`download_directory`
          Download directory name, defaults to: /tmp
        """

    def __init__(
            self,
            download_url,
            image_name,
            cloud,
            conditions=None,
            arch='x86_64',
            download_directory=None,
            version_format=None,
            log_level=logging.INFO,
            report_callback=None
    ):
        self.logger = logging.getLogger('img_downloader')
        self.logger.setLevel(log_level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter('%(message)s'))

        self.logger.addHandler(console_handler)

        self.download_url = download_url
        self.image_name = image_name
        self.cloud = cloud.lower()

        if cloud not in ('azure', 'ec2', 'gce', 'oci'):
            raise ImageDownloaderException(
                '{cloud} is not supported. '
                'Valid values are azure, ec2, gce or oci'.format(
                    cloud=cloud
                )
            )

        self.extension = extensions[cloud]
        self.arch = arch
        self.download_directory = os.path.expanduser(
            os.path.join(
                download_directory or '~/images/'
            )
        )
        self.image_metadata_name = None
        self.conditions = conditions
        self.log_callback = None
        self.version_format = \
            version_format or '{kiwi_version}-Build{obs_build}'
        self.version_format = self.version_format.format(
            kiwi_version=kiwi_version,
            obs_build=obs_build
        )

        self.remote = WebContent(self.download_url)
        self.report_callback = report_callback
        self.image_status = self._init_status()

    def _init_status(self):
        image_status = {
            'name': self.image_name,
            'job_status': 'prepared',
            'image_source': ['unknown'],
            'packages': {},
            'packages_checksum': 'unknown',
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
        ImageDownloaderException,
        ImageChecksumException
    ))
    def _download_image(self):
        """
        Download image and shasum to given file.
        """
        mkpath(self.download_directory)

        self._wait_on_image_conditions()

        regex = r''.join([
            r'^',
            self.image_metadata_name.replace('.packages', ''),
            r'\.',
            self.extension,
            r'$'
        ])

        image_file = self.remote.fetch_to_dir(
            self.image_name,
            regex,
            self.download_directory,
            self.report_callback
        )

        if not image_file:
            raise ImageDownloaderException(
                'No images found that match {regex} at {url}'.format(
                    regex=self.image_metadata_name,
                    url=self.download_url
                )
            )

        image_checksum = self.remote.fetch_to_dir(
            self.image_name,
            regex.replace('$', r'\.sha256$'),
            self.download_directory
        )

        if not image_checksum:
            raise ImageDownloaderException(
                'No checksum found that match {regex} at {url}'.format(
                    regex=self.image_metadata_name,
                    url=self.download_url
                )
            )

        image_hash = hashlib.sha256()
        with open(image_file, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b''):
                image_hash.update(byte_block)

        with open(image_checksum, 'r') as f:
            lines = f.readlines()
            expected_checksum = lines[3].strip()

        if image_hash.hexdigest() != expected_checksum:
            raise ImageChecksumException(
                'Image checksum does not match expected value'
            )

        return image_file

    def _get_build_number(self, name):
        build = re.search(self.version_format, name)

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
        self._get_image_packages_metadata()

        packages_digest = hashlib.md5()
        packages_digest.update(format(self.image_status['packages']).encode())
        packages_checksum = packages_digest.hexdigest()
        self.image_status['packages_checksum'] = packages_checksum

        self._get_image_version()

        for condition in self.image_status['conditions']:
            if 'image' in condition:
                if self.image_status['version'] == condition['image']:
                    condition['status'] = True
                else:
                    condition['status'] = False
            elif 'package_name' in condition:
                if self._lookup_package(
                        self.image_status['packages'], condition
                ):
                    condition['status'] = True
                else:
                    condition['status'] = False

        if not self._image_conditions_complied():
            raise ImageConditionsException('Image conditions not met')

    @retry(ImageConditionsException, tries=3, delay=300, backoff=1)
    def _wait_on_image_conditions(self):
        self.check_image_conditions()

    def get_image(self):
        self.image_status['image_source'] = self._download_image()
        self.logger.info(
            'Downloaded: {0}'.format(
                self.image_status['image_source']
            )
        )

    @retry(DownloadPackagesFileException)
    def _download_packages_file(self, packages_file_name):
        regex = r''.join([
            self.image_name,
            r'\.',
            self.arch,
            '-',
            self.version_format,
            r'\.packages'
        ])

        name = self.remote.fetch_file(
            self.image_name,
            regex,
            packages_file_name
        )

        if not name:
            raise DownloadPackagesFileException(
                'No image metadata found matching: {regex}, '
                'at {url}'.format(
                    regex=regex,
                    url=self.download_url
                )
            )

        return name

    def _get_image_version(self):
        # Extract image version information from .packages file name
        self.image_status['version'] = self._get_build_number(
            self.image_metadata_name
        ).kiwi_version

        if self.image_status['version'] == 'unknown':
            raise DownloadPackagesFileException(
                'No image version found using {formatter}. '
                'Unexpected image name format: {name}'.format(
                    formatter=self.version_format,
                    name=self.image_metadata_name
                )
            )

    def _get_image_packages_metadata(self):
        packages_file = NamedTemporaryFile()

        self.image_metadata_name = self._download_packages_file(
            packages_file.name
        )

        result_packages = {}
        with open(packages_file.name) as packages:
            for package in packages.readlines():
                package_digest = hashlib.md5()
                package_digest.update(package.encode())
                package_info = package.split('|')
                package_name = package_info[0]
                package_result = package_type(
                    version=package_info[2],
                    release=package_info[3],
                    arch=package_info[4],
                    checksum=package_digest.hexdigest()
                )
                result_packages[package_name] = package_result

        self.image_status['packages'] = result_packages

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
            raise PackageVersionException(
                'Invalid version compare expression: "{0}"'.format(condition)
            )

    def _lookup_package(self, packages, condition):
        package_name = condition['package_name']

        if package_name not in packages:
            return False

        condition_eval = condition.get('condition', '>=')
        package_data = packages[package_name]

        if 'version' in condition:
            # we want to lookup a specific version
            match = self._version_compare(
                package_data.version,
                condition['version'],
                condition_eval
            )

            if not match:
                return False

        if 'build_id' in condition:
            # we want to lookup a specific build number
            match = self._version_compare(
                package_data.release,
                condition['build_id'],
                condition_eval
            )

            if not match:
                return False

        return True
