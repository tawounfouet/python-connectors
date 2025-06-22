"""
Connecteur pour Facebook.

Ce module fournit un connecteur pour interagir avec l'API Facebook Graph,
permettant de publier des posts, récupérer le flux et gérer les pages.
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


@register_connector("facebook")
class FacebookConnector(SocialMediaConnector):
    """
    Connecteur pour Facebook utilisant l'API Graph.
    
    Supporte la publication de posts, récupération du flux et gestion des pages.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le connecteur Facebook.
        
        Args:
            config: Configuration contenant :
                - access_token: Token d'accès Facebook
                - page_id: ID de la page Facebook (optionnel)
        """
        super().__init__(config)
        self.api_base_url = "https://graph.facebook.com/v18.0"
        self.access_token = config.get('access_token')
        self.page_id = config.get('page_id')
        
        if not self.access_token:
            raise SocialMediaConnectionError(
                "Access token is required for Facebook API"
            )
    
    def connect(self) -> bool:
        """Établit une connexion avec Facebook."""
        try:
            self.session = requests.Session()
            return self.authenticate()
        except Exception as e:
            logging.error(f"Failed to connect to Facebook: {e}")
            return False
    
    def authenticate(self) -> bool:
        """Authentifie avec l'API Facebook."""
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
                logging.info("Successfully authenticated with Facebook")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"Facebook authentication failed: {e}")
            raise SocialMediaAuthenticationError(f"Facebook authentication failed: {e}")
    
    def post_message(self, content: str, media: Optional[List[str]] = None, 
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Publie un post sur Facebook."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Facebook")
        
        endpoint = f"{self.api_base_url}/me/feed"
        if self.page_id:
            endpoint = f"{self.api_base_url}/{self.page_id}/feed"
        
        payload = {
            'message': content,
            'access_token': self.access_token
        }
        
        try:
            response = self.session.post(endpoint, data=payload)
            
            if response.status_code == 200:
                post_data = response.json()
                return {
                    'id': post_data.get('id', ''),
                    'text': content,
                    'url': f"https://www.facebook.com/{post_data.get('id', '')}",
                    'created_at': datetime.now().isoformat(),
                    'platform': 'facebook'
                }
            else:
                self._handle_api_error(response)
                
        except Exception as e:
            logging.error(f"Failed to post on Facebook: {e}")
            raise SocialMediaAPIError(f"Failed to post on Facebook: {e}")
    
    def get_feed(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Récupère le flux Facebook."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Facebook")
        
        endpoint = f"{self.api_base_url}/me/feed"
        if self.page_id:
            endpoint = f"{self.api_base_url}/{self.page_id}/feed"
        
        params = {
            'limit': min(limit, 100),
            'access_token': self.access_token
        }
        
        try:
            response = self.session.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                
                if 'data' in data:
                    for post in data['data']:
                        posts.append({
                            'id': post.get('id', ''),
                            'text': post.get('message', ''),
                            'created_at': post.get('created_time', ''),
                            'platform': 'facebook'
                        })
                
                return posts
            else:
                self._handle_api_error(response)
                return []
                
        except Exception as e:
            logging.error(f"Failed to get Facebook feed: {e}")
            raise SocialMediaAPIError(f"Failed to get Facebook feed: {e}")
    
    def get_profile_info(self) -> Dict[str, Any]:
        """Récupère les informations du profil Facebook."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Facebook")
        
        try:
            response = self.session.get(
                f"{self.api_base_url}/me",
                params={
                    'fields': 'id,name,email',
                    'access_token': self.access_token
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'id': data.get('id', ''),
                    'name': data.get('name', ''),
                    'email': data.get('email', ''),
                    'platform': 'facebook'
                }
            else:
                self._handle_api_error(response)
                return {}
                
        except Exception as e:
            logging.error(f"Failed to get Facebook profile: {e}")
            raise SocialMediaAPIError(f"Failed to get Facebook profile: {e}")
    
    def delete_post(self, post_id: str) -> bool:
        """Supprime un post Facebook."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with Facebook")
        
        try:
            response = self.session.delete(
                f"{self.api_base_url}/{post_id}",
                params={'access_token': self.access_token}
            )
            
            if response.status_code == 200:
                logging.info(f"Successfully deleted Facebook post {post_id}")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"Failed to delete Facebook post {post_id}: {e}")
            raise SocialMediaAPIError(f"Failed to delete Facebook post: {e}")
