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
