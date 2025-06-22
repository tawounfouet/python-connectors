"""
Configuration pour le module connectors.
"""

from .validator import (
    ConnectorConfig,
    DatabaseConfig,
    S3Config,
    SMTPConfig,
    SnowflakeConfig,
    RetryConfig,
    LogLevel
)

from .loader import ConfigLoader, load_config, load_config_from_env, config_loader

from .social_media import (
    SocialMediaConfig,
    TwitterConfig,
    LinkedInConfig,
    FacebookConfig,
    InstagramConfig,
    YouTubeConfig,
    TikTokConfig,
    SocialMediaVisibility,
    create_social_config_from_dict
)

__all__ = [
    'ConnectorConfig',
    'DatabaseConfig', 
    'S3Config',
    'SMTPConfig',
    'SnowflakeConfig',
    'RetryConfig',
    'LogLevel',
    'ConfigLoader',
    'load_config',
    'load_config_from_env',
    'config_loader',
    # Configurations réseaux sociaux
    'SocialMediaConfig',
    'TwitterConfig',
    'LinkedInConfig',
    'FacebookConfig',
    'InstagramConfig',
    'YouTubeConfig',
    'TikTokConfig',
    'SocialMediaVisibility',
    'create_social_config_from_dict'
]
