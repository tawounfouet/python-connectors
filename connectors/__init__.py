"""
Module connectors - Connecteurs réutilisables pour systèmes externes.
"""

import os
from .utils.logger import setup_logger, global_logger
from .base import BaseConnector, DatabaseConnector, FileSystemConnector, MessagingConnector
from .registry import (
    registry,
    register_connector,
    create_connector,
    get_connector,
    list_available_connectors,
)
from .config import (
    ConnectorConfig,
    DatabaseConfig,
    S3Config,
    SMTPConfig,
    SnowflakeConfig,
    RetryConfig,
    LogLevel,
)
from .exceptions import (
    ConnectorError,
    ConnectionError,
    ConfigurationError,
    TimeoutError,
    AuthenticationError,
    RetryExhaustedError,
)


# Import automatique des connecteurs pour les enregistrer
def _load_connectors():
    """Charge automatiquement tous les connecteurs disponibles."""
    logger = global_logger

    # Import des connecteurs DB
    try:
        from .db import postgresql

        logger.debug("PostgreSQL connector loaded")
    except ImportError as e:
        logger.debug(f"PostgreSQL connector not available: {e}")

    try:
        from .db import mysql

        logger.debug("MySQL connector loaded")
    except ImportError as e:
        logger.debug(f"MySQL connector not available: {e}")

    try:
        from .db import sqlserver

        logger.debug("SQL Server connector loaded")
    except ImportError as e:
        logger.debug(f"SQL Server connector not available: {e}")

    try:
        from .db import snowflake

        logger.debug("Snowflake connector loaded")
    except ImportError as e:
        logger.debug(f"Snowflake connector not available: {e}")

    # Import des connecteurs Data Lake
    try:
        from .data_lake import s3

        logger.debug("S3 connector loaded")
    except ImportError as e:
        logger.debug(f"S3 connector not available: {e}")

    # Import des connecteurs réseaux sociaux
    try:
        from .social_media import twitter

        logger.debug("Twitter connector loaded")
    except ImportError as e:
        logger.debug(f"Twitter connector not available: {e}")

    try:
        from .social_media import facebook

        logger.debug("Facebook connector loaded")
    except ImportError as e:
        logger.debug(f"Facebook connector not available: {e}")

    try:
        from .social_media import instagram

        logger.debug("Instagram connector loaded")
    except ImportError as e:
        logger.debug(f"Instagram connector not available: {e}")

    try:
        from .social_media import linkedin

        logger.debug("LinkedIn connector loaded")
    except ImportError as e:
        logger.debug(f"LinkedIn connector not available: {e}")

    try:
        from .social_media import youtube

        logger.debug("YouTube connector loaded")
    except ImportError as e:
        logger.debug(f"YouTube connector not available: {e}")

    try:
        from .social_media import tiktok

        logger.debug("TikTok connector loaded")
    except ImportError as e:
        logger.debug(f"TikTok connector not available: {e}")

    try:
        from .social_media import github

        logger.debug("GitHub connector loaded")
    except ImportError as e:
        logger.debug(f"GitHub connector not available: {e}")

    # Import des connecteurs de messagerie
    try:
        from .messaging import smtp

        logger.debug("SMTP/Gmail connectors loaded")
    except ImportError as e:
        logger.debug(f"SMTP/Gmail connectors not available: {e}")

    try:
        from .messaging import imap

        logger.debug("IMAP/Gmail IMAP connectors loaded")
    except ImportError as e:
        logger.debug(f"IMAP/Gmail IMAP connectors not available: {e}")

    # TODO: Ajouter d'autres connecteurs ici


# Charger les connecteurs automatiquement à l'import
_load_connectors()

__version__ = "0.1.0"

__all__ = [
    # Classes de base
    "BaseConnector",
    "DatabaseConnector",
    "FileSystemConnector",
    "MessagingConnector",
    # Registre
    "registry",
    "register_connector",
    "create_connector",
    "get_connector",
    "list_available_connectors",
    # Configuration
    "ConnectorConfig",
    "DatabaseConfig",
    "S3Config",
    "SMTPConfig",
    "SnowflakeConfig",
    "RetryConfig",
    "LogLevel",
    # Exceptions
    "ConnectorError",
    "ConnectionError",
    "ConfigurationError",
    "TimeoutError",
    "AuthenticationError",
    "RetryExhaustedError",
    # Logging
    "setup_logger",
]

# Exporter setup_logger pour que les utilisateurs puissent configurer le logger
from .utils.logger import setup_logger
