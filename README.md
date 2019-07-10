[![Build Status](https://travis-ci.com/SUSE-Enceladus/obs-img-utils.svg?branch=master)](https://travis-ci.com/SUSE-Enceladus/obs-img-utils)
[![Documentation Status](https://readthedocs.org/projects/obs-img-utils/badge/?version=latest)](https://obs-img-utils.readthedocs.io/en/latest/?badge=latest)
[![Py Versions](https://img.shields.io/pypi/pyversions/obs-img-utils.svg)](https://pypi.org/project/obs-img-utils/)
[![License](https://img.shields.io/pypi/l/obs-img-utils.svg)](https://pypi.org/project/obs-img-utils/)

# [obs-img-utils](https://github.com/SUSE-Enceladus/obs-img-utils)

overview
========

obs-img-utils provides a command line utility and API for images
in Open Build Service.

It provides the following commands:

- Downloading images based on conditions
- Get list of packages in an image
- Get version info for a specific package

Installation
============

To install the package use the following commands as root:

```shell
$ zypper ar http://download.opensuse.org/repositories/Cloud:/Tools/<distribution>
$ zypper refresh
$ zypper in python3-obs-img-utils
```

Requirements
============

-   lxml
-   Click
-   PyYaml

# [Docs](https://obs-img-utils.readthedocs.io/en/latest/)

CLI Overview
============

The CLI provides multiple subcommands to initiate image testing:

* `obs-img-utils download`

   Download the image with optional condition checking for version
   and packages.

* `obs-img-utils packages list`

   Show a list of packages in the given image.

* `obs-img-utils packages show`

   Show version information for provided package.

Issues/Enhancements
===================

Please submit issues and requests to
[Github](https://github.com/SUSE-Enceladus/obs-img-utils/issues).

Contributing
============

Contributions to obs-img-utils are welcome and encouraged. See
[CONTRIBUTING](https://github.com/SUSE-Enceladus/obs-img-utils/blob/master/CONTRIBUTING.md)
for info on getting started.

License
=======

Copyright (c) 2019 SUSE LLC. All rights reserved.

Distributed under the terms of GPL-3.0+ license, see
[LICENSE](https://github.com/SUSE-Enceladus/obs-img-utils/blob/master/LICENSE)
for details.
