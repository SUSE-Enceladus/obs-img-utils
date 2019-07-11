Configuration
=============

OBS Image Utils uses a YAML configuration file. The expected path for the
configuration file is *~/.config/obs_img_utils/config.yaml*.

This location can be configured with each command using the *-C/--config*
option. For example::

    obs-mg-utils --config ~/new/config.yaml job add ...

Options
-------

The following options are currently available in the configuration file:

*arch*
  Architecture of image. Example *x86_64*

*cloud*
  Cloud provider the image is built for. Example *ec2*

*download_dir*
  Directory for saving image and checksum. Example */home/{user}/images*

*download_url*
  OBS download repository URL. Example
  *https://provo-mirror.opensuse.org/repositories/Cloud:/Images:/Leap_15.0/images/*

*version_format*
  Format of kiwi and obs version. Example *{kiwi_version}-Build{obs_build}*

*conditions_wait_time*
  Time in seconds to wait for conditions to pass. Example *300*

*log_level*
  Python log level. See Python docs_ for level values.

*no_color*
  If set to *True* removes ANSI color and styling from output.

*verify*
  Verify SSL Certificate. This is *True* by default. Can be *True*,
  *False* or a */path/to/certfile/* used in verification.

.. _docs: https://docs.python.org/3/library/logging.html#levels