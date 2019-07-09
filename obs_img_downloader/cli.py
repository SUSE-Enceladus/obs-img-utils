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

from obs_img_downloader.utils import (
    get_config,
    click_progress_callback,
    conditions_repl,
    handle_errors,
    echo_package,
    echo_packages
)
from obs_img_downloader.api import ImageDownloader, extensions

logger = logging.getLogger('obs_img_downloader')


def print_license(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('GPLv3+')
    ctx.exit()


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group()
@click.version_option()
@click.option(
    '--license',
    is_flag=True,
    callback=print_license,
    expose_value=False,
    is_eager=True,
    help='Show license information.'
)
@click.option(
    '-C',
    '--config',
    type=click.Path(exists=True),
    help='Image Downloader config file to use. Default: '
         '~/.config/obs_img_downloader/config.yaml'
)
@click.option(
    '--no-color',
    is_flag=True,
    help='Remove ANSI color and styling from output.'
)
@click.option(
    '--debug',
    'log_level',
    flag_value=logging.DEBUG,
    help='Display debug level logging to console.'
)
@click.option(
    '--verbose',
    'log_level',
    flag_value=logging.INFO,
    default=True,
    help='Display logging info to console. (Default)'
)
@click.option(
    '--quiet',
    'log_level',
    flag_value=logging.WARNING,
    help='Disable console output.'
)
@click.option(
    '--download-url',
    type=click.STRING,
    help='OBS download URL.'
)
@click.option(
    '--download-dir',
    type=click.Path(exists=True),
    help='Directory to store downloaded images and checksums.'
)
@click.option(
    '--image-name',
    type=click.STRING,
    help='Image name from the OBS download URL.',
    required=True
)
@click.option(
    '--cloud',
    type=click.Choice(extensions.keys()),
    help='Cloud framework for the image to be downloaded.'
)
@click.option(
    '--arch',
    type=click.Choice(['x86_64', 'aarch64']),
    help='Architecture of the image.'
)
@click.option(
    '--version-format',
    type=click.STRING,
    help='Version format for image. Should contain format strings for'
         ' {kiwi_version} and {obs_build}.'
         ' Example: "{kiwi_version}-Build{obs_build}".'
)
@click.pass_context
def main(
    context,
    config,
    no_color,
    log_level,
    download_url,
    download_dir,
    image_name,
    cloud,
    arch,
    version_format,
):
    """
    The command line interface allows you to download and check OBS images.
    """
    if context.obj is None:
        context.obj = {}

    logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(console_handler)

    context.obj['config'] = config
    context.obj['no_color'] = no_color
    context.obj['log_level'] = log_level
    context.obj['download_url'] = download_url
    context.obj['download_dir'] = download_dir
    context.obj['cloud'] = cloud
    context.obj['arch'] = arch
    context.obj['version_format'] = version_format
    context.obj['image_name'] = image_name


@click.command()
@click.option(
    '--conditions',
    is_flag=True,
    help='Invoke conditions process to specify conditions '
         'for image'
)
@click.option(
    '--conditions-wait-time',
    is_flag=True,
    help='Time (in seconds) to wait for conditions '
         'to be met. Retry period is 150 seconds and'
         ' default is 0 seconds for no wait.'
)
@click.pass_context
def download(context, conditions, conditions_wait_time):
    """
    Download image from Open Build Service at `download_url`.
    """
    context.obj['conditions_wait_time'] = conditions_wait_time

    config_data = get_config(context.obj)

    image_conditions = []
    if conditions:
        image_conditions = conditions_repl()

    with handle_errors(config_data.log_level, config_data.no_color):
        downloader = ImageDownloader(
            config_data.download_url,
            context.obj['image_name'],
            config_data.cloud,
            conditions=image_conditions,
            arch=config_data.arch,
            download_directory=config_data.download_dir,
            version_format=config_data.version_format,
            log_level=config_data.log_level,
            log_callback=logger,
            report_callback=click_progress_callback
        )
        image_source = downloader.get_image()

    click.echo(
        'Image downloaded: {img_source}'.format(img_source=image_source)
    )


@click.group()
def packages():
    """
    Handle package requests.
    """


@click.command(name='list')
@click.pass_context
def list_packages(context):
    """
    Return a list of packages for the given image.
    """
    config_data = get_config(context.obj)

    with handle_errors(config_data.log_level, config_data.no_color):
        downloader = ImageDownloader(
            config_data.download_url,
            config_data.image_name,
            config_data.cloud,
            arch=config_data.arch,
            download_directory=config_data.download_dir,
            version_format=config_data.version_format,
            log_level=config_data.log_level,
            log_callback=logger
        )
        packages_metadata = downloader.get_image_packages_metadata()

    echo_packages(
        packages_metadata,
        no_color=config_data.no_color
    )


@click.command()
@click.option(
    '--package-name',
    type=click.STRING,
    required=True,
    help='Name of the package.'
)
@click.pass_context
def show(context, package_name):
    """
    Return information for the provided package name.
    """
    config_data = get_config(context.obj)

    with handle_errors(config_data.log_level, config_data.no_color):
        downloader = ImageDownloader(
            config_data.download_url,
            config_data.image_name,
            config_data.cloud,
            arch=config_data.arch,
            download_directory=config_data.download_dir,
            version_format=config_data.version_format,
            log_level=config_data.log_level,
            log_callback=logger
        )
        packages_metadata = downloader.get_image_packages_metadata()

    echo_package(
        package_name,
        packages_metadata,
        no_color=config_data.no_color
    )


main.add_command(download)
packages.add_command(list_packages)
packages.add_command(show)
main.add_command(packages)
