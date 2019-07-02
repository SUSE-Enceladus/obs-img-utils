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
    'config': default_config,
    'download_dir': os.path.expanduser('~/obs_img_downloader/images'),
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


def callback(block_num, read_size, total_size, done=False):
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


def retry(exceptions, tries=4, delay=3, backoff=2, logger=None):
    """
    Retry calling the decorated function using an exponential backoff.
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, current_delay = tries, delay
            while mtries is None or mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = '{}, Retrying in {} seconds...'.format(
                        e,
                        current_delay
                    )
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)

                    if mtries:
                        mtries -= 1

                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
