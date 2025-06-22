"""
Configurations spécifiques pour les connecteurs de réseaux sociaux.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from .validator import ConnectorConfig


class SocialMediaVisibility(str, Enum):
    """Niveaux de visibilité pour les posts sur les réseaux sociaux."""

    PUBLIC = "public"
    CONNECTIONS = "connections"
    PRIVATE = "private"


class TwitterConfig(ConnectorConfig):
    """Configuration pour le connecteur Twitter."""

    bearer_token: str = Field(..., description="Token Bearer pour l'API Twitter")
    api_key: Optional[str] = Field(None, description="Clé API Twitter")
    api_secret: Optional[str] = Field(None, description="Secret API Twitter")
    access_token: Optional[str] = Field(None, description="Token d'accès Twitter")
    access_token_secret: Optional[str] = Field(None, description="Secret du token d'accès Twitter")

    @validator("bearer_token")
    def validate_bearer_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Bearer token must be provided and valid")
        return v


class LinkedInConfig(ConnectorConfig):
    """Configuration pour le connecteur LinkedIn."""

    access_token: str = Field(..., description="Token d'accès OAuth 2.0 LinkedIn")
    client_id: Optional[str] = Field(None, description="ID client de l'application LinkedIn")
    client_secret: Optional[str] = Field(
        None, description="Secret client de l'application LinkedIn"
    )
    default_visibility: SocialMediaVisibility = Field(
        SocialMediaVisibility.PUBLIC, description="Visibilité par défaut des posts"
    )

    @validator("access_token")
    def validate_access_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Access token must be provided and valid")
        return v


class FacebookConfig(ConnectorConfig):
    """Configuration pour le connecteur Facebook."""

    access_token: str = Field(..., description="Token d'accès Facebook")
    page_id: Optional[str] = Field(None, description="ID de la page Facebook (optionnel)")
    app_id: Optional[str] = Field(None, description="ID de l'application Facebook")
    app_secret: Optional[str] = Field(None, description="Secret de l'application Facebook")

    @validator("access_token")
    def validate_access_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Access token must be provided and valid")
        return v


class InstagramConfig(ConnectorConfig):
    """Configuration pour le connecteur Instagram."""

    access_token: str = Field(..., description="Token d'accès Instagram")
    user_id: Optional[str] = Field(None, description="ID utilisateur Instagram")
    business_account: bool = Field(False, description="Compte business Instagram")

    @validator("access_token")
    def validate_access_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Access token must be provided and valid")
        return v


class YouTubeConfig(ConnectorConfig):
    """Configuration pour le connecteur YouTube."""

    api_key: str = Field(..., description="Clé API YouTube Data")
    access_token: Optional[str] = Field(
        None, description="Token d'accès OAuth pour les opérations d'écriture"
    )
    client_id: Optional[str] = Field(None, description="ID client OAuth")
    client_secret: Optional[str] = Field(None, description="Secret client OAuth")
    channel_id: Optional[str] = Field(None, description="ID de la chaîne YouTube")

    @validator("api_key")
    def validate_api_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError("API key must be provided and valid")
        return v


class TikTokConfig(ConnectorConfig):
    """Configuration pour le connecteur TikTok."""

    access_token: str = Field(..., description="Token d'accès TikTok")
    client_key: Optional[str] = Field(None, description="Clé client de l'application TikTok")
    client_secret: Optional[str] = Field(None, description="Secret client de l'application TikTok")

    @validator("access_token")
    def validate_access_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Access token must be provided and valid")
        return v


class GitHubConfig(ConnectorConfig):
    """Configuration pour le connecteur GitHub."""

    access_token: str = Field(..., description="Token d'accès personnel GitHub")
    default_owner: Optional[str] = Field(
        None, description="Propriétaire par défaut pour les opérations"
    )
    default_repo: Optional[str] = Field(
        None, description="Repository par défaut pour les opérations"
    )

    @validator("access_token")
    def validate_access_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Access token must be provided and valid")
        return v


class SocialMediaConfig(BaseModel):
    """Configuration globale pour tous les réseaux sociaux."""

    # Configuration des plateformes
    twitter: Optional[TwitterConfig] = None
    linkedin: Optional[LinkedInConfig] = None
    facebook: Optional[FacebookConfig] = None
    instagram: Optional[InstagramConfig] = None
    youtube: Optional[YouTubeConfig] = None
    tiktok: Optional[TikTokConfig] = None
    github: Optional[GitHubConfig] = None

    # Configuration globale
    max_retries: int = Field(3, description="Nombre maximum de tentatives")
    retry_delay: float = Field(1.0, description="Délai entre les tentatives (secondes)")
    timeout: int = Field(30, description="Timeout des requêtes (secondes)")
    rate_limit_buffer: float = Field(0.1, description="Buffer pour les limites de taux (10%)")

    # Options de publication
    auto_hashtags: bool = Field(False, description="Ajouter automatiquement des hashtags")
    content_validation: bool = Field(True, description="Valider le contenu avant publication")
    duplicate_detection: bool = Field(True, description="Détection des doublons")

    class Config:
        """Configuration Pydantic."""

        use_enum_values = True
        validate_assignment = True

    def get_platform_config(self, platform: str) -> Optional[ConnectorConfig]:
        """
        Récupère la configuration pour une plateforme spécifique.

        Args:
            platform: Nom de la plateforme ('twitter', 'linkedin', etc.)

        Returns:
            Configuration de la plateforme ou None si non configurée.
        """
        return getattr(self, platform.lower(), None)

    def is_platform_configured(self, platform: str) -> bool:
        """
        Vérifie si une plateforme est configurée.

        Args:
            platform: Nom de la plateforme

        Returns:
            True si la plateforme est configurée.
        """
        config = self.get_platform_config(platform)
        return config is not None

    def get_configured_platforms(self) -> list[str]:
        """
        Retourne la liste des plateformes configurées.

        Returns:
            Liste des noms des plateformes configurées.
        """
        platforms = []
        for platform in [
            "twitter",
            "linkedin",
            "facebook",
            "instagram",
            "youtube",
            "tiktok",
            "github",
        ]:
            if self.is_platform_configured(platform):
                platforms.append(platform)
        return platforms


# Factory pour créer les configurations
def create_social_config_from_dict(config_dict: Dict[str, Any]) -> SocialMediaConfig:
    """
    Crée une configuration de réseaux sociaux à partir d'un dictionnaire.

    Args:
        config_dict: Dictionnaire de configuration

    Returns:
        Instance de SocialMediaConfig
    """
    # Traitement des configurations de plateformes
    platform_configs = {}

    if "twitter" in config_dict:
        platform_configs["twitter"] = TwitterConfig(**config_dict["twitter"])

    if "linkedin" in config_dict:
        platform_configs["linkedin"] = LinkedInConfig(**config_dict["linkedin"])

    if "facebook" in config_dict:
        platform_configs["facebook"] = FacebookConfig(**config_dict["facebook"])

    if "instagram" in config_dict:
        platform_configs["instagram"] = InstagramConfig(**config_dict["instagram"])

    if "youtube" in config_dict:
        platform_configs["youtube"] = YouTubeConfig(**config_dict["youtube"])

    if "tiktok" in config_dict:
        platform_configs["tiktok"] = TikTokConfig(**config_dict["tiktok"])

    if "github" in config_dict:
        platform_configs["github"] = GitHubConfig(**config_dict["github"])

    # Configuration globale
    global_config = {
        k: v
        for k, v in config_dict.items()
        if k not in ["twitter", "linkedin", "facebook", "instagram", "youtube", "tiktok", "github"]
    }

    return SocialMediaConfig(**{**platform_configs, **global_config})
