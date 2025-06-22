"""
Configuration utilities for loading settings from INI files and environment variables.
"""

import configparser
import os
from typing import Dict, Any, Optional

# Charger les variables d'environnement depuis .env si disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv n'est pas installé, pas grave


class ConfigLoader:
    """Utility class for loading configuration from INI files."""
    
    def __init__(self, config_path: str = "config.ini"):
        """
        Initialize the config loader.
        
        Args:
            config_path: Path to the INI configuration file
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        if os.path.exists(config_path):
            self.config.read(config_path)
    
    def get_connector_config(self, connector_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific connector type.
        
        Args:
            connector_type: Type of connector (postgresql, mysql, etc.)
            
        Returns:
            Dictionary containing the configuration
            
        Raises:
            ValueError: If connector type is not found in config
        """
        if connector_type not in self.config:
            raise ValueError(f"Configuration for '{connector_type}' not found in {self.config_path}")
        
        config_dict = dict(self.config[connector_type])
        
        # Remove empty values first (only for string values)
        cleaned_config = {}
        for k, v in config_dict.items():
            if isinstance(v, str) and v.strip():
                cleaned_config[k] = v.strip()
            elif not isinstance(v, str):
                cleaned_config[k] = v
        
        # Convert specific types
        if 'port' in cleaned_config:
            cleaned_config['port'] = int(cleaned_config['port'])
        
        if 'timeout' in cleaned_config:
            cleaned_config['timeout'] = int(cleaned_config['timeout'])
            
        if 'metrics_enabled' in cleaned_config:
            cleaned_config['metrics_enabled'] = cleaned_config['metrics_enabled'].lower() == 'true'
        
        config_dict = cleaned_config
        
        return config_dict
    
    def get_section_names(self) -> list:
        """Get all available section names (connector types)."""
        return list(self.config.sections())
    
    def has_section(self, section_name: str) -> bool:
        """Check if a section exists in the configuration."""
        return self.config.has_section(section_name)


# Global instance for easy access
config_loader = ConfigLoader()


def load_config_from_env(connector_type: str) -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Args:
        connector_type: Type of connector (postgresql, mysql, etc.)
        
    Returns:
        Configuration dictionary loaded from environment variables
    """
    config = {}
    prefix = connector_type.upper()
    
    # Mapping des variables d'environnement communes
    env_mappings = {
        'postgresql': {
            'host': f'{prefix}_HOST',
            'port': f'{prefix}_PORT',
            'database': f'{prefix}_DATABASE',
            'username': f'{prefix}_USERNAME',
            'password': f'{prefix}_PASSWORD',
            'timeout': f'{prefix}_TIMEOUT',
            'sslmode': f'{prefix}_SSLMODE',
            'metrics_enabled': f'{prefix}_METRICS_ENABLED'
        },
        'mysql': {
            'host': f'{prefix}_HOST',
            'port': f'{prefix}_PORT',
            'database': f'{prefix}_DATABASE',
            'username': f'{prefix}_USERNAME',
            'password': f'{prefix}_PASSWORD',
            'timeout': f'{prefix}_TIMEOUT',
            'metrics_enabled': f'{prefix}_METRICS_ENABLED'
        },
        's3': {
            'aws_access_key_id': 'AWS_ACCESS_KEY_ID',
            'aws_secret_access_key': 'AWS_SECRET_ACCESS_KEY',
            'region_name': 'AWS_REGION',
            'bucket_name': 'S3_BUCKET_NAME',
            'metrics_enabled': f'{prefix}_METRICS_ENABLED'
        }
    }
    
    if connector_type in env_mappings:
        for config_key, env_key in env_mappings[connector_type].items():
            value = os.getenv(env_key)
            if value:
                # Conversion des types
                if config_key == 'port' or config_key == 'timeout':
                    config[config_key] = int(value)
                elif config_key == 'metrics_enabled':
                    config[config_key] = value.lower() == 'true'
                else:
                    config[config_key] = value
    
    return config


def load_config(connector_type: str, config_file: Optional[str] = None, prefer_env: bool = False) -> Dict[str, Any]:
    """
    Convenience function to load configuration for a connector type.
    
    Args:
        connector_type: Type of connector
        config_file: Optional path to config file (uses default if None)
        prefer_env: If True, try environment variables first, then INI file
        
    Returns:
        Configuration dictionary
    """
    config = {}
    
    if prefer_env:
        # Essayer d'abord les variables d'environnement
        config = load_config_from_env(connector_type)
        if config:
            return config
        
        # Fallback vers le fichier INI
        try:
            if config_file:
                loader = ConfigLoader(config_file)
            else:
                loader = config_loader
            return loader.get_connector_config(connector_type)
        except Exception:
            return config
    else:
        # Essayer d'abord le fichier INI
        try:
            if config_file:
                loader = ConfigLoader(config_file)
            else:
                loader = config_loader
            return loader.get_connector_config(connector_type)
        except Exception:
            # Fallback vers les variables d'environnement
            return load_config_from_env(connector_type)
