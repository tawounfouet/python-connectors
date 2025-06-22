# Guide des Connecteurs de Réseaux Sociaux

Ce guide détaille l'utilisation des connecteurs pour les principales plateformes de réseaux sociaux.

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Configuration](#configuration)
3. [Utilisation par plateforme](#utilisation-par-plateforme)
4. [Bonnes pratiques](#bonnes-pratiques)
5. [Gestion des erreurs](#gestion-des-erreurs)
6. [Limites et restrictions](#limites-et-restrictions)

## 🌟 Vue d'ensemble

Les connecteurs de réseaux sociaux permettent d'interagir avec les APIs des principales plateformes sociales de manière unifiée. Chaque connecteur implémente l'interface `SocialMediaConnector` avec les méthodes communes :

- `authenticate()` - Authentification
- `post_message()` - Publication de contenu
- `get_feed()` - Récupération du flux
- `get_profile_info()` - Informations du profil
- `delete_post()` - Suppression de contenu

## ⚙️ Configuration

### Variables d'environnement

```bash
# Twitter
export TWITTER_BEARER_TOKEN="your_bearer_token"
export TWITTER_API_KEY="your_api_key"
export TWITTER_API_SECRET="your_api_secret"
export TWITTER_ACCESS_TOKEN="your_access_token"
export TWITTER_ACCESS_TOKEN_SECRET="your_access_token_secret"

# LinkedIn
export LINKEDIN_ACCESS_TOKEN="your_access_token"
export LINKEDIN_CLIENT_ID="your_client_id"
export LINKEDIN_CLIENT_SECRET="your_client_secret"

# Facebook
export FACEBOOK_ACCESS_TOKEN="your_access_token"
export FACEBOOK_PAGE_ID="your_page_id"

# Instagram
export INSTAGRAM_ACCESS_TOKEN="your_access_token"
export INSTAGRAM_USER_ID="your_user_id"

# YouTube
export YOUTUBE_API_KEY="your_api_key"
export YOUTUBE_ACCESS_TOKEN="your_access_token"

# TikTok
export TIKTOK_ACCESS_TOKEN="your_access_token"
export TIKTOK_CLIENT_KEY="your_client_key"

# GitHub
export GITHUB_ACCESS_TOKEN="your_personal_access_token"
```

### Configuration par code

```python
from connectors import create_connector
from connectors.config import TwitterConfig, LinkedInConfig

# Configuration Twitter
twitter_config = TwitterConfig(
    bearer_token="your_bearer_token",
    api_key="your_api_key",
    api_secret="your_api_secret",
    timeout=30,
    retry_attempts=3
)

# Configuration LinkedIn
linkedin_config = LinkedInConfig(
    access_token="your_access_token",
    client_id="your_client_id",
    default_visibility="PUBLIC"
)

# Configuration GitHub
github_config = {
    'access_token': 'your_personal_access_token',
    'default_owner': 'your_username',
    'default_repo': 'your_repository'
}

# Configuration avec classe (recommandée)
from connectors.config.social_media import GitHubConfig

github_config = GitHubConfig(
    access_token="your_personal_access_token",
    default_owner="your_username",
    default_repo="your_repository"
)
```

## 🔗 Utilisation par plateforme

### Twitter

```python
from connectors import create_connector

# Configuration
config = {
    'bearer_token': 'your_bearer_token',
    'api_key': 'your_api_key',
    'api_secret': 'your_api_secret'
}

# Création et utilisation
twitter = create_connector("twitter", config)

with twitter.connection():
    # Publication d'un tweet
    tweet = twitter.post_message("Hello from Python! #automation")
    print(f"Tweet publié: {tweet['url']}")
    
    # Récupération du flux
    feed = twitter.get_feed(limit=10)
    for post in feed:
        print(f"- {post['text'][:50]}...")
    
    # Informations du profil
    profile = twitter.get_profile_info()
    print(f"Profil: @{profile['username']} ({profile['followers_count']} abonnés)")
```

### LinkedIn

```python
from connectors import create_connector

config = {
    'access_token': 'your_access_token',
    'client_id': 'your_client_id'
}

linkedin = create_connector("linkedin", config)

with linkedin.connection():
    # Publication d'un post
    post = linkedin.post_message(
        "Excited to share our new automation tool!",
        options={'visibility': 'PUBLIC'}
    )
    
    # Récupération des connexions
    connections = linkedin.get_connections(limit=50)
    print(f"Vous avez {len(connections)} connexions")
```

### Facebook

```python
from connectors import create_connector

config = {
    'access_token': 'your_access_token',
    'page_id': 'your_page_id'  # Optionnel pour les pages
}

facebook = create_connector("facebook", config)

with facebook.connection():
    # Publication d'un post
    post = facebook.post_message("Hello from our automation system!")
    
    # Récupération du flux
    feed = facebook.get_feed(limit=5)
    for post in feed:
        print(f"Post: {post['text']}")
```

### Instagram

```python
from connectors import create_connector

config = {
    'access_token': 'your_access_token',
    'user_id': 'your_user_id'
}

instagram = create_connector("instagram", config)

with instagram.connection():
    # Récupération du contenu
    media = instagram.get_feed(limit=10)
    for item in media:
        print(f"Post: {item['media_type']} - {item['text']}")
    
    # Informations du profil
    profile = instagram.get_profile_info()
    print(f"Instagram: @{profile['username']} ({profile['media_count']} posts)")
```

### YouTube

```python
from connectors import create_connector

config = {
    'api_key': 'your_api_key',
    'access_token': 'your_access_token'  # Pour les opérations d'écriture
}

youtube = create_connector("youtube", config)

with youtube.connection():
    # Récupération des vidéos de la chaîne
    videos = youtube.get_feed(limit=10)
    for video in videos:
        print(f"Vidéo: {video['title']} - {video['url']}")
    
    # Informations de la chaîne
    channel = youtube.get_profile_info()
    print(f"Chaîne: {channel['title']} ({channel['subscriber_count']} abonnés)")
    
    # Récupération des playlists
    playlists = youtube.get_playlists(limit=5)
    for playlist in playlists:
        print(f"Playlist: {playlist['title']}")
```

### TikTok

```python
from connectors import create_connector

config = {
    'access_token': 'your_access_token',
    'client_key': 'your_client_key'
}

tiktok = create_connector("tiktok", config)

with tiktok.connection():
    # Récupération des vidéos
    videos = tiktok.get_feed(limit=10)
    for video in videos:
        print(f"Vidéo: {video['title']} - {video['view_count']} vues")
    
    # Informations du profil
    profile = tiktok.get_profile_info()
    print(f"TikTok: @{profile['username']} ({profile['follower_count']} abonnés)")
    
    # Analytics d'une vidéo
    analytics = tiktok.get_video_analytics("video_id")
    print(f"Analytics: {analytics['view_count']} vues, {analytics['like_count']} likes")
```

### GitHub

```python
from connectors import create_connector

# Configuration
config = {
    'access_token': 'your_personal_access_token',  # Token d'accès GitHub
    'default_owner': 'your_username',              # Optionnel: propriétaire par défaut
    'default_repo': 'your_repository'              # Optionnel: dépôt par défaut
}

# Création du connecteur
github = create_connector("github", config)

with github.connection():
    # Création d'une issue
    issue = github.post_message(
        "Bug dans la fonction d'authentification",
        options={
            'owner': 'username',            # Remplace default_owner si spécifié
            'repo': 'repository',           # Remplace default_repo si spécifié
            'title': "Bug d'authentification", 
            'labels': ['bug', 'priority']   # Optionnel
        }
    )
    print(f"Issue créée: {issue['url']}")
    
    # Commentaire sur une issue existante
    comment = github.post_message(
        "J'ai trouvé la solution au problème!",
        options={
            'issue_number': 42              # Numéro de l'issue à commenter
        }
    )
    
    # Récupération des issues et pull requests
    activity = github.get_feed(
        limit=15,
        type='all',                         # 'all', 'issues' ou 'pulls'
        state='open'                        # 'open', 'closed' ou 'all'
    )
    
    for item in activity:
        if item['type'] == 'issue':
            print(f"Issue #{item['number']}: {item['title']}")
        else:
            print(f"PR #{item['number']}: {item['title']} ({item['branch']})")
    
    # Informations du profil
    profile = github.get_profile_info()
    print(f"Profil: {profile['login']} ({profile['public_repos']} repos publics)")
    
    # Fermeture d'une issue (GitHub ne permet pas la suppression via API)
    github.delete_post('issue:username:repository:42')
    
    # Suppression d'un commentaire
    github.delete_post('comment:username:repository:123')
```

## 🎯 Bonnes pratiques

### 1. Gestion des tokens

```python
import os
from datetime import datetime, timedelta

class TokenManager:
    """Gestionnaire de tokens avec renouvellement automatique."""
    
    def __init__(self):
        self.tokens = {}
        self.expiry_times = {}
    
    def get_token(self, platform: str) -> str:
        """Récupère un token valide."""
        if self.is_token_expired(platform):
            self.refresh_token(platform)
        return self.tokens.get(platform)
    
    def is_token_expired(self, platform: str) -> bool:
        """Vérifie si le token a expiré."""
        expiry = self.expiry_times.get(platform)
        if not expiry:
            return True
        return datetime.now() > expiry
    
    def refresh_token(self, platform: str):
        """Renouvelle le token."""
        # Logique de renouvellement spécifique à chaque plateforme
        pass
```

### 2. Rate limiting intelligent

```python
from time import sleep
import random

class RateLimiter:
    """Gestionnaire intelligent des limites de taux."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.last_request_time = 0
        self.request_count = 0
    
    def wait_if_needed(self):
        """Attend si nécessaire pour respecter les limites."""
        current_time = time.time()
        
        if current_time - self.last_request_time < 60:
            if self.request_count >= self.requests_per_minute:
                wait_time = 60 - (current_time - self.last_request_time)
                sleep(wait_time + random.uniform(0.1, 0.5))  # Jitter
                self.request_count = 0
        else:
            self.request_count = 0
        
        self.last_request_time = current_time
        self.request_count += 1
```

### 3. Validation de contenu

```python
def validate_content(content: str, platform: str) -> bool:
    """Valide le contenu avant publication."""
    
    limits = {
        'twitter': 280,
        'linkedin': 3000,
        'facebook': 63206,
        'instagram': 2200,
        'github': 65536     # Limite pour un commentaire/issue
    }
    
    max_length = limits.get(platform, 1000)
    
    if len(content) > max_length:
        raise ValueError(f"Content too long for {platform}: {len(content)}/{max_length}")
    
    # Validation des caractères interdits
    forbidden_chars = ['<script>', '<?php']
    for char in forbidden_chars:
        if char in content.lower():
            raise ValueError(f"Forbidden content detected: {char}")
    
    return True
```

## 🚨 Gestion des erreurs

### Types d'erreurs communes

```python
from connectors.exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError,
    SocialMediaAPIError,
    SocialMediaRateLimitError
)

def handle_social_media_errors(func):
    """Décorateur pour gérer les erreurs des réseaux sociaux."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SocialMediaRateLimitError as e:
            print(f"Rate limit exceeded: {e}")
            # Attendre et réessayer
            sleep(60)
            return func(*args, **kwargs)
        except SocialMediaAuthenticationError as e:
            print(f"Authentication failed: {e}")
            # Renouveler le token
            refresh_authentication()
            return func(*args, **kwargs)
        except SocialMediaAPIError as e:
            print(f"API error: {e}")
            # Logger l'erreur et continuer
            return None
    return wrapper
```

### Retry avec backoff exponentiel

```python
import time
import random
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0):
    """Retry avec backoff exponentiel et jitter."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        raise e
                    
                    # Calcul du délai avec backoff exponentiel et jitter
                    delay = base_delay * (2 ** attempt)
                    jitter = random.uniform(0.1, 0.3) * delay
                    total_delay = delay + jitter
                    
                    print(f"Attempt {attempt + 1} failed, retrying in {total_delay:.2f}s...")
                    time.sleep(total_delay)
            
            raise last_exception
        return wrapper
    return decorator
```

## ⚠️ Limites et restrictions

### Limites par plateforme

| Plateforme | Posts/jour | Caractères max | Rate limit | Spécificités |
|------------|------------|----------------|------------|--------------|
| Twitter | Illimité* | 280 | 300 req/15min | *Avec restrictions |
| LinkedIn | 150 | 3000 | 500 req/jour | Posts personnels |
| Facebook | Illimité | 63,206 | 200 req/heure | Pages uniquement |
| Instagram | 25 | 2,200 | 200 req/heure | Business account |
| YouTube | Illimité | N/A | 10,000 unités/jour | Upload limité |
| TikTok | 20 | N/A | Varie | Beta API |
| GitHub | Illimité | 65,536 | 5000 req/heure | Authentifié |

### Permissions requises

#### Twitter
- Read permissions: `tweet.read`, `users.read`
- Write permissions: `tweet.write`

#### LinkedIn
- Read permissions: `r_liteprofile`, `r_basicprofile`
- Write permissions: `w_member_social`

#### Facebook/Instagram
- Permissions: `pages_manage_posts`, `instagram_basic`
- Compte business requis pour Instagram

#### YouTube
- Scopes: `youtube.readonly`, `youtube.upload` (pour upload)

#### TikTok
- Permissions: `user.info.basic`, `video.list`, `video.upload`

#### GitHub
- Scopes: `repo`, `user`
- Permissions: `issues:write`, `contents:read`

## 📊 Monitoring et métriques

```python
from dataclasses import dataclass
from typing import Dict, Any
import time

@dataclass
class SocialMediaMetrics:
    """Métriques d'utilisation des réseaux sociaux."""
    platform: str
    posts_published: int = 0
    api_calls: int = 0
    errors: int = 0
    rate_limit_hits: int = 0
    total_response_time: float = 0.0
    
    @property
    def average_response_time(self) -> float:
        return self.total_response_time / max(self.api_calls, 1)
    
    @property
    def error_rate(self) -> float:
        return self.errors / max(self.api_calls, 1) * 100

class MetricsCollector:
    """Collecteur de métriques pour les réseaux sociaux."""
    
    def __init__(self):
        self.metrics: Dict[str, SocialMediaMetrics] = {}
    
    def record_api_call(self, platform: str, response_time: float, success: bool = True):
        """Enregistre un appel API."""
        if platform not in self.metrics:
            self.metrics[platform] = SocialMediaMetrics(platform)
        
        metric = self.metrics[platform]
        metric.api_calls += 1
        metric.total_response_time += response_time
        
        if not success:
            metric.errors += 1
    
    def record_post(self, platform: str):
        """Enregistre une publication."""
        if platform not in self.metrics:
            self.metrics[platform] = SocialMediaMetrics(platform)
        
        self.metrics[platform].posts_published += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des métriques."""
        summary = {}
        for platform, metric in self.metrics.items():
            summary[platform] = {
                'posts_published': metric.posts_published,
                'api_calls': metric.api_calls,
                'error_rate': f"{metric.error_rate:.2f}%",
                'avg_response_time': f"{metric.average_response_time:.3f}s"
            }
        return summary
```

## 🔒 Sécurité

### Stockage sécurisé des credentials

```python
import keyring
from cryptography.fernet import Fernet

class SecureCredentialManager:
    """Gestionnaire sécurisé des credentials."""
    
    def __init__(self):
        self.fernet = Fernet(Fernet.generate_key())
    
    def store_credential(self, platform: str, credential_type: str, value: str):
        """Stocke un credential de manière sécurisée."""
        encrypted_value = self.fernet.encrypt(value.encode())
        keyring.set_password(f"social_connector_{platform}", credential_type, encrypted_value.decode())
    
    def get_credential(self, platform: str, credential_type: str) -> str:
        """Récupère un credential."""
        encrypted_value = keyring.get_password(f"social_connector_{platform}", credential_type)
        if encrypted_value:
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        return None
```

### Audit et logging

```python
import logging
from datetime import datetime

class SocialMediaAuditor:
    """Auditeur pour les actions sur les réseaux sociaux."""
    
    def __init__(self):
        self.logger = logging.getLogger('social_media_audit')
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('social_media_audit.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_action(self, platform: str, action: str, details: dict):
        """Log une action sur les réseaux sociaux."""
        self.logger.info(f"Platform: {platform} | Action: {action} | Details: {details}")
    
    def log_post(self, platform: str, content: str, post_id: str = None):
        """Log une publication."""
        self.log_action(platform, "POST", {
            'content_length': len(content),
            'post_id': post_id,
            'timestamp': datetime.now().isoformat()
        })
```

---

Pour plus d'informations, consultez la documentation API officielle de chaque plateforme et les exemples dans le dossier `scripts/`.
