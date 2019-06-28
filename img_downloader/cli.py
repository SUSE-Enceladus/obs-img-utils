import click
import logging

from img_downloader.utils import bar, get_config, callback
from img_downloader.img_downloader import ImageDownloader


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
         '~/.config/img_downloader/config'
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
@click.pass_context
def main(context, config, no_color, log_level):
    """
    The command line interface allows you to download and check OBS images.
    """
    if context.obj is None:
        context.obj = {}

    context.obj['config'] = config
    context.obj['no_color'] = no_color
    context.obj['log_level'] = log_level


@click.command()
@click.option(
    '--download-url',
    type=click.STRING,
    help=''
)
@click.option(
    '--download-dir',
    type=click.STRING,
    help=''
)
@click.option(
    '--image-name',
    type=click.STRING,
    help=''
)
@click.option(
    '--cloud',
    type=click.STRING,
    help=''
)
@click.option(
    '--arch',
    type=click.STRING,
    help=''
)
@click.option(
    '--version-format',
    type=click.STRING,
    help=''
)
@click.pass_context
def download(context, download_url, download_dir, image_name, cloud, arch, version_format):
    """
    Download image.
    """
    #config_data = get_config(context.obj)

    d = ImageDownloader(
        'https://provo-mirror.opensuse.org/repositories/Cloud:/Images:/Leap_15.0/images/',
        'openSUSE-Leap-15.0-GCE',
        'gce',
        download_directory='/run/media/smarlow/DellHDD/mash/images',
        report_callback=callback
    )

    d.get_image()


main.add_command(download)
