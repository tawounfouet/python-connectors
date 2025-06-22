"""
Exceptions personnalisées pour les connecteurs.
"""


class ConnectorError(Exception):
    """Exception de base pour tous les connecteurs."""
    pass


class ConnectionError(ConnectorError):
    """Erreur lors de la connexion à un système externe."""
    pass


class ConfigurationError(ConnectorError):
    """Erreur de configuration du connecteur."""
    pass


class TimeoutError(ConnectorError):
    """Erreur de timeout lors d'une opération."""
    pass


class AuthenticationError(ConnectorError):
    """Erreur d'authentification."""
    pass


class RetryExhaustedError(ConnectorError):
    """Erreur après épuisement des tentatives de retry."""
    pass


# Exceptions spécifiques aux réseaux sociaux
class SocialMediaConnectionError(ConnectionError):
    """Erreur de connexion spécifique aux réseaux sociaux."""
    pass


class SocialMediaAuthenticationError(AuthenticationError):
    """Erreur d'authentification spécifique aux réseaux sociaux."""
    pass


class SocialMediaAPIError(ConnectorError):
    """Erreur générale de l'API des réseaux sociaux."""
    pass


class SocialMediaRateLimitError(SocialMediaAPIError):
    """Erreur de limite de taux dépassée."""
    pass


class SocialMediaContentError(SocialMediaAPIError):
    """Erreur liée au contenu publié (trop long, format invalide, etc.)."""
    pass


class SocialMediaPermissionError(SocialMediaAPIError):
    """Erreur de permissions insuffisantes."""
    pass
