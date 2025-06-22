"""
Connecteur IMAP pour la lecture d'emails.

Ce module fournit un connecteur pour interagir avec les serveurs IMAP,
permettant de lister, lire et gérer les emails dans une boîte de réception.
"""

import imaplib
import email
from email.header import decode_header
import logging
import re
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple

# Import des utilitaires OAuth
from .oauth_utils import OAuth2Manager

try:
    from connectors.base import MessagingConnector
    from connectors.registry import register_connector
    from connectors.exceptions import ConnectionError, ConfigurationError, AuthenticationError
    from connectors.config import ConnectorConfig
    from connectors.config.validator import OAuthConfig
except ImportError:
    # Import relatif si l'import absolu échoue
    from ..base import MessagingConnector
    from ..registry import register_connector
    from ..exceptions import ConnectionError, ConfigurationError, AuthenticationError
    from ..config import ConnectorConfig
    from ..config.validator import OAuthConfig

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IMAPConfig(ConnectorConfig):
    """Configuration pour les connecteurs IMAP."""

    host: str = Field(..., description="Adresse du serveur IMAP")
    port: int = Field(default=993, description="Port du serveur IMAP")
    username: str = Field(..., description="Nom d'utilisateur")
    password: Optional[str] = Field(
        None, description="Mot de passe (non requis si OAuth est utilisé)"
    )
    use_ssl: bool = Field(default=True, description="Utiliser SSL pour la connexion")
    mailbox: str = Field(default="INBOX", description="Boîte à lister par défaut")
    use_oauth: bool = Field(default=False, description="Utiliser l'authentification OAuth 2.0")
    oauth: Optional[OAuthConfig] = Field(None, description="Configuration OAuth si use_oauth=True")


@register_connector("imap")
class IMAPConnector(MessagingConnector):
    """Connecteur pour serveur IMAP."""

    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        super().__init__(config, connector_name)

        # Validation de la configuration
        try:
            self.imap_config = IMAPConfig(**config)
        except Exception as e:
            raise ConfigurationError(f"Invalid IMAP configuration: {e}")

        self.imap_client = None

    def connect(self):
        """Établit la connexion au serveur IMAP."""
        try:
            if self.imap_config.use_ssl:
                self.imap_client = imaplib.IMAP4_SSL(
                    host=self.imap_config.host, port=self.imap_config.port
                )
            else:
                self.imap_client = imaplib.IMAP4(
                    host=self.imap_config.host, port=self.imap_config.port
                )

            # Authentification
            if self.imap_config.use_oauth and self.imap_config.oauth:
                # Utiliser OAuth 2.0
                self._oauth_login()
            elif self.imap_config.password:
                # Utiliser l'authentification par mot de passe classique
                self.imap_client.login(self.imap_config.username, self.imap_config.password)
            else:
                raise ConfigurationError(
                    "No authentication method provided. Set either password or OAuth configuration"
                )

            self.logger.info(
                f"Connected to IMAP server: {self.imap_config.host}:{self.imap_config.port}"
            )
            self._connected = True

        except Exception as e:
            self.logger.error(f"Failed to connect to IMAP server: {e}")
            raise ConnectionError(f"Failed to connect to IMAP server: {e}")

    def _oauth_login(self):
        """Authentification par OAuth 2.0."""
        if not self.imap_config.oauth:
            raise ConfigurationError("OAuth configuration is missing")

        try:
            # Créer le gestionnaire OAuth
            oauth_manager = OAuth2Manager(
                client_id=self.imap_config.oauth.client_id,
                client_secret=self.imap_config.oauth.client_secret,
                refresh_token=self.imap_config.oauth.refresh_token,
                access_token=self.imap_config.oauth.access_token,
            )

            # Générer le token XOAUTH2
            auth_string = oauth_manager.get_auth_string(self.imap_config.username)

            # Le mécanisme d'authentification dépend du serveur
            if "gmail" in self.imap_config.host:
                # Pour Gmail, on peut utiliser la commande AUTHENTICATE XOAUTH2
                self.imap_client.authenticate("XOAUTH2", lambda x: auth_string)
                self.logger.info("Authenticated with Gmail using OAuth 2.0")
            else:
                # Pour d'autres serveurs, il faudra peut-être adapter cette partie
                self.logger.warning(
                    "OAuth authentication might not be supported by this IMAP server"
                )
                self.imap_client.authenticate("XOAUTH2", lambda x: auth_string)

        except Exception as e:
            self.logger.error(f"OAuth authentication failed: {e}")
            raise AuthenticationError(f"IMAP OAuth authentication failed: {e}")

    def disconnect(self):
        """Ferme la connexion au serveur IMAP."""
        if self.imap_client:
            try:
                self.imap_client.logout()
                self.logger.debug("Disconnected from IMAP server")
            except Exception as e:
                self.logger.warning(f"Error while disconnecting from IMAP server: {e}")
            finally:
                self.imap_client = None
                self._connected = False

    def test_connection(self) -> bool:
        """Teste la connexion au serveur IMAP."""
        if not self._connected:
            try:
                self.connect()
                # Liste des boîtes disponibles pour vérifier que tout fonctionne
                self.list_mailboxes()
                return True
            except Exception as e:
                self.logger.error(f"IMAP connection test failed: {e}")
                return False
            finally:
                if self._connected:
                    self.disconnect()
        return True

    def list_mailboxes(self) -> List[str]:
        """
        Liste toutes les boîtes email disponibles.

        Returns:
            Liste des noms de boîtes
        """
        if not self._connected:
            raise ConnectionError("Not connected to IMAP server")

        def _list_mailboxes():
            status, mailboxes = self.imap_client.list()
            if status != "OK":
                raise ConnectionError(f"Failed to list mailboxes: {status}")

            result = []
            for mailbox in mailboxes:
                if isinstance(mailbox, bytes):
                    # Décodage du nom de la boîte
                    parts = mailbox.decode().split(' "." ')
                    if len(parts) > 1:
                        # Enlever les guillemets en début et fin si présents
                        name = parts[-1].strip('"')
                        result.append(name)

            return result

        return self.execute_with_metrics("list_mailboxes", _list_mailboxes)

    def select_mailbox(self, mailbox: str = None) -> int:
        """
        Sélectionne une boîte email et retourne le nombre de messages.

        Args:
            mailbox: Nom de la boîte (par défaut: boîte configurée)

        Returns:
            Nombre de messages dans la boîte
        """
        if not self._connected:
            raise ConnectionError("Not connected to IMAP server")

        mailbox = mailbox or self.imap_config.mailbox

        def _select_mailbox():
            status, data = self.imap_client.select(mailbox)
            if status != "OK":
                raise ConnectionError(f"Failed to select mailbox {mailbox}: {status}")

            # data[0] contient le nombre d'emails dans la boîte
            return int(data[0])

        return self.execute_with_metrics("select_mailbox", _select_mailbox)

    def _decode_email_header(self, header_value: str) -> str:
        """
        Décode les valeurs d'en-tête qui peuvent être encodées.

        Args:
            header_value: Valeur d'en-tête à décoder

        Returns:
            Valeur décodée
        """
        if not header_value:
            return ""

        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                if encoding:
                    try:
                        part = part.decode(encoding)
                    except:
                        part = part.decode("utf-8", errors="replace")
                else:
                    part = part.decode("utf-8", errors="replace")
            decoded_parts.append(part)

        return "".join(decoded_parts)

    def _parse_email(self, email_id: str, email_data: bytes) -> Dict[str, Any]:
        """
        Parse un email brut et le convertit en dictionnaire.

        Args:
            email_id: ID de l'email
            email_data: Données brutes de l'email

        Returns:
            Dictionnaire contenant les informations de l'email
        """
        msg = email.message_from_bytes(email_data)

        # Extraction des en-têtes
        subject = self._decode_email_header(msg["Subject"])
        from_header = self._decode_email_header(msg["From"])
        to_header = self._decode_email_header(msg["To"])
        date_str = msg["Date"]

        # Conversion de la date en format standard
        date = None
        if date_str:
            try:
                # Les formats de date peuvent varier, donc on essaie plusieurs approches
                date_obj = email.utils.parsedate_to_datetime(date_str)
                date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                date = date_str

        # Extraction du corps du message
        body = ""
        html = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Ignorer les pièces jointes
                if "attachment" in content_disposition:
                    continue

                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset()
                    if charset:
                        try:
                            decoded_payload = payload.decode(charset)
                        except:
                            decoded_payload = payload.decode("utf-8", errors="replace")
                    else:
                        decoded_payload = payload.decode("utf-8", errors="replace")

                    if content_type == "text/plain":
                        body = decoded_payload
                    elif content_type == "text/html":
                        html = decoded_payload
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset()
                if charset:
                    try:
                        decoded_payload = payload.decode(charset)
                    except:
                        decoded_payload = payload.decode("utf-8", errors="replace")
                else:
                    decoded_payload = payload.decode("utf-8", errors="replace")

                if msg.get_content_type() == "text/plain":
                    body = decoded_payload
                elif msg.get_content_type() == "text/html":
                    html = decoded_payload

        # Liste des pièces jointes
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue

                filename = part.get_filename()
                if filename:
                    attachments.append(
                        {
                            "filename": self._decode_email_header(filename),
                            "content_type": part.get_content_type(),
                        }
                    )

        # Construction du résultat
        return {
            "id": email_id,
            "subject": subject,
            "from": from_header,
            "to": to_header,
            "date": date,
            "body": body,
            "html": html,
            "has_attachments": len(attachments) > 0,
            "attachments": attachments,
        }

    def receive_messages(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Reçoit les messages d'une boîte email.

        Args:
            **kwargs: Options additionnelles
                - mailbox: Nom de la boîte à lire
                - limit: Nombre maximum de messages à récupérer
                - unread_only: Si True, récupère uniquement les messages non lus
                - newest_first: Si True, récupère les messages les plus récents d'abord

        Returns:
            Liste de dictionnaires contenant les informations des messages
        """
        if not self._connected:
            raise ConnectionError("Not connected to IMAP server")

        def _receive_messages():
            mailbox = kwargs.get("mailbox", self.imap_config.mailbox)
            limit = kwargs.get("limit", 10)
            unread_only = kwargs.get("unread_only", False)
            newest_first = kwargs.get("newest_first", True)

            self.select_mailbox(mailbox)

            # Construction de la requête
            search_criteria = "UNSEEN" if unread_only else "ALL"

            # Exécution de la recherche
            status, data = self.imap_client.search(None, search_criteria)
            if status != "OK":
                raise ConnectionError(f"Failed to search emails: {status}")

            # Liste des IDs d'emails
            email_ids = data[0].split()
            if not email_ids:
                return []

            # Si on veut les plus récents d'abord
            if newest_first:
                email_ids = reversed(email_ids)

            # Limiter le nombre de messages
            email_ids = list(email_ids)[:limit]

            results = []

            # Récupération des messages
            for email_id in email_ids:
                status, data = self.imap_client.fetch(email_id, "(RFC822)")
                if status == "OK":
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            email_data = response_part[1]
                            email_info = self._parse_email(email_id.decode(), email_data)
                            results.append(email_info)

            return results

        return self.execute_with_metrics("receive_messages", _receive_messages)

    def mark_as_read(self, email_ids: List[str], mailbox: str = None) -> bool:
        """
        Marque des emails comme lus.

        Args:
            email_ids: Liste des IDs d'emails à marquer
            mailbox: Nom de la boîte (par défaut: boîte configurée)

        Returns:
            True si l'opération a réussi
        """
        if not self._connected:
            raise ConnectionError("Not connected to IMAP server")

        def _mark_as_read():
            self.select_mailbox(mailbox)

            for email_id in email_ids:
                # Convertir en bytes si nécessaire
                if isinstance(email_id, str):
                    email_id = email_id.encode()

                self.imap_client.store(email_id, "+FLAGS", "\\Seen")

            return True

        return self.execute_with_metrics("mark_as_read", _mark_as_read)

    def delete_messages(self, email_ids: List[str], mailbox: str = None) -> bool:
        """
        Supprime des emails.

        Args:
            email_ids: Liste des IDs d'emails à supprimer
            mailbox: Nom de la boîte (par défaut: boîte configurée)

        Returns:
            True si l'opération a réussi
        """
        if not self._connected:
            raise ConnectionError("Not connected to IMAP server")

        def _delete_messages():
            self.select_mailbox(mailbox)

            for email_id in email_ids:
                # Convertir en bytes si nécessaire
                if isinstance(email_id, str):
                    email_id = email_id.encode()

                # Marquer comme supprimé
                self.imap_client.store(email_id, "+FLAGS", "\\Deleted")

            # Appliquer les suppressions
            self.imap_client.expunge()

            return True

        return self.execute_with_metrics("delete_messages", _delete_messages)

    def send_message(self, message: str, recipient: str, **kwargs):
        """
        Non implémenté pour IMAP (utiliser un connecteur SMTP pour l'envoi).

        Raises:
            NotImplementedError: Cette fonction n'est pas disponible pour IMAP
        """
        raise NotImplementedError(
            "IMAP connector does not support sending messages. Use SMTP instead."
        )


@register_connector("gmail_imap")
class GmailIMAPConnector(IMAPConnector):
    """Connecteur IMAP spécifique pour Gmail."""

    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        # Préparation de la configuration spécifique à Gmail
        gmail_config = config.copy()
        gmail_config.update({"host": "imap.gmail.com", "port": 993, "use_ssl": True})

        # Si OAuth est activé, il faut s'assurer que certains paramètres sont présents
        if config.get("use_oauth", False):
            if not config.get("oauth"):
                raise ConfigurationError("OAuth is enabled but OAuth configuration is missing")

            # Pour Gmail, le scope minimal est 'https://mail.google.com/'
            scopes = config.get("oauth_scopes", ["https://mail.google.com/"])
            self.logger.info(f"OAuth configuration detected for Gmail with scopes: {scopes}")

        super().__init__(gmail_config, connector_name or "gmail_imap")

    def connect(self):
        """Établit la connexion à Gmail."""
        try:
            super().connect()
        except ConnectionError as e:
            # Message plus spécifique pour les problèmes de connexion Gmail
            if "Authentication" in str(e):
                if self.imap_config.use_oauth:
                    raise ConnectionError(
                        "Failed to authenticate with Gmail IMAP using OAuth. "
                        "Make sure your OAuth credentials are correct and you have the appropriate scopes."
                    )
                else:
                    raise ConnectionError(
                        "Failed to authenticate with Gmail IMAP. Make sure you've enabled 'Less secure apps' "
                        "or created an App Password if you're using 2-factor authentication."
                    )
            raise

    def get_all_labels(self) -> List[str]:
        """
        Retourne la liste de tous les labels Gmail.

        Returns:
            Liste des labels Gmail
        """
        return self.list_mailboxes()

    @classmethod
    def create_with_oauth(
        cls,
        email: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        access_token: Optional[str] = None,
        token_file: Optional[str] = None,
        connector_name: Optional[str] = None,
    ):
        """
        Crée une instance de connecteur Gmail avec OAuth 2.0.

        Args:
            email: Adresse email Gmail
            client_id: ID client OAuth
            client_secret: Secret client OAuth
            refresh_token: Token de rafraîchissement
            access_token: Token d'accès (optionnel)
            token_file: Chemin vers un fichier pour stocker les tokens (optionnel)
            connector_name: Nom du connecteur (optionnel)

        Returns:
            Instance de GmailIMAPConnector configurée avec OAuth
        """
        from .oauth_utils import generate_gmail_oauth_config

        # Générer la configuration OAuth
        oauth_config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }

        if access_token:
            oauth_config["access_token"] = access_token

        # Configuration complète
        config = {"username": email, "use_oauth": True, "oauth": oauth_config}

        # Création de l'instance
        return cls(config, connector_name)
