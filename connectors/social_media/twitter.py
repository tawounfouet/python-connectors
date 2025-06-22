"""
Connecteur pour Twitter/X.

Ce module fournit un connecteur pour interagir avec l'API Twitter/X,
permettant de publier des tweets, récupérer le flux et gérer le profil.
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .base_social import SocialMediaConnector
from ..exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError,
    SocialMediaAPIError
)
from ..registry import register_connector


@register_connector("twitter")
class TwitterConnector(SocialMediaConnector):
    """
    Connecteur pour Twitter/X utilisant l'API v2.
    
    Supporte l'authentification OAuth 2.0 et les opérations de base
    comme publier des tweets, récupérer le flux et gérer le profil.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le connecteur Twitter.
        
        Args:
            config: Configuration contenant :
                - bearer_token: Token Bearer pour l'API Twitter
                - api_key: Clé API (optionnel pour certaines opérations)
                - api_secret: Secret API (optionnel)
                - access_token: Token d'accès (optionnel)
                - access_token_secret: Secret du token d'accès (optionnel)
        """
        super().__init__(config)
        self.api_base_url = "https://api.twitter.com/2"
        self.bearer_token = config.get('bearer_token')
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.access_token = config.get('access_token')
        self.access_token_secret = config.get('access_token_secret')
        
        if not self.bearer_token:
            raise SocialMediaConnectionError(
                "Bearer token is required for Twitter API"
            )
    
    def connect(self) -> bool:
        """
        Établit une connexion avec Twitter.
        
        Returns:
            bool: True si la connexion réussit.
        """
        try:
            self.session = requests.Session()
            return self.authenticate()
        except Exception as e:
            logging.error(f"Failed to connect to Twitter: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        Authentifie avec l'API Twitter.
        
        Returns:
            bool: True si l'authentification réussit.
        """
        try:
            if not self.session:
                self.session = requests.Session()
            
            # Configuration des headers avec le Bearer token
            self.session.headers.update({
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Type': 'application/json'
            })
            
            # Test de l'authentification en récupérant les infos du profil
            response = self.session.get(
                f"{self.api_base_url}/users/me",
                params={'user.fields': 'id,name,username,public_metrics'}
            )
            
            if response.status_code == 200:
                self.authenticated = True
                logging.info("Successfully authenticated with Twitter")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"Twitter authentication failed: {e}")
            raise SocialMediaAuthenticationError(f"Twitter authentication failed: {e}")
    
    def post_message(self, content: str, media: Optional[List[str]] = None, 
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Publie un tweet.
        
        Args:
            content: Le contenu du tweet (max 280 caractères).
            media: Liste de chemins vers des fichiers média (non supporté dans cette version).
            options: Options supplémentaires (reply_to_id, etc.).
            
        Returns:
            Dict contenant les informations du tweet publié.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Twitter")
        
        if len(content) > 280:
            raise SocialMediaAPIError("Tweet content exceeds 280 characters")
        
        payload = {"text": content}
        
        # Ajout des options si présentes
        if options:
            if 'reply_to_id' in options:
                payload['reply'] = {'in_reply_to_tweet_id': options['reply_to_id']}
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/tweets",
                data=json.dumps(payload)
            )
            
            self._update_rate_limit_info(response.headers)
            
            if response.status_code == 201:
                tweet_data = response.json()
                return {
                    'id': tweet_data['data']['id'],
                    'text': tweet_data['data']['text'],
                    'url': f"https://twitter.com/i/status/{tweet_data['data']['id']}",
                    'created_at': datetime.now().isoformat(),
                    'platform': 'twitter'
                }
            else:
                self._handle_api_error(response)
                
        except Exception as e:
            logging.error(f"Failed to post tweet: {e}")
            raise SocialMediaAPIError(f"Failed to post tweet: {e}")
    
    def get_feed(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Récupère le flux Twitter de l'utilisateur.
        
        Args:
            limit: Nombre maximum de tweets à récupérer (max 100).
            **kwargs: Paramètres supplémentaires (user_id, etc.).
            
        Returns:
            Liste des tweets du flux.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Twitter")
        
        # Limitation de l'API Twitter
        limit = min(limit, 100)
        
        try:
            # Récupération du flux de l'utilisateur authentifié
            params = {
                'max_results': limit,
                'tweet.fields': 'created_at,public_metrics,author_id',
                'user.fields': 'name,username'
            }
            
            response = self.session.get(
                f"{self.api_base_url}/users/me/tweets",
                params=params
            )
            
            self._update_rate_limit_info(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                tweets = []
                
                if 'data' in data:
                    for tweet in data['data']:
                        tweets.append({
                            'id': tweet['id'],
                            'text': tweet['text'],
                            'created_at': tweet.get('created_at', ''),
                            'author_id': tweet.get('author_id', ''),
                            'public_metrics': tweet.get('public_metrics', {}),
                            'url': f"https://twitter.com/i/status/{tweet['id']}",
                            'platform': 'twitter'
                        })
                
                return tweets
            else:
                self._handle_api_error(response)
                return []
                
        except Exception as e:
            logging.error(f"Failed to get Twitter feed: {e}")
            raise SocialMediaAPIError(f"Failed to get Twitter feed: {e}")
    
    def get_profile_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du profil Twitter.
        
        Returns:
            Dict contenant les informations du profil.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Twitter")
        
        try:
            response = self.session.get(
                f"{self.api_base_url}/users/me",
                params={
                    'user.fields': 'id,name,username,description,public_metrics,profile_image_url,verified'
                }
            )
            
            self._update_rate_limit_info(response.headers)
            
            if response.status_code == 200:
                data = response.json()['data']
                return {
                    'id': data['id'],
                    'name': data['name'],
                    'username': data['username'],
                    'description': data.get('description', ''),
                    'followers_count': data.get('public_metrics', {}).get('followers_count', 0),
                    'following_count': data.get('public_metrics', {}).get('following_count', 0),
                    'tweet_count': data.get('public_metrics', {}).get('tweet_count', 0),
                    'profile_image_url': data.get('profile_image_url', ''),
                    'verified': data.get('verified', False),
                    'platform': 'twitter'
                }
            else:
                self._handle_api_error(response)
                return {}
                
        except Exception as e:
            logging.error(f"Failed to get Twitter profile: {e}")
            raise SocialMediaAPIError(f"Failed to get Twitter profile: {e}")
    
    def delete_post(self, post_id: str) -> bool:
        """
        Supprime un tweet.
        
        Args:
            post_id: ID du tweet à supprimer.
            
        Returns:
            bool: True si la suppression réussit.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Twitter")
        
        try:
            response = self.session.delete(f"{self.api_base_url}/tweets/{post_id}")
            
            self._update_rate_limit_info(response.headers)
            
            if response.status_code == 200:
                logging.info(f"Successfully deleted tweet {post_id}")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"Failed to delete tweet {post_id}: {e}")
            raise SocialMediaAPIError(f"Failed to delete tweet: {e}")
    
    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """
        Met à jour les informations de limite de taux à partir des headers Twitter.
        
        Args:
            headers: Headers de la réponse HTTP.
        """
        rate_limit_headers = {
            'limit': headers.get('x-rate-limit-limit'),
            'remaining': headers.get('x-rate-limit-remaining'),
            'reset': headers.get('x-rate-limit-reset')
        }
        
        if rate_limit_headers['reset']:
            try:
                self.rate_limit_info = {
                    'limit': int(rate_limit_headers['limit']) if rate_limit_headers['limit'] else None,
                    'remaining': int(rate_limit_headers['remaining']) if rate_limit_headers['remaining'] else None,
                    'reset_time': int(rate_limit_headers['reset']) if rate_limit_headers['reset'] else None
                }
            except (ValueError, TypeError):
                pass
