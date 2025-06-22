# python-connectors

Module "connectors" réutilisable dans des projets python pour centraliser l'accès à différents systèmes externes comme :

- Systèmes de fichiers (local, S3, Azure Blob, GCS…)
- Bases de données (PostgreSQL, MySQL, Oracle, etc.)
- NoSQL (MongoDB, Redis, etc.)
- Messageries (SMTP, IMAP, Slack, Teams…)
- APIs (REST, GraphQL…)
- Modèles IA (Hugging Face, OpenAI, etc.)


## 📁 Architecture du module connectors
```sh
project/
│
├── connectors/
│   ├── __init__.py
│   ├── base.py             # Base classes/interfaces
│   ├── registry.py      # Enregistrement dynamique des connecteurs
│   ├── db/
│   │   ├── postgres.py
│   │   ├── mysql.py
│   ├── data_lake/
│   │   ├── s3.py
│   │   └── azure_blob.py
│   ├── messaging/
│   │   ├── smtp.py
│   │   └── slack.py
│   ├── api/
│   │   ├── rest_api.py
│   │   ├── openai.py
│   ├── social_media/      # Nouveaux connecteurs réseaux sociaux
│   │   ├── __init__.py
│   │   ├── base_social.py  # Interface commune pour réseaux sociaux
│   │   ├── twitter.py
│   │   ├── facebook.py
│   │   ├── instagram.py
│   │   ├── linkedin.py
│   │   ├── youtube.py
│   │   └── tiktok.py
│   └── nosql/
│       ├── mongo.py
│       └── redis.py
└── tests/
    ├── test_postgres.py
    ├── test_s3.py
    ├── test_slack.py
    └── social_media/
        ├── test_twitter.py
        ├── test_facebook.py
        ├── test_instagram.py
        └── test_linkedin.py
```


## 🔧 Base Class pour tous les connecteurs (base.py)

```python
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        pass
```


## 🚀 Suggestions d'améliorations

### 1. Gestion des erreurs et retry

```python
class BaseConnector(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.retry_config = config.get('retry', {})

    @abstractmethod
    def connect(self):
        pass

    def connect_with_retry(self):
        # Logique de retry automatique
        pass
```

### 2. Configuration centralisée

```python
from pydantic import BaseModel

class ConnectorConfig(BaseModel):
    timeout: int = 30
    retry_attempts: int = 3
    pool_size: int = 10
```

### 3. Monitoring et métriques

```python
class BaseConnector(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.metrics = MetricsCollector()

    def execute_with_metrics(self, operation):
        # Mesure du temps d'exécution, erreurs, etc.
        pass
```

### 4. Context managers

```python
class BaseConnector(ABC):
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
```

### 5. Structure suggérée étendue

```
connectors/
├── __init__.py
├── base.py
├── registry.py
├── config/
│   ├── __init__.py
│   └── validator.py
├── exceptions/
│   ├── __init__.py
│   └── connector_exceptions.py
├── utils/
│   ├── __init__.py
│   ├── retry.py
│   └── metrics.py
└── [vos dossiers existants]
```


## 🚀 Installation

### Installation de base
```bash
pip install python-connectors
```

### Installation avec connecteurs spécifiques
```bash
# PostgreSQL
pip install python-connectors[postgresql]

# S3
pip install python-connectors[s3]

# Réseaux sociaux
pip install python-connectors[social]

# Tous les connecteurs
pip install python-connectors[all]

# Développement
pip install python-connectors[dev]
```

## 📖 Utilisation

### Exemple rapide avec PostgreSQL

```python
from connectors import create_connector

# Configuration
config = {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "password",
    "timeout": 30,
    "retry": {
        "max_attempts": 3,
        "backoff_factor": 2.0
    }
}

# Création du connecteur
postgres = create_connector("postgresql", config, "my_postgres")

# Utilisation avec context manager
with postgres.connection():
    # Créer une table
    postgres.create_table("users", {
        "id": "SERIAL PRIMARY KEY",
        "name": "VARCHAR(100)",
        "email": "VARCHAR(100) UNIQUE"
    })
    
    # Insérer des données
    postgres.insert_data("users", {
        "name": "John Doe",
        "email": "john@example.com"
    })
    
    # Requête des données
    users = postgres.fetch_all("SELECT * FROM users")
    print(f"Users: {users}")

# Afficher les métriques
metrics = postgres.get_metrics_summary()
print(f"Metrics: {metrics}")
```

### Exemple avec S3

```python
from connectors import create_connector

# Configuration S3
config = {
    "access_key_id": "your_access_key",
    "secret_access_key": "your_secret_key",
    "bucket_name": "your-bucket",
    "region": "us-east-1"
}

# Création du connecteur
s3 = create_connector("s3", config, "my_s3")

# Utilisation
with s3.connection():
    # Upload d'un fichier
    s3.upload_file("local_file.txt", "remote_file.txt")
    
    # Lister les fichiers
    files = s3.list_files(prefix="documents/")
    print(f"Files: {len(files)}")
    
    # Créer une URL pré-signée
    url = s3.create_presigned_url("remote_file.txt", expiration=3600)
    print(f"URL: {url}")
```

### Exemple avec Twitter

```python
from connectors import create_connector

# Configuration Twitter
config = {
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "access_token": "your_access_token",
    "access_token_secret": "your_access_token_secret"
}

# Création du connecteur
twitter = create_connector("twitter", config, "my_twitter")

# Utilisation
with twitter.connection():
    # Publier un tweet
    tweet = twitter.post_message("Hello from Python!")
    print(f"Tweet publié: {tweet['id']}")
    
    # Récupérer le fil d'actualité
    feed = twitter.get_feed(limit=10)
    print(f"Derniers tweets: {len(feed)}")
    
    # Obtenir les informations du profil
    profile = twitter.get_profile_info()
    print(f"Profil: @{profile['username']} ({profile['followers_count']} abonnés)")
```

### Exemple avec LinkedIn

```python
from connectors import create_connector

# Configuration LinkedIn
config = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "access_token": "your_access_token"
}

# Création du connecteur
linkedin = create_connector("linkedin", config, "my_linkedin")

# Utilisation
with linkedin.connection():
    # Publier un post
    post = linkedin.post_message(
        "Excited to share our new Python connectors module!",
        media=["image.jpg"]
    )
    print(f"Post LinkedIn publié: {post['id']}")
    
    # Récupérer les connexions
    connections = linkedin.get_connections(limit=50)
    print(f"Connexions: {len(connections)}")
```

### Gestion des erreurs et retry

```python
from connectors import create_connector
from connectors.exceptions import ConnectionError, RetryExhaustedError

try:
    with postgres.connection():
        result = postgres.fetch_all("SELECT * FROM users")
except ConnectionError as e:
    print(f"Connection failed: {e}")
except RetryExhaustedError as e:
    print(f"All retry attempts failed: {e}")
```

### Utilisation du registre

```python
from connectors import list_available_connectors, get_connector

# Lister les connecteurs disponibles
connectors = list_available_connectors()
print(f"Available: {connectors}")

# Récupérer une instance existante
postgres = get_connector("my_postgres")
```

## 🧪 Tests

```bash
# Installation des dépendances de développement
pip install -r requirements-dev.txt

# Lancer les tests
pytest

# Avec couverture
pytest --cov=connectors --cov-report=html
```

## 📊 Métriques

Le module collecte automatiquement des métriques sur les opérations :

- Nombre d'opérations réussies/échouées
- Temps de réponse moyen
- Nombre de connexions
- Taux de succès

```python
# Récupérer les métriques
metrics = connector.get_metrics_summary()
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Average duration: {metrics['average_duration']:.3f}s")
```

## 🔧 Développement

### Ajouter un nouveau connecteur

1. Créer une classe héritant de `BaseConnector` ou d'une classe spécialisée
2. Implémenter les méthodes abstraites
3. Enregistrer le connecteur avec `@register_connector`

```python
from connectors import BaseConnector, register_connector

@register_connector("mon_connecteur")
class MonConnecteur(BaseConnector):
    def connect(self):
        # Logique de connexion
        pass
    
    def disconnect(self):
        # Logique de déconnexion
        pass
    
    def test_connection(self) -> bool:
        # Test de connexion
        return True
```

## 📦 Connecteurs disponibles

### Bases de données
- ✅ **PostgreSQL** - Base de données relationnelle
- 🚧 **MySQL** - Base de données relationnelle (à venir)
- 🚧 **Oracle** - Base de données enterprise (à venir)
- 🚧 **SQL Server** - Base de données Microsoft (à venir)

### NoSQL
- 🚧 **MongoDB** - Base de données NoSQL (à venir)
- 🚧 **Redis** - Cache/base de données en mémoire (à venir)
- 🚧 **Cassandra** - Base de données distribuée (à venir)

### Stockage cloud
- ✅ **Amazon S3** - Stockage cloud AWS
- 🚧 **Azure Blob Storage** - Stockage cloud Microsoft (à venir)
- 🚧 **Google Cloud Storage** - Stockage cloud Google (à venir)

### Messagerie
- 🚧 **SMTP** - Envoi d'emails (à venir)
- 🚧 **Slack** - Messagerie d'équipe (à venir)
- 🚧 **Microsoft Teams** - Collaboration Microsoft (à venir)

### APIs et IA
- 🚧 **OpenAI** - API d'intelligence artificielle (à venir)
- 🚧 **REST API** - Client REST générique (à venir)
- 🚧 **GraphQL** - Client GraphQL (à venir)

### Réseaux sociaux
- 🚧 **Twitter/X** - Publication et récupération de tweets (à venir)
- 🚧 **Facebook** - Gestion des pages et posts Facebook (à venir)
- 🚧 **Instagram** - Publication de photos et stories (à venir)
- 🚧 **LinkedIn** - Publication professionnelle et networking (à venir)
- 🚧 **YouTube** - Gestion de vidéos et playlists (à venir)
- 🚧 **TikTok** - Publication de vidéos courtes (à venir)

## 📄 Licence

## 🧪 Tests et validation

### Exécuter les tests d'intégration
```bash
# Tests complets
python scripts/test_integration.py

# Tests spécifiques aux réseaux sociaux
python -m pytest tests/social_media/ -v

# Tests avec couverture
python -m pytest tests/ --cov=connectors --cov-report=html
```

### Validation des connecteurs
```bash
# Validation des connecteurs disponibles
python scripts/example_social_media.py

# Test de configuration
python scripts/example_config.py
```

## 📚 Documentation

- 📖 [Guide des connecteurs de bases de données](docs/database_guide.md)
- 🌐 [Guide des connecteurs de réseaux sociaux](docs/social_media_guide.md)
- ☁️ [Guide des connecteurs cloud](docs/cloud_guide.md)
- 🔧 [Guide de configuration avancée](docs/advanced_config.md)

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez le [guide de contribution](CONTRIBUTING.md) pour plus d'informations.

## 📄 Licence

MIT License - voir le fichier [LICENSE](LICENSE) pour plus de détails.