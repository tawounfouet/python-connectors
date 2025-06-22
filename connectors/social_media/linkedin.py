"""
Connecteur pour LinkedIn.

Ce module fournit un connecteur pour interagir avec l'API LinkedIn,
permettant de publier des posts, récupérer le flux et gérer le profil professionnel.
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


@register_connector("linkedin")
class LinkedInConnector(SocialMediaConnector):
    """
    Connecteur pour LinkedIn utilisant l'API LinkedIn v2.
    
    Supporte l'authentification OAuth 2.0 et les opérations de publication,
    récupération de flux et gestion de profil professionnel.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le connecteur LinkedIn.
        
        Args:
            config: Configuration contenant :
                - access_token: Token d'accès OAuth 2.0
                - client_id: ID client de l'application LinkedIn
                - client_secret: Secret client de l'application
        """
        super().__init__(config)
        self.api_base_url = "https://api.linkedin.com/v2"
        self.access_token = config.get('access_token')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        
        if not self.access_token:
            raise SocialMediaConnectionError(
                "Access token is required for LinkedIn API"
            )
    
    def connect(self) -> bool:
        """
        Établit une connexion avec LinkedIn.
        
        Returns:
            bool: True si la connexion réussit.
        """
        try:
            self.session = requests.Session()
            return self.authenticate()
        except Exception as e:
            logging.error(f"Failed to connect to LinkedIn: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        Authentifie avec l'API LinkedIn.
        
        Returns:
            bool: True si l'authentification réussit.
        """
        try:
            if not self.session:
                self.session = requests.Session()
            
            # Configuration des headers avec le token d'accès
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            })
            
            # Test de l'authentification en récupérant les infos du profil
            response = self.session.get(f"{self.api_base_url}/people/~")
            
            if response.status_code == 200:
                self.authenticated = True
                logging.info("Successfully authenticated with LinkedIn")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"LinkedIn authentication failed: {e}")
            raise SocialMediaAuthenticationError(f"LinkedIn authentication failed: {e}")
    
    def post_message(self, content: str, media: Optional[List[str]] = None, 
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Publie un post sur LinkedIn.
        
        Args:
            content: Le contenu du post.
            media: Liste de chemins vers des fichiers média (non supporté dans cette version).
            options: Options supplémentaires (visibility, etc.).
            
        Returns:
            Dict contenant les informations du post publié.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with LinkedIn")
        
        # Récupération de l'ID de la personne pour le post
        person_info = self._get_person_id()
        if not person_info:
            raise SocialMediaAPIError("Could not retrieve person ID")
        
        person_urn = person_info['id']
        
        # Construction du payload pour le post
        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Personnalisation de la visibilité si spécifiée
        if options and 'visibility' in options:
            visibility = options['visibility'].upper()
            if visibility in ['PUBLIC', 'CONNECTIONS']:
                payload['visibility'] = {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/ugcPosts",
                data=json.dumps(payload)
            )
            
            self._update_rate_limit_info(response.headers)
            
            if response.status_code == 201:
                post_data = response.json()
                post_id = post_data.get('id', '')
                
                return {
                    'id': post_id,
                    'text': content,
                    'url': f"https://www.linkedin.com/feed/update/{post_id}/",
                    'created_at': datetime.now().isoformat(),
                    'platform': 'linkedin'
                }
            else:
                self._handle_api_error(response)
                
        except Exception as e:
            logging.error(f"Failed to post on LinkedIn: {e}")
            raise SocialMediaAPIError(f"Failed to post on LinkedIn: {e}")
    
    def get_feed(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Récupère le flux LinkedIn de l'utilisateur.
        
        Args:
            limit: Nombre maximum de posts à récupérer.
            **kwargs: Paramètres supplémentaires.
            
        Returns:
            Liste des posts du flux.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with LinkedIn")
        
        try:
            # Récupération des posts de l'utilisateur
            params = {
                'count': min(limit, 50),  # LinkedIn limite à 50
                'start': 0
            }
            
            response = self.session.get(
                f"{self.api_base_url}/ugcPosts",
                params=params
            )
            
            self._update_rate_limit_info(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                
                if 'elements' in data:
                    for post in data['elements']:
                        post_content = post.get('specificContent', {}).get(
                            'com.linkedin.ugc.ShareContent', {}
                        )
                        commentary = post_content.get('shareCommentary', {})
                        
                        posts.append({
                            'id': post.get('id', ''),
                            'text': commentary.get('text', ''),
                            'created_at': post.get('created', {}).get('time', ''),
                            'author': post.get('author', ''),
                            'platform': 'linkedin'
                        })
                
                return posts
            else:
                self._handle_api_error(response)
                return []
                
        except Exception as e:
            logging.error(f"Failed to get LinkedIn feed: {e}")
            raise SocialMediaAPIError(f"Failed to get LinkedIn feed: {e}")
    
    def get_profile_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du profil LinkedIn.
        
        Returns:
            Dict contenant les informations du profil.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with LinkedIn")
        
        try:
            # Récupération des informations de base
            response = self.session.get(
                f"{self.api_base_url}/people/~",
                params={
                    'projection': '(id,firstName,lastName,headline,profilePicture(displayImage~:playableStreams))'
                }
            )
            
            self._update_rate_limit_info(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Construction du nom complet
                first_name = data.get('firstName', {}).get('localized', {})
                last_name = data.get('lastName', {}).get('localized', {})
                
                full_name = ""
                if first_name and last_name:
                    # Prendre la première langue disponible
                    first_key = list(first_name.keys())[0] if first_name else ""
                    last_key = list(last_name.keys())[0] if last_name else ""
                    if first_key and last_key:
                        full_name = f"{first_name[first_key]} {last_name[last_key]}"
                
                return {
                    'id': data.get('id', ''),
                    'name': full_name,
                    'headline': data.get('headline', {}).get('localized', {}).get('en_US', ''),
                    'profile_url': f"https://www.linkedin.com/in/{data.get('id', '')}",
                    'platform': 'linkedin'
                }
            else:
                self._handle_api_error(response)
                return {}
                
        except Exception as e:
            logging.error(f"Failed to get LinkedIn profile: {e}")
            raise SocialMediaAPIError(f"Failed to get LinkedIn profile: {e}")
    
    def get_connections(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère la liste des connexions LinkedIn.
        
        Args:
            limit: Nombre maximum de connexions à récupérer.
            
        Returns:
            Liste des connexions.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with LinkedIn")
        
        try:
            params = {
                'count': min(limit, 500),  # LinkedIn limite à 500
                'start': 0
            }
            
            response = self.session.get(
                f"{self.api_base_url}/people/~/connections",
                params=params
            )
            
            self._update_rate_limit_info(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                connections = []
                
                if 'values' in data:
                    for connection in data['values']:
                        connections.append({
                            'id': connection.get('id', ''),
                            'first_name': connection.get('firstName', ''),
                            'last_name': connection.get('lastName', ''),
                            'headline': connection.get('headline', ''),
                            'industry': connection.get('industry', ''),
                            'platform': 'linkedin'
                        })
                
                return connections
            else:
                self._handle_api_error(response)
                return []
                
        except Exception as e:
            logging.error(f"Failed to get LinkedIn connections: {e}")
            raise SocialMediaAPIError(f"Failed to get LinkedIn connections: {e}")
    
    def delete_post(self, post_id: str) -> bool:
        """
        Supprime un post LinkedIn.
        
        Args:
            post_id: ID du post à supprimer.
            
        Returns:
            bool: True si la suppression réussit.
        """
        if not self.authenticated:
            raise SocialMediaAuthenticationError("Not authenticated with LinkedIn")
        
        try:
            response = self.session.delete(f"{self.api_base_url}/ugcPosts/{post_id}")
            
            self._update_rate_limit_info(response.headers)
            
            if response.status_code == 204:
                logging.info(f"Successfully deleted LinkedIn post {post_id}")
                return True
            else:
                self._handle_api_error(response)
                return False
                
        except Exception as e:
            logging.error(f"Failed to delete LinkedIn post {post_id}: {e}")
            raise SocialMediaAPIError(f"Failed to delete LinkedIn post: {e}")
    
    def _get_person_id(self) -> Optional[Dict[str, Any]]:
        """
        Récupère l'ID de la personne connectée.
        
        Returns:
            Dict avec l'ID de la personne ou None si échec.
        """
        try:
            response = self.session.get(f"{self.api_base_url}/people/~")
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """
        Met à jour les informations de limite de taux à partir des headers LinkedIn.
        
        Args:
            headers: Headers de la réponse HTTP.
        """
        # LinkedIn utilise des headers différents pour les rate limits
        rate_limit_headers = {
            'limit': headers.get('X-RateLimit-Limit'),
            'remaining': headers.get('X-RateLimit-Remaining'),
            'reset': headers.get('X-RateLimit-Reset')
        }
        
        if any(rate_limit_headers.values()):
            try:
                self.rate_limit_info = {
                    'limit': int(rate_limit_headers['limit']) if rate_limit_headers['limit'] else None,
                    'remaining': int(rate_limit_headers['remaining']) if rate_limit_headers['remaining'] else None,
                    'reset_time': int(rate_limit_headers['reset']) if rate_limit_headers['reset'] else None
                }
            except (ValueError, TypeError):
                pass
