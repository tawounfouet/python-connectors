"""
Connecteur pour Instagram.

Ce module fournit un connecteur pour interagir avec l'API Instagram Basic Display,
permettant de publier des photos et récupérer le contenu.
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


@register_connector("instagram")
class InstagramConnector(SocialMediaConnector):
    """
    Connecteur pour Instagram utilisant l'API Basic Display.
    
    Supporte la publication de photos et la récupération du contenu.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le connecteur Instagram.
        
        Args:
            config: Configuration contenant :
                - access_token: Token d'accès Instagram
                - user_id: ID utilisateur Instagram
        """
        super().__init__(config)
        self.api_base_url = "https://graph.instagram.com"
        self.access_token = config.get('access_token')
        self.user_id = config.get('user_id')
        
        if not self.access_token:
            raise SocialMediaConnectionError(
                "Access token is required for Instagram API"
            )
    
    def connect(self) -> bool:
        """Établit une connexion avec Instagram."""
        try:
            self.session = requests.Session()
            return self.authenticate()
        except Exception as e:
            logging.error(f"Failed to connect to Instagram: {e}")
            return False
    
    def authenticate(self) -> bool:
        """Authentifie avec l'API Instagram."""
        try:
            if not self.session:
                self.session = requests.Session()
            
            # Test de l'authentification
            response = self.session.get(
                f"{self.api_base_url}/me",
                params={'access_token': self.access_token}
            )
            
            if response.status_code == 200:
                self.authenticated = True
                logging.info("Successfully authenticated with Instagram")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"Instagram authentication failed: {e}")
            raise SocialMediaAuthenticationError(f"Instagram authentication failed: {e}")
    
    def post_message(self, content: str, media: Optional[List[str]] = None, 
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Publie un post sur Instagram.
        
        Note: Cette méthode nécessite l'API Instagram Graph qui requiert
        un compte business et des permissions spéciales.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Instagram")
        
        # Pour Instagram, la publication nécessite généralement des médias
        if not media:
            raise SocialMediaAPIError("Instagram posts require media content")
        
        # Cette implémentation est simplifiée - l'API réelle nécessite
        # un processus en deux étapes pour publier du contenu
        raise SocialMediaAPIError(
            "Instagram posting requires Instagram Graph API and business account"
        )
    
    def get_feed(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Récupère le flux Instagram."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Instagram")
        
        try:
            params = {
                'fields': 'id,caption,media_type,media_url,timestamp',
                'limit': min(limit, 100),
                'access_token': self.access_token
            }
            
            response = self.session.get(
                f"{self.api_base_url}/me/media",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                
                if 'data' in data:
                    for post in data['data']:
                        posts.append({
                            'id': post.get('id', ''),
                            'text': post.get('caption', ''),
                            'media_type': post.get('media_type', ''),
                            'media_url': post.get('media_url', ''),
                            'created_at': post.get('timestamp', ''),
                            'platform': 'instagram'
                        })
                
                return posts
            else:
                self._handle_api_error(response)
                return []
                
        except Exception as e:
            logging.error(f"Failed to get Instagram feed: {e}")
            raise SocialMediaAPIError(f"Failed to get Instagram feed: {e}")
    
    def get_profile_info(self) -> Dict[str, Any]:
        """Récupère les informations du profil Instagram."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Instagram")
        
        try:
            response = self.session.get(
                f"{self.api_base_url}/me",
                params={
                    'fields': 'id,username,account_type,media_count',
                    'access_token': self.access_token
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'id': data.get('id', ''),
                    'username': data.get('username', ''),
                    'account_type': data.get('account_type', ''),
                    'media_count': data.get('media_count', 0),
                    'platform': 'instagram'
                }
            else:
                self._handle_api_error(response)
                return {}
                
        except Exception as e:
            logging.error(f"Failed to get Instagram profile: {e}")
            raise SocialMediaAPIError(f"Failed to get Instagram profile: {e}")
    
    def delete_post(self, post_id: str) -> bool:
        """Supprime un post Instagram."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Instagram")
        
        try:
            response = self.session.delete(
                f"{self.api_base_url}/{post_id}",
                params={'access_token': self.access_token}
            )
            
            if response.status_code == 200:
                logging.info(f"Successfully deleted Instagram post {post_id}")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"Failed to delete Instagram post {post_id}: {e}")
            raise SocialMediaAPIError(f"Failed to delete Instagram post: {e}")
