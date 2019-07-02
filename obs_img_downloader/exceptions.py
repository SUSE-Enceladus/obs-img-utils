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


class ImageDownloaderException(Exception):
    """
    Base class to handle all known exceptions.

    Specific exceptions are implemented as sub classes
    of ImageDownloaderException.

    Attributes
    * :attr:`message`
        Exception message text
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return format(self.message)


class DownloadPackagesFileException(ImageDownloaderException):
    """
    Exception raised if there is an issue downloading packages file.
    """


class ImageConditionsException(ImageDownloaderException):
    """
    Exception raised if image metadata does not match conditions.
    """


class PackageVersionException(ImageDownloaderException):
    """
    Exception raised if package does not match version conditions.
    """


class ImageChecksumException(ImageDownloaderException):
    """
    Exception raised if image checksum does not match.
    """


class ImageVersionException(ImageDownloaderException):
    """
    Exception raised when unable to parse image version.
    """


class ImageDownloadException(ImageDownloaderException):
    """
    Exception raised when unable to download image file.
    """
