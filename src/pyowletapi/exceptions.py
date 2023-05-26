class OwletError(Exception):
    """Generic exception"""


class OwletConnectionError(OwletError):
    """When a connection error occurs"""


class OwletAuthenticationError(OwletError):
    """When login details are incorrect"""


class OwletPasswordError(OwletError):
    """When password is incorrect"""


class OwletEmailError(OwletError):
    """When email is incorrect"""

class OwletCredentialsError(OwletError):
    """When login creds are, no descript, api no longer returns if this is username or password that is incorrect"""


class OwletDevicesError(OwletError):
    """when no devices are found"""
