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
import logging

from obs_img_utils.utils import (
    get_config,
    click_progress_callback,
    conditions_repl,
    handle_errors,
    echo_package,
    echo_packages,
    get_logger,
    process_shared_options,
    license_repl,
    packages_repl,
    filter_packages_by_licenses,
    filter_packages_by_name
)
from obs_img_utils.api import OBSImageUtil

shared_options = [
    click.option(
        '-C',
        '--config',
        type=click.Path(exists=True),
        help='OBS Image utils config file to use. Default: '
             '~/.config/obs_img_utils/config.yaml'
    ),
    click.option(
        '--no-color',
        is_flag=True,
        help='Remove ANSI color and styling from output.'
    ),
    click.option(
        '--debug',
        'log_level',
        flag_value=logging.DEBUG,
        help='Display debug level logging to console.'
    ),
    click.option(
        '--verbose',
        'log_level',
        flag_value=logging.INFO,
        default=True,
        help='Display logging info to console. (Default)'
    ),
    click.option(
        '--quiet',
        'log_level',
        flag_value=logging.WARNING,
        help='Disable console output.'
    ),
    click.option(
        '--download-url',
        type=click.STRING,
        help='URL for OBS download repository.'
    ),
    click.option(
        '--target-dir',
        type=click.Path(exists=True),
        help='Directory to store downloaded images and checksums.'
    ),
    click.option(
        '--image-name',
        type=click.STRING,
        help='Image name to download from the download-url.',
        required=True
    ),
    click.option(
        '--arch',
        type=click.Choice(['x86_64', 'aarch64']),
        help='Architecture of the image.'
    ),
    click.option(
        '--profile',
        type=click.STRING,
        help='The multibuild profile name for the image.'
    )
]


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


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
@click.pass_context
def main(context):
    """
    The command line interface provides obs image utilities.

    This includes downloading images, checking packages in images
    and getting package version information.
    """
    if context.obj is None:
        context.obj = {}


@click.command()
@click.option(
    '--add-conditions',
    is_flag=True,
    help='Invoke conditions process to specify conditions '
         'for image'
)
@click.option(
    '--conditions-wait-time',
    type=click.INT,
    default=0,
    help='Time (in seconds) to wait for conditions '
         'to be met. Retry period is 150 seconds and'
         ' default is 0 seconds for no wait.'
)
@click.option(
    '--extension',
    type=click.STRING,
    help='Image file extension. Examples: [tar.gz, raw.xz]'
)
@click.option(
    '--checksum-extension',
    type=click.STRING,
    help='Image checksum file extension. Example: sha256'
)
@click.option(
    '--disallow-licenses',
    is_flag=True,
    help='Invoke license REPL to specify any licenses that '
         'should not be in the image.'
)
@click.option(
    '--disallow-packages',
    is_flag=True,
    help='Invoke packages REPL to specify any packages which '
         ' should not be in the image. This can use a wildcard'
         ' (*) to match a naming pattern like "*-mini".'
)
@add_options(shared_options)
@click.pass_context
def download(
    context,
    add_conditions,
    conditions_wait_time,
    extension,
    checksum_extension,
    disallow_licenses,
    disallow_packages,
    **kwargs
):
    """
    Download image from OBS repository specified by `download-url`.
    """
    context.obj['conditions_wait_time'] = conditions_wait_time
    context.obj['checksum_extension'] = checksum_extension
    context.obj['extension'] = extension

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = get_logger(config_data.log_level)

    image_conditions = []
    if add_conditions:
        image_conditions = conditions_repl(config_data.no_color)

    licenses = []
    if disallow_licenses:
        licenses = license_repl()

    package_names = []
    if disallow_packages:
        package_names = packages_repl()

    with handle_errors(config_data.log_level, config_data.no_color):
        downloader = OBSImageUtil(
            config_data.download_url,
            context.obj['image_name'],
            conditions=image_conditions,
            arch=config_data.arch,
            target_directory=config_data.target_dir,
            profile=config_data.profile,
            log_level=config_data.log_level,
            conditions_wait_time=config_data.conditions_wait_time,
            log_callback=logger,
            report_callback=click_progress_callback,
            checksum_extension=config_data.checksum_extension,
            extension=config_data.extension,
            filter_licenses=licenses,
            filter_packages=package_names
        )
        image_source = downloader.get_image()

    click.echo(
        'Image downloaded: {img_source}'.format(img_source=image_source)
    )


@click.group()
def packages():
    """
    Package commands.
    """


@click.command(name='list')
@click.option(
    '--filter-licenses',
    is_flag=True,
    help='Invoke license REPL to specify license filters'
)
@click.option(
    '--filter-packages',
    is_flag=True,
    help='Invoke packages REPL to specify package name filters'
)
@add_options(shared_options)
@click.pass_context
def list_packages(context, filter_licenses, filter_packages, **kwargs):
    """
    Return a list of packages for the given image name.
    """
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = get_logger(config_data.log_level)

    licenses = []
    if filter_licenses:
        licenses = license_repl()

    package_names = []
    if filter_packages:
        package_names = packages_repl()

    with handle_errors(config_data.log_level, config_data.no_color):
        downloader = OBSImageUtil(
            config_data.download_url,
            config_data.image_name,
            arch=config_data.arch,
            target_directory=config_data.target_dir,
            profile=config_data.profile,
            log_level=config_data.log_level,
            log_callback=logger
        )
        packages_metadata = downloader.get_image_packages_metadata()

    if licenses:
        packages_metadata = filter_packages_by_licenses(
            packages_metadata,
            licenses
        )

    if package_names:
        matching_packages = {}
        for name in package_names:
            matching_packages.update(
                filter_packages_by_name(
                    packages_metadata,
                    name
                )
            )

        packages_metadata = matching_packages

    if not packages_metadata:
        click.echo('No packages found matching criteria.')
    else:
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
@add_options(shared_options)
@click.pass_context
def show(context, package_name, **kwargs):
    """
    Return information for the provided package name in the given image.
    """
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = get_logger(config_data.log_level)

    with handle_errors(config_data.log_level, config_data.no_color):
        downloader = OBSImageUtil(
            config_data.download_url,
            config_data.image_name,
            arch=config_data.arch,
            target_directory=config_data.target_dir,
            profile=config_data.profile,
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
