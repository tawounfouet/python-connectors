# Guide des Connecteurs de Messagerie

Ce guide détaille l'utilisation des connecteurs pour les systèmes de messagerie électronique.

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Types de connecteurs](#types-de-connecteurs)
3. [Configuration](#configuration)
4. [Envoi d'emails avec SMTP](#envoi-demails-avec-smtp)
5. [Lecture d'emails avec IMAP](#lecture-demails-avec-imap)
6. [Utilisation spécifique à Gmail](#utilisation-spécifique-à-gmail)
7. [Authentification OAuth 2.0](#authentification-oauth-20)
8. [Bonnes pratiques](#bonnes-pratiques)
9. [Gestion des erreurs](#gestion-des-erreurs)

## 🌟 Vue d'ensemble

Les connecteurs de messagerie permettent d'interagir avec différents services de messagerie électronique (SMTP, IMAP) à travers une interface unifiée. Cette bibliothèque prend en charge :

- L'envoi d'emails avec pièces jointes via SMTP
- La lecture et la gestion d'emails via IMAP
- Des connecteurs spécifiques pour Gmail
- L'authentification par mot de passe et par OAuth 2.0

## 🔌 Types de connecteurs

### SMTP Connector
- Envoi d'emails avec pièces jointes
- Authentification par mot de passe
- Authentification OAuth 2.0 (pour les services supportant XOAUTH2)

### Gmail Connector
- Implémentation spécifique du connecteur SMTP pour Gmail
- Configuration pré-définie pour Gmail
- Support complet de l'authentification OAuth 2.0
- Méthode pratique `create_with_oauth`

### IMAP Connector
- Lecture et gestion d'emails dans une boîte de réception
- Authentification par mot de passe
- Authentification OAuth 2.0 (pour les services compatibles)
- Fonctions pour lister, lire, marquer et supprimer des emails

### Gmail IMAP Connector
- Implémentation spécifique du connecteur IMAP pour Gmail
- Configuration pré-définie pour Gmail
- Support complet de l'authentification OAuth 2.0
- Méthode pratique `create_with_oauth`

## ⚙️ Configuration

### Variables d'environnement

```bash
# Configuration SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=True

# Configuration IMAP
IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_USERNAME=your-email@example.com
IMAP_PASSWORD=your-password

# Configuration Gmail
GMAIL_USERNAME=your-email@gmail.com
GMAIL_PASSWORD=your-app-password  # Mot de passe d'application si 2FA activé

# Configuration OAuth 2.0 pour Gmail
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Configuration par code

```python
# Configuration SMTP standard
smtp_config = {
    "host": "smtp.example.com",
    "port": 587,
    "username": "your-email@example.com",
    "password": "your-password",
    "use_tls": True,
    "timeout": 30
}

# Configuration IMAP standard
imap_config = {
    "host": "imap.example.com",
    "port": 993,
    "username": "your-email@example.com",
    "password": "your-password",
    "use_ssl": True
}

# Configuration Gmail simplifiée
gmail_config = {
    "username": "your-email@gmail.com",
    "password": "your-app-password"  # Mot de passe d'application si 2FA activé
}

# Configuration OAuth pour Gmail
oauth_config = {
    "username": "your-email@gmail.com",
    "use_oauth": True,
    "oauth": {
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "refresh_token": "your-refresh-token"
    }
}
```

## 📧 Envoi d'emails avec SMTP

### Exemple simple

```python
from connectors import create_connector

# Configuration
config = {
    "host": "smtp.example.com",
    "port": 587,
    "username": "your-email@example.com",
    "password": "your-password",
    "use_tls": True
}

# Création du connecteur
smtp_connector = create_connector("smtp", config)

# Connexion
smtp_connector.connect()

# Envoi d'un email simple
smtp_connector.send_email(
    subject="Test email",
    recipients=["recipient@example.com"],
    body="This is a test email sent from Python.",
    html_body="<h1>Test Email</h1><p>This is a <b>test</b> email sent from Python.</p>"
)

# Déconnexion
smtp_connector.disconnect()
```

### Email avec pièces jointes

```python
from connectors import create_connector

# Création du connecteur
smtp_connector = create_connector("smtp", config)

# Envoi avec pièce jointe
with smtp_connector.connection():
    smtp_connector.send_email(
        subject="Email with attachments",
        recipients=["recipient@example.com"],
        body="Please find attached the requested documents.",
        attachments=[
            "/path/to/document.pdf",
            "/path/to/image.jpg"
        ]
    )
```

## 📬 Lecture d'emails avec IMAP

### Lister et lire les emails

```python
from connectors import create_connector

# Configuration
config = {
    "host": "imap.example.com",
    "port": 993,
    "username": "user@example.com",
    "password": "password",
    "use_ssl": True
}

# Créer une instance du connecteur
imap_connector = create_connector("imap", config)

# Se connecter et utiliser le contexte manager
with imap_connector.connection():
    # Lister les boîtes disponibles
    mailboxes = imap_connector.list_mailboxes()
    print(f"Boîtes disponibles: {mailboxes}")

    # Sélectionner une boîte et récupérer le nombre de messages
    num_messages = imap_connector.select_mailbox("INBOX")
    print(f"Nombre de messages: {num_messages}")

    # Récupérer les 10 derniers emails
    messages = imap_connector.receive_messages(
        limit=10,
        unread_only=False,
        newest_first=True
    )

    # Traiter les messages
    for msg in messages:
        print(f"ID: {msg['id']}")
        print(f"Sujet: {msg['subject']}")
        print(f"De: {msg['from']}")
        print(f"Date: {msg['date']}")
        print(f"Corps: {msg['body'][:100]}...")
```

### Recherche avancée d'emails

```python
# Recherche avec des critères spécifiques
messages = imap_connector.search_messages(
    criteria=[
        "FROM", "important@example.com",
        "SUBJECT", "Urgent",
        "SINCE", "01-Jan-2023"
    ],
    limit=5
)

# Télécharger les pièces jointes d'un message
msg = messages[0]
if msg["has_attachments"]:
    attachments = imap_connector.get_attachments(msg["id"])
    for att in attachments:
        print(f"Nom: {att['filename']}")
        # Sauvegarder la pièce jointe
        with open(f"downloads/{att['filename']}", "wb") as f:
            f.write(att["data"])
```

### Gestion des emails

```python
# Marquer des emails comme lus
imap_connector.mark_as_read(["123", "124", "125"])

# Déplacer des emails vers un autre dossier
imap_connector.move_messages(["123", "124"], "Archives")

# Supprimer des emails
imap_connector.delete_messages(["125", "126"])
```

## 📱 Utilisation spécifique à Gmail

### Connecteur Gmail SMTP

```python
from connectors import create_connector

# Configuration minimale pour Gmail
config = {
    "username": "your-email@gmail.com",
    "password": "your-app-password"  # Mot de passe d'application si 2FA activé
}

# Le host et port sont préconfigurés pour Gmail
gmail_connector = create_connector("gmail", config)

with gmail_connector.connection():
    gmail_connector.send_email(
        subject="Email depuis Gmail",
        recipients=["recipient@example.com"],
        body="Email envoyé via le connecteur Gmail spécifique."
    )
```

### Connecteur Gmail IMAP

```python
from connectors import create_connector

# Configuration pour Gmail IMAP
config = {
    "username": "your-email@gmail.com",
    "password": "your-app-password"
}

# Créer une instance du connecteur Gmail IMAP
gmail_imap = create_connector("gmail_imap", config)

with gmail_imap.connection():
    # Lister tous les labels Gmail (spécifique à Gmail)
    labels = gmail_imap.get_all_labels()
    print(f"Labels disponibles: {labels}")

    # Récupérer les emails d'un label spécifique
    messages = gmail_imap.receive_messages(
        mailbox="[Gmail]/Starred",  # Label Gmail
        limit=5
    )
    
    # Rechercher des emails avec la syntaxe Gmail
    important_msgs = gmail_imap.search_messages(
        criteria=["X-GM-RAW", "is:important has:attachment"],
        limit=3
    )
```

## 🔐 Authentification OAuth 2.0

OAuth 2.0 est une méthode d'authentification plus sécurisée qui ne nécessite pas de stocker le mot de passe.

### Préparation des identifiants OAuth

Avant d'utiliser OAuth 2.0 avec Gmail:

1. Créez un projet sur [Google Cloud Console](https://console.cloud.google.com/)
2. Activez l'API Gmail pour votre projet
3. Créez des identifiants OAuth (ID client et secret client)
4. Utilisez ces identifiants pour obtenir un refresh token

### Utilisation d'OAuth avec les connecteurs

```python
# Configuration OAuth pour SMTP
oauth_config = {
    "username": "your-email@gmail.com",
    "use_oauth": True,
    "oauth": {
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "refresh_token": "your-refresh-token"
    }
}

# Création du connecteur avec OAuth
smtp_connector = create_connector("smtp", oauth_config)
```

### Utilisation des méthodes create_with_oauth

```python
from connectors.messaging.smtp import GmailConnector
from connectors.messaging.imap import GmailIMAPConnector

# Pour Gmail SMTP
gmail_smtp = GmailConnector.create_with_oauth(
    email="your-email@gmail.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    refresh_token="your-refresh-token"
)

# Pour Gmail IMAP
gmail_imap = GmailIMAPConnector.create_with_oauth(
    email="your-email@gmail.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    refresh_token="your-refresh-token"
)

# Utilisation comme les autres connecteurs
with gmail_smtp.connection():
    gmail_smtp.send_email(
        subject="Test OAuth",
        recipients=["recipient@example.com"],
        body="Email envoyé avec OAuth 2.0"
    )
```

### Obtention d'un refresh token

Un exemple complet est disponible dans `scripts/example_oauth_gmail.py`. Voici un extrait:

```python
from connectors.messaging.oauth_utils import OAuth2Manager

# Initialiser le gestionnaire OAuth
oauth_manager = OAuth2Manager(
    client_id="your-client-id",
    client_secret="your-client-secret",
    scopes=["https://mail.google.com/"]
)

# Générer l'URL d'autorisation
auth_url = oauth_manager.generate_oauth_url()
print(f"Visitez cette URL et autorisez l'application: {auth_url}")

# Après autorisation, récupérer le code d'autorisation de l'URL de redirection
auth_code = input("Entrez le code d'autorisation: ")

# Échanger le code contre des tokens
tokens = oauth_manager.exchange_code_for_tokens(auth_code)
print(f"Refresh token: {tokens['refresh_token']}")
print(f"Access token: {tokens['access_token']}")
```

## 💡 Bonnes pratiques

1. **Utilisation du contexte manager**: Préférez l'utilisation du contexte manager (`with connector.connection():`) pour garantir la déconnexion propre:
   ```python
   with smtp_connector.connection():
       smtp_connector.send_email(...)
   ```

2. **Authentification OAuth 2.0**: Pour les applications de production, préférez l'authentification OAuth 2.0 qui est plus sécurisée qu'un mot de passe.

3. **Gestion des pièces jointes volumineuses**: Pour les pièces jointes volumineuses, utilisez un traitement en streaming ou limitez leur taille:
   ```python
   # Vérifier la taille des pièces jointes avant envoi
   import os
   if os.path.getsize(attachment_path) > 10 * 1024 * 1024:  # 10 MB
       print("Pièce jointe trop volumineuse, utiliser une solution alternative")
   ```

4. **Recherche optimisée**: Pour les boîtes email avec beaucoup de messages, utilisez des critères de recherche précis:
   ```python
   # Plus efficace que de récupérer tous les emails
   recent_important = imap_connector.search_messages([
       "SINCE", "01-Jan-2023",
       "FROM", "important@example.com"
   ])
   ```

5. **Gestion des timeouts**: Définissez des timeouts adaptés pour éviter les blocages:
   ```python
   config["timeout"] = 60  # timeout en secondes
   ```

## ⚠️ Gestion des erreurs

```python
from connectors.exceptions import (
    ConnectionError, AuthenticationError,
    ConfigurationError, MessageError
)

try:
    smtp_connector.connect()
    smtp_connector.send_email(...)
except ConnectionError as e:
    print(f"Erreur de connexion: {e}")
except AuthenticationError as e:
    print(f"Erreur d'authentification: {e}")
except ConfigurationError as e:
    print(f"Erreur de configuration: {e}")
except MessageError as e:
    print(f"Erreur lors de l'envoi du message: {e}")
except Exception as e:
    print(f"Erreur inattendue: {e}")
finally:
    if smtp_connector.is_connected():
        smtp_connector.disconnect()
```

### Erreurs courantes et solutions:

| Erreur | Cause probable | Solution |
|--------|----------------|----------|
| `ConnectionError` | Serveur inaccessible ou problème réseau | Vérifier les paramètres host/port et la connexion réseau |
| `SMTPAuthenticationError` | Identifiants invalides | Vérifier le nom d'utilisateur et le mot de passe |
| `ConfigurationError` | Configuration incomplète ou invalide | Vérifier tous les paramètres requis |
| `MessageError` | Problème avec le contenu du message | Vérifier les adresses des destinataires et le format du message |
| `SSLError` | Problème de certificat SSL | Vérifier les paramètres SSL/TLS ou utiliser `verify_ssl=False` (non recommandé en production) |
