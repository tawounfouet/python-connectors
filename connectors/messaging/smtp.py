"""
Connecteur SMTP pour l'envoi d'emails.

Ce module fournit un connecteur pour interagir avec les serveurs SMTP,
permettant l'envoi d'emails avec ou sans pièces jointes.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formataddr, formatdate
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

try:
    from connectors.base import MessagingConnector
    from connectors.registry import register_connector
    from connectors.exceptions import ConnectionError, ConfigurationError, AuthenticationError
    from connectors.config import SMTPConfig
    from connectors.config.validator import OAuthConfig
except ImportError:
    # Import relatif si l'import absolu échoue
    from ..base import MessagingConnector
    from ..registry import register_connector
    from ..exceptions import ConnectionError, ConfigurationError, AuthenticationError
    from ..config import SMTPConfig
    from ..config.validator import OAuthConfig

logger = logging.getLogger(__name__)


@register_connector("smtp")
class SMTPConnector(MessagingConnector):
    """Connecteur pour serveur SMTP."""

    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        super().__init__(config, connector_name)

        # Validation de la configuration
        try:
            self.smtp_config = SMTPConfig(**config)
        except Exception as e:
            raise ConfigurationError(f"Invalid SMTP configuration: {e}")

        self.smtp_client = None

    def connect(self):
        """Établit la connexion au serveur SMTP."""
        try:
            if self.smtp_config.use_ssl:
                self.smtp_client = smtplib.SMTP_SSL(
                    host=self.smtp_config.host,
                    port=self.smtp_config.port,
                    timeout=self.smtp_config.timeout,
                )
            else:
                self.smtp_client = smtplib.SMTP(
                    host=self.smtp_config.host,
                    port=self.smtp_config.port,
                    timeout=self.smtp_config.timeout,
                )

                # Si TLS est activé, démarrer TLS
                if self.smtp_config.use_tls:
                    self.smtp_client.starttls()

            # Authentification
            if self.smtp_config.use_oauth and self.smtp_config.oauth:
                # Utiliser OAuth 2.0
                self._oauth_login()
            elif self.smtp_config.username and self.smtp_config.password:
                # Authentification classique avec identifiant/mot de passe
                self.smtp_client.login(self.smtp_config.username, self.smtp_config.password)
            # Si pas d'authentification, on essaie de continuer sans login

            self.logger.info(
                f"Connected to SMTP server: {self.smtp_config.host}:{self.smtp_config.port}"
            )
            self._connected = True

        except Exception as e:
            self.logger.error(f"Failed to connect to SMTP server: {e}")
            raise ConnectionError(f"Failed to connect to SMTP server: {e}")

    def _oauth_login(self):
        """Authentification par OAuth 2.0."""
        if not self.smtp_config.oauth:
            raise ConfigurationError("OAuth configuration is missing")

        try:
            from .oauth_utils import OAuth2Manager

            # Créer le gestionnaire OAuth
            oauth_manager = OAuth2Manager(
                client_id=self.smtp_config.oauth.client_id,
                client_secret=self.smtp_config.oauth.client_secret,
                refresh_token=self.smtp_config.oauth.refresh_token,
                access_token=self.smtp_config.oauth.access_token,
            )

            # Le mécanisme d'authentification dépend du serveur
            if "gmail" in self.smtp_config.host:
                # Pour Gmail, on utilise XOAUTH2
                auth_string = oauth_manager.get_auth_string(self.smtp_config.username)

                # Authentification SMTP avec XOAUTH2
                self.smtp_client.ehlo()
                self.smtp_client.docmd("AUTH", f"XOAUTH2 {auth_string}")
                self.logger.info("Authenticated with Gmail SMTP using OAuth 2.0")
            else:
                # Pour d'autres serveurs, adapter selon le besoin
                self.logger.warning(
                    "OAuth authentication for this SMTP server is not specifically implemented"
                )
                auth_string = oauth_manager.get_auth_string(self.smtp_config.username)
                self.smtp_client.ehlo()
                self.smtp_client.docmd("AUTH", f"XOAUTH2 {auth_string}")

        except ImportError:
            raise ConfigurationError("OAuth module not available. Install oauth2client package.")
        except Exception as e:
            self.logger.error(f"OAuth authentication failed: {e}")
            raise AuthenticationError(f"SMTP OAuth authentication failed: {e}")

    def disconnect(self):
        """Ferme la connexion au serveur SMTP."""
        if self.smtp_client:
            try:
                self.smtp_client.quit()
                self.logger.debug("Disconnected from SMTP server")
            except Exception as e:
                self.logger.warning(f"Error while disconnecting from SMTP server: {e}")
            finally:
                self.smtp_client = None
                self._connected = False

    def test_connection(self) -> bool:
        """Teste la connexion au serveur SMTP."""
        if not self._connected:
            try:
                self.connect()
                self.disconnect()
                return True
            except Exception as e:
                self.logger.error(f"SMTP connection test failed: {e}")
                return False
        return True

    def send_message(self, message: str, recipient: str, **kwargs):
        """
        Envoie un email via SMTP.

        Args:
            message: Corps de l'email
            recipient: Adresse email du destinataire
            **kwargs: Options additionnelles :
                - subject: Sujet de l'email
                - from_name: Nom de l'expéditeur
                - html: Si True, le message est envoyé au format HTML
                - cc: Liste des destinataires en copie
                - bcc: Liste des destinataires en copie cachée
                - attachments: Liste des chemins vers les pièces jointes

        Returns:
            Dict contenant le statut de l'envoi et les détails
        """
        if not self._connected:
            raise ConnectionError("Not connected to SMTP server")

        def _send_email():
            # Configuration des options
            subject = kwargs.get("subject", "No Subject")
            from_name = kwargs.get("from_name", "")
            html = kwargs.get("html", False)
            cc = kwargs.get("cc", [])
            bcc = kwargs.get("bcc", [])
            attachments = kwargs.get("attachments", [])

            # Création du message
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = formataddr((from_name, self.smtp_config.username))
            msg["To"] = recipient
            msg["Date"] = formatdate(localtime=True)

            if cc:
                msg["Cc"] = ", ".join(cc) if isinstance(cc, list) else cc

            # Ajout du corps du message
            if html:
                msg.attach(MIMEText(message, "html"))
            else:
                msg.attach(MIMEText(message, "plain"))

            # Ajout des pièces jointes
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)

            # Liste complète des destinataires pour l'envoi
            recipients = [recipient]
            if cc:
                if isinstance(cc, list):
                    recipients.extend(cc)
                else:
                    recipients.append(cc)
            if bcc:
                if isinstance(bcc, list):
                    recipients.extend(bcc)
                else:
                    recipients.append(bcc)

            # Envoi du message
            self.smtp_client.sendmail(
                from_addr=self.smtp_config.username, to_addrs=recipients, msg=msg.as_string()
            )

            return {
                "status": "sent",
                "to": recipient,
                "cc": cc,
                "bcc": bcc,
                "subject": subject,
                "has_attachments": len(attachments) > 0,
                "attachment_count": len(attachments),
            }

        return self.execute_with_metrics("send_email", _send_email)

    def _add_attachment(self, msg: MIMEMultipart, attachment: str) -> None:
        """
        Ajoute une pièce jointe au message.

        Args:
            msg: Message MIMEMultipart
            attachment: Chemin vers le fichier à attacher
        """
        try:
            path = Path(attachment)
            if not path.exists():
                self.logger.warning(f"Attachment not found: {attachment}")
                return

            filename = path.name

            with open(path, "rb") as file:
                part = MIMEApplication(file.read(), Name=filename)

            # Ajout des headers
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)

        except Exception as e:
            self.logger.error(f"Failed to add attachment {attachment}: {e}")

    def receive_messages(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Méthode pour recevoir des messages.
        Non implémentée pour SMTP (utiliser un connecteur IMAP pour cela).

        Raises:
            NotImplementedError: Cette fonction n'est pas disponible pour SMTP
        """
        raise NotImplementedError(
            "SMTP connector does not support receiving messages. Use IMAP instead."
        )


@register_connector("gmail")
class GmailConnector(SMTPConnector):
    """Connecteur SMTP spécifique pour Gmail."""

    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        # Préparation de la configuration spécifique à Gmail
        gmail_config = config.copy()
        gmail_config.update(
            {"host": "smtp.gmail.com", "port": 587, "use_tls": True, "use_ssl": False}
        )

        # Si OAuth est activé, on s'assure que la configuration est présente
        if config.get("use_oauth", False):
            if not config.get("oauth"):
                raise ConfigurationError("OAuth is enabled but OAuth configuration is missing")

            # Pour Gmail, le scope minimal est 'https://mail.google.com/'
            scopes = config.get("oauth_scopes", ["https://mail.google.com/"])
            self.logger.info(f"OAuth configuration detected for Gmail with scopes: {scopes}")

        super().__init__(gmail_config, connector_name or "gmail")

    def connect(self):
        """Établit la connexion à Gmail."""
        try:
            super().connect()
        except ConnectionError as e:
            # Message plus spécifique pour les problèmes de connexion Gmail
            if "Authentication" in str(e):
                if self.smtp_config.use_oauth:
                    raise ConnectionError(
                        "Failed to authenticate with Gmail SMTP using OAuth. "
                        "Make sure your OAuth credentials are correct and you have the appropriate scopes."
                    )
                else:
                    raise ConnectionError(
                        "Failed to authenticate with Gmail SMTP. Make sure you've enabled 'Less secure apps' "
                        "or created an App Password if you're using 2-factor authentication."
                    )
            raise

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
            Instance de GmailConnector configurée avec OAuth
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
