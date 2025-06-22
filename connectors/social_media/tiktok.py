"""
Connecteur pour TikTok.

Ce module fournit un connecteur pour interagir avec l'API TikTok,
permettant de publier des vidéos et récupérer le contenu.
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


@register_connector("tiktok")
class TikTokConnector(SocialMediaConnector):
    """
    Connecteur pour TikTok utilisant l'API TikTok for Developers.
    
    Supporte la publication de vidéos et la récupération du contenu.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le connecteur TikTok.
        
        Args:
            config: Configuration contenant :
                - access_token: Token d'accès TikTok
                - client_key: Clé client de l'application
        """
        super().__init__(config)
        self.api_base_url = "https://open-api.tiktok.com"
        self.access_token = config.get('access_token')
        self.client_key = config.get('client_key')
        
        if not self.access_token:
            raise SocialMediaConnectionError(
                "Access token is required for TikTok API"
            )
    
    def connect(self) -> bool:
        """Établit une connexion avec TikTok."""
        try:
            self.session = requests.Session()
            return self.authenticate()
        except Exception as e:
            logging.error(f"Failed to connect to TikTok: {e}")
            return False
    
    def authenticate(self) -> bool:
        """Authentifie avec l'API TikTok."""
        try:
            if not self.session:
                self.session = requests.Session()
            
            # Configuration des headers
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            })
            
            # Test de l'authentification
            response = self.session.post(
                f"{self.api_base_url}/v2/user/info/",
                json={'access_token': self.access_token}
            )
            
            if response.status_code == 200:
                self.authenticated = True
                logging.info("Successfully authenticated with TikTok")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"TikTok authentication failed: {e}")
            raise SocialMediaAuthenticationError(f"TikTok authentication failed: {e}")
    
    def post_message(self, content: str, media: Optional[List[str]] = None, 
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Publie une vidéo sur TikTok.
        
        Note: TikTok nécessite obligatoirement une vidéo pour publier du contenu.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with TikTok")
        
        if not media:
            raise SocialMediaAPIError("TikTok posts require video content")
        
        # L'upload de vidéo sur TikTok nécessite un processus complexe
        # avec des chunks et la gestion de fichiers binaires
        raise SocialMediaAPIError(
            "TikTok video upload requires specialized implementation with file handling"
        )
    
    def get_feed(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Récupère les vidéos TikTok de l'utilisateur."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with TikTok")
        
        try:
            payload = {
                'access_token': self.access_token,
                'max_count': min(limit, 20)  # TikTok limite à 20
            }
            
            response = self.session.post(
                f"{self.api_base_url}/v2/video/list/",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                if 'data' in data and 'videos' in data['data']:
                    for video in data['data']['videos']:
                        videos.append({
                            'id': video.get('id', ''),
                            'title': video.get('title', ''),
                            'description': video.get('description', ''),
                            'created_at': video.get('create_time', ''),
                            'view_count': video.get('view_count', 0),
                            'like_count': video.get('like_count', 0),
                            'comment_count': video.get('comment_count', 0),
                            'share_count': video.get('share_count', 0),
                            'url': video.get('share_url', ''),
                            'platform': 'tiktok'
                        })
                
                return videos
            else:
                self._handle_api_error(response)
                return []
                
        except Exception as e:
            logging.error(f"Failed to get TikTok videos: {e}")
            raise SocialMediaAPIError(f"Failed to get TikTok videos: {e}")
    
    def get_profile_info(self) -> Dict[str, Any]:
        """Récupère les informations du profil TikTok."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with TikTok")
        
        try:
            payload = {'access_token': self.access_token}
            
            response = self.session.post(
                f"{self.api_base_url}/v2/user/info/",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'user' in data['data']:
                    user = data['data']['user']
                    return {
                        'id': user.get('open_id', ''),
                        'username': user.get('display_name', ''),
                        'bio': user.get('bio_description', ''),
                        'follower_count': user.get('follower_count', 0),
                        'following_count': user.get('following_count', 0),
                        'likes_count': user.get('likes_count', 0),
                        'video_count': user.get('video_count', 0),
                        'avatar_url': user.get('avatar_url', ''),
                        'platform': 'tiktok'
                    }
                return {}
            else:
                self._handle_api_error(response)
                return {}
                
        except Exception as e:
            logging.error(f"Failed to get TikTok profile: {e}")
            raise SocialMediaAPIError(f"Failed to get TikTok profile: {e}")
    
    def delete_post(self, post_id: str) -> bool:
        """
        Supprime une vidéo TikTok.
        
        Note: La suppression n'est pas disponible dans toutes les versions de l'API TikTok.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with TikTok")
        
        try:
            payload = {
                'access_token': self.access_token,
                'video_id': post_id
            }
            
            response = self.session.post(
                f"{self.api_base_url}/v2/video/delete/",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data', {}).get('error_code') == 0:
                    logging.info(f"Successfully deleted TikTok video {post_id}")
                    return True
                else:
                    error_msg = data.get('data', {}).get('description', 'Unknown error')
                    raise SocialMediaAPIError(f"TikTok deletion failed: {error_msg}")
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"Failed to delete TikTok video {post_id}: {e}")
            raise SocialMediaAPIError(f"Failed to delete TikTok video: {e}")
    
    def get_video_analytics(self, video_id: str) -> Dict[str, Any]:
        """Récupère les analytics d'une vidéo TikTok."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with TikTok")
        
        try:
            payload = {
                'access_token': self.access_token,
                'video_id': video_id
            }
            
            response = self.session.post(
                f"{self.api_base_url}/v2/video/data/",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    analytics = data['data']
                    return {
                        'video_id': video_id,
                        'view_count': analytics.get('view_count', 0),
                        'like_count': analytics.get('like_count', 0),
                        'comment_count': analytics.get('comment_count', 0),
                        'share_count': analytics.get('share_count', 0),
                        'platform': 'tiktok'
                    }
                return {}
            else:
                self._handle_api_error(response)
                return {}
                
        except Exception as e:
            logging.error(f"Failed to get TikTok video analytics: {e}")
            raise SocialMediaAPIError(f"Failed to get TikTok video analytics: {e}")
