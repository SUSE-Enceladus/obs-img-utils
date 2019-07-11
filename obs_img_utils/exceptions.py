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


class OBSImageUtilsException(Exception):
    """
    Base class to handle all known exceptions.

    Specific exceptions are implemented as sub classes
    of OBSImageUtilsException.

    Attributes
    * :attr:`message`
        Exception message text
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return format(self.message)


class DownloadPackagesFileExceptionOBS(OBSImageUtilsException):
    """
    Exception raised if there is an issue downloading packages file.
    """


class OBSImageConditionsException(OBSImageUtilsException):
    """
    Exception raised if image metadata does not match conditions.
    """


class PackageVersionExceptionOBS(OBSImageUtilsException):
    """
    Exception raised if package does not match version conditions.
    """


class OBSImageChecksumException(OBSImageUtilsException):
    """
    Exception raised if image checksum does not match.
    """


class OBSImageVersionException(OBSImageUtilsException):
    """
    Exception raised when unable to parse image version.
    """


class OBSImageDownloadException(OBSImageUtilsException):
    """
    Exception raised when unable to download image file.
    """
