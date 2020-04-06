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

import click
import hashlib
import json
import logging
import os
import sys
import time
import yaml
import fnmatch

from collections import ChainMap, namedtuple
from contextlib import contextmanager, suppress
from functools import wraps

module = sys.modules[__name__]

default_config = os.path.expanduser('~/.config/obs_img_utils/config.yaml')
extensions = [
    'vhdfixed.xz',
    'raw.xz',
    'tar.gz',
    'qcow2'
]
checksum_extensions = ['sha256']

defaults = {
    'arch': 'x86_64',
    'config': default_config,
    'target_dir': os.path.expanduser('~/obs_img_utils/images'),
    'download_url': 'https://provo-mirror.opensuse.org/repositories'
                    '/Cloud:/Images:/Leap_15.0/images/',
    'image_name': None,
    'log_level': logging.INFO,
    'no_color': False,
    'conditions_wait_time': 0,
    'profile': None,
    'checksum_extension': None,
    'extension': None
}

img_downloader_config = namedtuple(
    'img_downloader_config',
    sorted(defaults)
)

bar = None


def get_config(cli_context):
    """
    Process OBS Image utils config.

    Use ChainMap to build config values based on
    command line args, config and defaults.
    """
    config_path = cli_context['config'] or default_config

    config_values = {}
    with suppress(Exception):
        with open(config_path) as config_file:
            config_values = yaml.safe_load(config_file)

    cli_values = {
        key: value for key, value in cli_context.items() if value is not None
    }
    data = ChainMap(cli_values, config_values, defaults)

    return img_downloader_config(**data)


def click_progress_callback(block_num, read_size, total_size, done=False):
    """
    Update the module level progress bar with image download progress.

    If download has finished flush stdout with render_finish.
    """
    if done and module.bar:
        module.bar.render_finish()
        module.bar = None
        return

    if not module.bar:
        module.bar = click.progressbar(
            length=total_size,
            label='Downloading image'
        )

    module.bar.update(read_size)


def retry(exceptions, tries=4, delay=3, backoff=2):
    """
    Retry calling the decorated instance method using an exponential backoff.
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            retries, cur_delay = tries, delay
            while retries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as error:
                    msg = '{}, Retrying in {} seconds...'.format(
                        error,
                        cur_delay
                    )

                    with suppress(Exception):
                        # 'Self' is always first arg for instance method
                        log_callback = locals()['args'][0].log_callback
                        log_callback.warning(msg)

                    time.sleep(cur_delay)
                    retries -= 1

                    cur_delay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def echo_style(message, no_color, fg='green'):
    if no_color:
        click.echo(message)
    else:
        click.secho(message, fg=fg)


def conditions_repl(no_color):
    """
    Query and accept input for condition options.
    """
    image_conditions = []
    while True:
        if click.confirm('Add a condition?'):
            package_name = click.prompt(
                'Enter the package name '
                '(leave blank for an image condition)',
                type=str,
                default=''
            )

            condition_exp = click.prompt(
                'Enter the condition expression',
                type=click.Choice(['>=', '<=', '==', '>', '<']),
                default='>='
            )

            version = click.prompt(
                'Enter the version (optional)',
                type=str,
                default=''
            )

            release = click.prompt(
                'Enter the release (optional)',
                type=str,
                default=''
            )

            if not (package_name or version or release):
                echo_style(
                    'Condition skipped, conditions require at least one of:'
                    ' package_name, version or release.',
                    no_color,
                    fg='red'
                )
                continue

            condition = {
                'condition': condition_exp,
            }

            if package_name:
                condition['package_name'] = package_name
            if version:
                condition['version'] = version
            if release:
                condition['release'] = release

            image_conditions.append(condition)
        else:
            break

    return image_conditions


@contextmanager
def handle_errors(log_level, no_color):
    """
    Context manager to handle exceptions and echo error msg.
    """
    try:
        yield
    except Exception as error:
        if log_level == logging.DEBUG:
            raise

        echo_style(
            "{}: {}".format(type(error).__name__, error),
            no_color,
            fg='red'
        )
        sys.exit(1)


def style_string(message, no_color, fg='yellow'):
    """
    Add color style to string if no_color is False.
    """
    if no_color:
        return message
    else:
        return click.style(message, fg=fg)


def echo_package(name, data, no_color):
    """
    Echoes package info to terminal based on name.
    """
    try:
        package_info = data[name]
    except KeyError:
        echo_style(
            'Package with name: {name}, not in image.'.format(name=name),
            no_color,
            fg='red'
        )
    else:
        click.echo(
            style_string(
                json.dumps(package_info._asdict(), indent=2),
                no_color,
                fg='green'
            )
        )


def echo_packages(data, no_color):
    """
    Echoes list of package info to terminal.
    """
    packages = {}
    for name, info in data.items():
        packages[name] = info._asdict()

    click.echo(
        style_string(
            json.dumps(packages, indent=2),
            no_color,
            fg='green'
        )
    )


def get_logger(log_level):
    """
    Return new console logger at provided log level.
    """
    logger = logging.getLogger('obs_img_utils')
    logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter('%(message)s'))

    logger.addHandler(console_handler)
    return logger


def process_shared_options(context_obj, kwargs):
    """
    Update context with values for shared options.
    """
    context_obj['config'] = kwargs['config']
    context_obj['no_color'] = kwargs['no_color']
    context_obj['log_level'] = kwargs['log_level']
    context_obj['download_url'] = kwargs['download_url']
    context_obj['target_dir'] = kwargs['target_dir']
    context_obj['arch'] = kwargs['arch']
    context_obj['profile'] = kwargs['profile']
    context_obj['image_name'] = kwargs['image_name']


def get_hash_from_image(image_file):
    """
    Calculate hash of image read in from stream.
    """
    image_hash = hashlib.sha256()
    with open(image_file, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            image_hash.update(byte_block)

    return image_hash


def get_checksum_from_file(checksum_file):
    """
    Get the checksum from OBS image.

    Expects an inline signed file where checksum is on line 4.
    """
    with open(checksum_file, 'r') as f:
        lines = f.readlines()

    try:
        expected_checksum = lines[3].strip().split()[0]
    except IndexError:
        expected_checksum = lines[0].strip().split()[0]

    return expected_checksum


def license_repl():
    """
    Query and accept input for license types.
    """
    licenses = []
    while True:
        if click.confirm('Add another license?'):
            license_name = click.prompt(
                'Enter the license name (GPL-2.0-only)',
                type=str
            )
            licenses.append(license_name)
        else:
            break

    return licenses


def packages_repl():
    """
    Query and accept input for invalid package names.
    """
    packages = []
    while True:
        if click.confirm('Add another package?'):
            package_name = click.prompt(
                'Enter the package name or wildcard (*-mini)',
                type=str
            )
            packages.append(package_name)
        else:
            break

    return packages


def filter_packages_by_licenses(packages_metadata, licenses):
    """
    Returned a filtered dictionary of packages that matches the licenses.
    """
    matching_packages = {}
    for package, pkg_data in packages_metadata.items():
        if pkg_data.license in licenses:
            matching_packages[package] = pkg_data

    return matching_packages


def filter_packages_by_name(packages_metadata, package_name):
    """
    Returned a filtered dictionary of packages that matches the package names.
    """
    matching_packages = {}

    packages = packages_metadata.keys()
    matching_names = fnmatch.filter(packages, package_name)

    for name in matching_names:
        matching_packages[name] = packages_metadata[name]

    return matching_packages
