# Copyright (c) 2019 SUSE LLC, All rights reserved.
#
# This file is part of obs-img-downloader. obs-img-downloader provides
# an api and command line utilities for downloading images from OBS.
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
import logging
import os
import sys
import time
import yaml

from collections import ChainMap, namedtuple
from contextlib import suppress
from functools import wraps

module = sys.modules[__name__]

default_config = os.path.expanduser('~/.config/obs_img_downloader/config.yaml')
defaults = {
    'arch': 'x86_64',
    'cloud': 'ec2',
    'config': default_config,
    'download_dir': os.path.expanduser('~/obs_img_downloader/images'),
    'download_url': 'https://provo-mirror.opensuse.org/repositories'
                    '/Cloud:/Images:/Leap_15.0/images/',
    'log_level': logging.INFO,
    'no_color': False,
    'version_format': '{kiwi_version}-Build{obs_build}'
}

img_downloader_config = namedtuple(
    'img_downloader_config',
    sorted(defaults)
)

bar = None


def get_config(cli_context):
    """
    Process Image Downloader config.

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
    if done:
        module.bar.render_finish()
        module.bar = None
        return

    if not module.bar:
        module.bar = click.progressbar(
            length=total_size,
            label='Downloading image'
        )

    module.bar.update(block_num)


def retry(exceptions, tries=4, delay=3, backoff=2):
    """
    Retry calling the decorated instance method using an exponential backoff.
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = '{}, Retrying in {} seconds...'.format(
                        e,
                        mdelay
                    )

                    with suppress(Exception):
                        # 'Self' is always first arg for instance method
                        log_callback = locals()['args'][0].log_callback
                        log_callback.warning(msg)

                    time.sleep(mdelay)
                    mtries -= 1

                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def echo_style(message, no_color, fg='green'):
    if no_color:
        click.echo(message)
    else:
        click.secho(message, fg=fg)


def conditions_repl():
    image_conditions = []
    while True:
        if click.confirm('Add an image condition?'):
            condition_type = click.prompt(
                'Enter the condition type',
                type=click.Choice(['image', 'package'])
            )

            if condition_type == 'image':
                image_version = click.prompt(
                    'Enter the image version condition',
                    type=str
                )

                image_conditions.append({'image': image_version})
            else:
                package_name = click.prompt(
                    'Enter the package name',
                    type=str
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

                build_id = click.prompt(
                    'Enter the build id (optional)',
                    type=str,
                    default=''
                )

                condition = {
                    'package_name': package_name,
                    'condition': condition_exp,
                }

                if version:
                    condition['version'] = version
                elif build_id:
                    condition['build_id'] = build_id

                image_conditions.append(condition)
        else:
            break

    return image_conditions
