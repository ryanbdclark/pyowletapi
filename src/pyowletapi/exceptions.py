class OwletError(Exception):
    """Generic exception"""


class OwletConnectionError(OwletError):
    """When a connection error occurs"""


class OwletAuthenticationError(OwletError):
    """When login details are incorrect"""


class OwletDevicesError(OwletError):
    """when no devices are found"""
