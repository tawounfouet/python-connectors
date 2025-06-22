"""
Exceptions pour le module connectors.
"""

from .connector_exceptions import (
    ConnectorError,
    ConnectionError,
    ConfigurationError,
    TimeoutError,
    AuthenticationError,
    RetryExhaustedError
)

__all__ = [
    'ConnectorError',
    'ConnectionError',
    'ConfigurationError', 
    'TimeoutError',
    'AuthenticationError',
    'RetryExhaustedError'
]
