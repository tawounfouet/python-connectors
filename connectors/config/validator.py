"""
Configuration et validation pour les connecteurs.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class RetryConfig(BaseModel):
    """Configuration des tentatives de retry."""

    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_factor: float = Field(default=2.0, ge=1.0)
    initial_delay: float = Field(default=1.0, ge=0.1)
    max_delay: float = Field(default=60.0, ge=1.0)


class ConnectorConfig(BaseModel):
    """Configuration de base pour tous les connecteurs."""

    timeout: int = Field(default=30, ge=1, le=300)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    pool_size: int = Field(default=10, ge=1, le=100)
    log_level: LogLevel = Field(default=LogLevel.INFO)
    metrics_enabled: bool = Field(default=True)
    extra_config: Dict[str, Any] = Field(default_factory=dict)


class DatabaseConfig(ConnectorConfig):
    """Configuration spécifique aux bases de données."""

    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_enabled: bool = Field(default=False)
    connection_string: Optional[str] = None


class S3Config(ConnectorConfig):
    """Configuration pour Amazon S3."""

    access_key_id: str
    secret_access_key: str
    bucket_name: str
    region: str = Field(default="us-east-1")
    endpoint_url: Optional[str] = None


class OAuthConfig(BaseModel):
    """Configuration pour l'authentification OAuth 2.0."""

    client_id: str = Field(..., description="ID client OAuth 2.0")
    client_secret: str = Field(..., description="Secret client OAuth 2.0")
    refresh_token: str = Field(..., description="Token de rafraîchissement OAuth 2.0")
    access_token: Optional[str] = Field(
        None, description="Token d'accès OAuth 2.0 (optionnel, peut être généré automatiquement)"
    )
    token_expiry: Optional[int] = Field(None, description="Timestamp d'expiration du token d'accès")


class SMTPConfig(ConnectorConfig):
    """Configuration pour SMTP."""

    host: str
    port: int = Field(default=587)
    username: str
    password: Optional[str] = None
    use_tls: bool = Field(default=True)
    use_ssl: bool = Field(default=False)
    use_oauth: bool = Field(default=False, description="Utiliser l'authentification OAuth 2.0")
    oauth: Optional[OAuthConfig] = Field(None, description="Configuration OAuth si use_oauth=True")


class SnowflakeConfig(ConnectorConfig):
    """Configuration spécialisée pour Snowflake."""

    # Paramètres de connexion de base
    account: str = Field(..., description="Nom du compte Snowflake")
    username: str = Field(..., description="Nom d'utilisateur")
    password: str = Field(..., description="Mot de passe")

    # Paramètres optionnels Snowflake
    warehouse: Optional[str] = Field(None, description="Nom du warehouse Snowflake")
    database: Optional[str] = Field(None, description="Nom de la base de données")
    schema_name: Optional[str] = Field(None, alias="schema", description="Nom du schéma")
    role: Optional[str] = Field(None, description="Rôle Snowflake à utiliser")

    # Paramètres d'authentification
    authenticator: Optional[str] = Field("snowflake", description="Type d'authentification")

    class Config:
        """Configuration Pydantic."""

        extra = "allow"  # Permet des champs supplémentaires
        populate_by_name = True  # Permet l'utilisation d'alias et du nom réel

    def get_connection_params(self) -> Dict[str, Any]:
        """Retourne les paramètres de connexion pour Snowflake."""
        params = {
            "account": self.account,
            "user": self.username,
            "password": self.password,
            "authenticator": self.authenticator,
        }

        # Ajouter les paramètres optionnels s'ils sont définis
        if self.warehouse:
            params["warehouse"] = self.warehouse
        if self.database:
            params["database"] = self.database
        if self.schema_name:
            params["schema"] = self.schema_name
        if self.role:
            params["role"] = self.role

        return params
