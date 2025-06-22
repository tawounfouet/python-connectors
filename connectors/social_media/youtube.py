"""
Connecteur pour YouTube.

Ce module fournit un connecteur pour interagir avec l'API YouTube Data,
permettant de gérer les vidéos, playlists et chaînes.
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


@register_connector("youtube")
class YouTubeConnector(SocialMediaConnector):
    """
    Connecteur pour YouTube utilisant l'API YouTube Data v3.
    
    Supporte la gestion des vidéos, playlists et informations de chaîne.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le connecteur YouTube.
        
        Args:
            config: Configuration contenant :
                - api_key: Clé API YouTube Data
                - access_token: Token d'accès OAuth (pour les opérations d'écriture)
        """
        super().__init__(config)
        self.api_base_url = "https://www.googleapis.com/youtube/v3"
        self.api_key = config.get('api_key')
        self.access_token = config.get('access_token')
        
        if not self.api_key:
            raise SocialMediaConnectionError(
                "API key is required for YouTube API"
            )
    
    def connect(self) -> bool:
        """Établit une connexion avec YouTube."""
        try:
            self.session = requests.Session()
            return self.authenticate()
        except Exception as e:
            logging.error(f"Failed to connect to YouTube: {e}")
            return False
    
    def authenticate(self) -> bool:
        """Authentifie avec l'API YouTube."""
        try:
            if not self.session:
                self.session = requests.Session()
            
            # Configuration des headers si un token d'accès est fourni
            if self.access_token:
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
            
            # Test de l'authentification en récupérant les infos du canal
            params = {'part': 'snippet', 'mine': 'true', 'key': self.api_key}
            response = self.session.get(f"{self.api_base_url}/channels", params=params)
            
            if response.status_code == 200:
                self.authenticated = True
                logging.info("Successfully authenticated with YouTube")
                return True
            else:
                # Fallback: test avec juste la clé API
                params = {'part': 'snippet', 'id': 'UC_x5XG1OV2P6uZZ5FSM9Ttw', 'key': self.api_key}
                response = self.session.get(f"{self.api_base_url}/channels", params=params)
                if response.status_code == 200:
                    self.authenticated = True
                    return True
                else:
                    self._handle_api_error(response)
                    return False
                
        except Exception as e:
            logging.error(f"YouTube authentication failed: {e}")
            raise SocialMediaAuthenticationError(f"YouTube authentication failed: {e}")
    
    def post_message(self, content: str, media: Optional[List[str]] = None, 
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Publie une vidéo sur YouTube.
        
        Note: Cette méthode nécessite l'upload d'une vidéo, ce qui est complexe
        et nécessite des permissions spéciales.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with YouTube")
        
        # L'upload de vidéo sur YouTube nécessite un processus complexe
        # avec des chunks et des métadonnées spécifiques
        raise SocialMediaAPIError(
            "YouTube video upload requires specialized implementation with file handling"
        )
    
    def get_feed(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Récupère les vidéos de la chaîne."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with YouTube")
        
        try:
            # Récupération des vidéos de la chaîne
            params = {
                'part': 'snippet,statistics',
                'mine': 'true',
                'order': 'date',
                'maxResults': min(limit, 50),
                'key': self.api_key
            }
            
            response = self.session.get(f"{self.api_base_url}/search", params=params)
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                if 'items' in data:
                    for video in data['items']:
                        snippet = video.get('snippet', {})
                        videos.append({
                            'id': video.get('id', {}).get('videoId', ''),
                            'title': snippet.get('title', ''),
                            'description': snippet.get('description', ''),
                            'published_at': snippet.get('publishedAt', ''),
                            'thumbnail': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                            'url': f"https://www.youtube.com/watch?v={video.get('id', {}).get('videoId', '')}",
                            'platform': 'youtube'
                        })
                
                return videos
            else:
                self._handle_api_error(response)
                return []
                
        except Exception as e:
            logging.error(f"Failed to get YouTube videos: {e}")
            raise SocialMediaAPIError(f"Failed to get YouTube videos: {e}")
    
    def get_profile_info(self) -> Dict[str, Any]:
        """Récupère les informations de la chaîne YouTube."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with YouTube")
        
        try:
            params = {
                'part': 'snippet,statistics',
                'mine': 'true',
                'key': self.api_key
            }
            
            response = self.session.get(f"{self.api_base_url}/channels", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and data['items']:
                    channel = data['items'][0]
                    snippet = channel.get('snippet', {})
                    statistics = channel.get('statistics', {})
                    
                    return {
                        'id': channel.get('id', ''),
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'subscriber_count': statistics.get('subscriberCount', 0),
                        'video_count': statistics.get('videoCount', 0),
                        'view_count': statistics.get('viewCount', 0),
                        'thumbnail': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                        'platform': 'youtube'
                    }
                return {}
            else:
                self._handle_api_error(response)
                return {}
                
        except Exception as e:
            logging.error(f"Failed to get YouTube channel info: {e}")
            raise SocialMediaAPIError(f"Failed to get YouTube channel info: {e}")
    
    def delete_post(self, post_id: str) -> bool:
        """Supprime une vidéo YouTube."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with YouTube")
        
        if not self.access_token:
            raise SocialMediaAPIError("Access token required for video deletion")
        
        try:
            params = {'id': post_id, 'key': self.api_key}
            response = self.session.delete(f"{self.api_base_url}/videos", params=params)
            
            if response.status_code == 204:
                logging.info(f"Successfully deleted YouTube video {post_id}")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"Failed to delete YouTube video {post_id}: {e}")
            raise SocialMediaAPIError(f"Failed to delete YouTube video: {e}")
    
    def get_playlists(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère les playlists de la chaîne."""
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with YouTube")
        
        try:
            params = {
                'part': 'snippet,status',
                'mine': 'true',
                'maxResults': min(limit, 50),
                'key': self.api_key
            }
            
            response = self.session.get(f"{self.api_base_url}/playlists", params=params)
            
            if response.status_code == 200:
                data = response.json()
                playlists = []
                
                if 'items' in data:
                    for playlist in data['items']:
                        snippet = playlist.get('snippet', {})
                        playlists.append({
                            'id': playlist.get('id', ''),
                            'title': snippet.get('title', ''),
                            'description': snippet.get('description', ''),
                            'published_at': snippet.get('publishedAt', ''),
                            'thumbnail': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                            'platform': 'youtube'
                        })
                
                return playlists
            else:
                self._handle_api_error(response)
                return []
                
        except Exception as e:
            logging.error(f"Failed to get YouTube playlists: {e}")
            raise SocialMediaAPIError(f"Failed to get YouTube playlists: {e}")
