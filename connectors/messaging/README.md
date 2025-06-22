# Connecteurs de Messagerie

Ce module contient des connecteurs pour interagir avec différents systèmes de messagerie électronique.

## Connecteurs disponibles

### 1. SMTP Connector
Le connecteur SMTP permet d'envoyer des emails avec pièces jointes.
- Authentification par mot de passe
- Authentification OAuth 2.0 (pour les services supportant XOAUTH2)
- Prise en charge des pièces jointes

### 2. Gmail Connector
Une implémentation spécifique du connecteur SMTP pour Gmail.
- Configuration pré-définie pour Gmail
- Support complet de l'authentification OAuth 2.0
- Méthode pratique `create_with_oauth` pour une configuration facile

### 3. IMAP Connector
Le connecteur IMAP permet de lire et gérer les emails dans une boîte de réception.
- Authentification par mot de passe
- Authentification OAuth 2.0 (pour les services compatibles)
- Fonctions pour lister, lire, marquer et supprimer des emails

### 4. Gmail IMAP Connector
Une implémentation spécifique du connecteur IMAP pour Gmail.
- Configuration pré-définie pour Gmail
- Support complet de l'authentification OAuth 2.0
- Méthode pratique `create_with_oauth` pour une configuration facile

## Exemple d'utilisation IMAP

```python
from connectors import create_connector

# Configuration pour un serveur IMAP quelconque
config = {
    "host": "imap.example.com",
    "port": 993,
    "username": "user@example.com",
    "password": "password",
    "use_ssl": True
}

# Créer une instance du connecteur
imap_connector = create_connector("imap", config)

# Se connecter au serveur
imap_connector.connect()

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
    
# Déconnexion à la fin
imap_connector.disconnect()
```

## Exemple d'utilisation Gmail

```python
from connectors import create_connector

# Configuration pour Gmail
config = {
    "username": "user@gmail.com",
    "password": "app_password"  # Mot de passe d'application si 2FA activé
}

# Créer une instance du connecteur (les paramètres host/port sont définis automatiquement)
gmail_connector = create_connector("gmail_imap", config)

# Se connecter à Gmail
gmail_connector.connect()

# Lister tous les labels Gmail
labels = gmail_connector.get_all_labels()
print(f"Labels disponibles: {labels}")

# Récupérer les emails non lus
messages = gmail_connector.receive_messages(
    mailbox="INBOX",
    limit=5,
    unread_only=True,
    newest_first=True
)

# Marquer des emails comme lus
if messages:
    email_ids = [msg['id'] for msg in messages]
    gmail_connector.mark_as_read(email_ids)
    
# Déconnexion
gmail_connector.disconnect()
```

## Authentification OAuth 2.0

Les connecteurs Gmail et IMAP supportent l'authentification OAuth 2.0, qui est plus sécurisée que l'authentification par mot de passe.

### Configuration OAuth pour Gmail
```python
# Configuration OAuth
oauth_config = {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "refresh_token": "your-refresh-token"
}

# Configuration du connecteur
config = {
    "username": "your-email@gmail.com",
    "use_oauth": True,
    "oauth": oauth_config
}

# Création du connecteur
gmail_connector = create_connector("gmail", config)
```

### Utilisation de la méthode `create_with_oauth`
```python
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
```

### Obtention des identifiants OAuth 2.0
1. Créez un projet sur [Google Cloud Console](https://console.cloud.google.com/)
2. Activez l'API Gmail pour votre projet
3. Créez des identifiants OAuth (ID client et secret client)
4. Utilisez ces identifiants pour obtenir un refresh token (voir script `example_oauth_gmail.py`)

Pour plus d'informations, consultez la [documentation officielle de Google](https://developers.google.com/identity/protocols/oauth2).

## Remarques

- Pour Gmail avec authentification par mot de passe, vous devrez créer un "mot de passe d'application" si vous utilisez l'authentification à deux facteurs (2FA). Voir https://support.google.com/accounts/answer/185833
- L'authentification OAuth 2.0 est recommandée pour les applications de production car elle est plus sécurisée.
- Le connecteur IMAP ne permet pas d'envoyer des emails. Pour cela, utilisez le connecteur SMTP.
