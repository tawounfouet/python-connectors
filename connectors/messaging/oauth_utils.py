"""
Utilitaire pour la gestion de l'authentification OAuth 2.0.
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional, Tuple

# Imports for OAuth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Global logger
logger = logging.getLogger(__name__)


class OAuth2Manager:
    """
    Gestionnaire d'authentification OAuth 2.0.

    Cette classe gère la récupération et le rafraîchissement des tokens OAuth 2.0,
    en particulier pour les services Google comme Gmail.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: Optional[str] = None,
        access_token: Optional[str] = None,
        token_expiry: Optional[int] = None,
        scopes: Optional[list] = None,
        token_file: Optional[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.token_expiry = token_expiry
        self.scopes = scopes or []
        self.token_file = token_file
        self.credentials = None

    def _load_credentials_from_file(self) -> bool:
        """
        Charge les credentials depuis un fichier de token.

        Returns:
            True si les credentials ont été chargées avec succès, False sinon
        """
        if not self.token_file or not os.path.exists(self.token_file):
            return False

        try:
            with open(self.token_file, "r") as f:
                token_info = json.load(f)

            self.credentials = Credentials(
                token=token_info.get("access_token"),
                refresh_token=token_info.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes,
            )

            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.refresh_credentials()
                return True

            return self.credentials is not None and not self.credentials.expired
        except Exception as e:
            logger.error(f"Error loading credentials from file: {e}")
            return False

    def _save_credentials_to_file(self) -> bool:
        """
        Sauvegarde les credentials dans un fichier de token.

        Returns:
            True si les credentials ont été sauvegardées avec succès, False sinon
        """
        if not self.token_file or not self.credentials:
            return False

        try:
            token_info = {
                "access_token": self.credentials.token,
                "refresh_token": self.credentials.refresh_token,
                "token_uri": self.credentials.token_uri,
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "scopes": self.credentials.scopes,
                "expiry": self.credentials.expiry.timestamp() if self.credentials.expiry else None,
            }

            with open(self.token_file, "w") as f:
                json.dump(token_info, f)

            return True
        except Exception as e:
            logger.error(f"Error saving credentials to file: {e}")
            return False

    def generate_oauth_url(self, redirect_uri: str = "http://localhost") -> str:
        """
        Génère une URL d'autorisation OAuth 2.0.

        Args:
            redirect_uri: URI de redirection après authentification

        Returns:
            URL à ouvrir dans un navigateur pour autoriser l'application
        """
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.scopes,
        )

        auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

        return auth_url

    def get_token_from_code(
        self, code: str, redirect_uri: str = "http://localhost"
    ) -> Dict[str, Any]:
        """
        Obtient un token à partir d'un code d'autorisation.

        Args:
            code: Code d'autorisation retourné par le serveur OAuth
            redirect_uri: URI de redirection utilisé pour l'autorisation

        Returns:
            Dictionnaire contenant les informations du token
        """
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.scopes,
        )

        flow.fetch_token(code=code)
        self.credentials = flow.credentials

        if self.token_file:
            self._save_credentials_to_file()

        return {
            "access_token": self.credentials.token,
            "refresh_token": self.credentials.refresh_token,
            "expiry": self.credentials.expiry.timestamp() if self.credentials.expiry else None,
        }

    def get_access_token(self) -> Tuple[str, int]:
        """
        Récupère un token d'accès valide, en le rafraîchissant si nécessaire.

        Returns:
            Tuple (access_token, expiry_timestamp)

        Raises:
            ValueError: Si aucun token d'accès ou de rafraîchissement n'est disponible
        """
        # Si on a un fichier de token, essayer de charger les credentials
        if self.token_file and os.path.exists(self.token_file):
            self._load_credentials_from_file()

        # Si on n'a pas de credentials mais des tokens en paramètres
        elif not self.credentials and (self.access_token or self.refresh_token):
            self.credentials = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes,
            )

        # Si toujours pas de credentials, erreur
        if not self.credentials:
            raise ValueError(
                "No credentials available. Use generate_oauth_url() to get authorization"
            )

        # Rafraîchir le token si expiré et qu'on a un refresh_token
        if self.credentials.expired and self.credentials.refresh_token:
            self.refresh_credentials()

        # Si token expiré et pas de refresh_token, erreur
        elif self.credentials.expired:
            raise ValueError("Access token expired and no refresh token available")

        return self.credentials.token, int(time.time() + 3600)  # Par défaut, validité d'une heure

    def refresh_credentials(self) -> bool:
        """
        Rafraîchit les credentials avec le refresh_token.

        Returns:
            True si le rafraîchissement a réussi, False sinon
        """
        if not self.credentials or not self.credentials.refresh_token:
            return False

        try:
            self.credentials.refresh(Request())

            # Mettre à jour les attributs
            self.access_token = self.credentials.token
            self.refresh_token = self.credentials.refresh_token
            self.token_expiry = (
                int(self.credentials.expiry.timestamp()) if self.credentials.expiry else None
            )

            # Sauvegarder si un fichier est spécifié
            if self.token_file:
                self._save_credentials_to_file()

            return True
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False

    def get_auth_string(self, username: str) -> str:
        """
        Génère la chaîne d'authentification au format XOAUTH2.

        Args:
            username: Adresse email de l'utilisateur

        Returns:
            Chaîne d'authentification XOAUTH2 encodée en base64
        """
        import base64

        access_token, _ = self.get_access_token()
        auth_string = f"user={username}\1auth=Bearer {access_token}\1\1"
        return base64.b64encode(auth_string.encode()).decode()


# Fonctions d'aide


def generate_gmail_oauth_config(
    client_id: str, client_secret: str, email: str, token_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Génère une configuration OAuth pour Gmail avec les scopes nécessaires.

    Args:
        client_id: ID client OAuth
        client_secret: Secret client OAuth
        email: Adresse email de l'utilisateur
        token_file: Fichier de sauvegarde du token (optionnel)

    Returns:
        Configuration OAuth complète pour Gmail
    """
    scopes = [
        "https://mail.google.com/",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.send",
    ]

    manager = OAuth2Manager(
        client_id=client_id, client_secret=client_secret, scopes=scopes, token_file=token_file
    )

    # Si on a un fichier de token, on essaie de charger les credentials
    if token_file and os.path.exists(token_file):
        loaded = manager._load_credentials_from_file()
        if loaded:
            access_token, expiry = manager.get_access_token()
            return {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": manager.refresh_token,
                "access_token": access_token,
                "token_expiry": expiry,
            }

    # Sinon on renvoie juste la config de base
    return {"client_id": client_id, "client_secret": client_secret}
