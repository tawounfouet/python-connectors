"""
Interface de base pour tous les connecteurs de réseaux sociaux.

Ce module définit l'interface commune que tous les connecteurs de réseaux sociaux
doivent implémenter, garantissant une API cohérente.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime

from ..base import BaseConnector
from ..exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError,
    SocialMediaAPIError
)


class SocialMediaConnector(BaseConnector):
    """
    Interface commune pour tous les connecteurs de réseaux sociaux.
    
    Cette classe abstraite définit les méthodes que chaque connecteur
    de réseau social doit implémenter.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le connecteur avec la configuration fournie.
        
        Args:
            config: Configuration contenant les paramètres d'authentification
                   et autres options spécifiques à la plateforme.
        """
        super().__init__(config)
        self.platform_name = self.__class__.__name__.replace('Connector', '').lower()
        self.session = None
        self.authenticated = False
        self.rate_limit_info = {}
        
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authentifie l'utilisateur auprès de la plateforme.
        
        Returns:
            bool: True si l'authentification réussit, False sinon.
            
        Raises:
            SocialMediaAuthenticationError: Si l'authentification échoue.
        """
        pass
    
    @abstractmethod
    def post_message(self, content: str, media: Optional[List[str]] = None, 
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Publie un message sur la plateforme.
        
        Args:
            content: Le contenu textuel du message.
            media: Liste optionnelle de chemins vers des fichiers média.
            options: Options supplémentaires spécifiques à la plateforme.
            
        Returns:
            Dict contenant les informations sur le message publié (ID, URL, etc.).
            
        Raises:
            SocialMediaAPIError: Si la publication échoue.
        """
        pass
    
    @abstractmethod
    def get_feed(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Récupère les dernières publications du flux.
        
        Args:
            limit: Nombre maximum de publications à récupérer.
            **kwargs: Paramètres supplémentaires spécifiques à la plateforme.
            
        Returns:
            Liste des publications du flux.
            
        Raises:
            SocialMediaAPIError: Si la récupération échoue.
        """
        pass
    
    @abstractmethod
    def get_profile_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du profil connecté.
        
        Returns:
            Dict contenant les informations du profil.
            
        Raises:
            SocialMediaAPIError: Si la récupération échoue.
        """
        pass
    
    @abstractmethod
    def delete_post(self, post_id: str) -> bool:
        """
        Supprime une publication.
        
        Args:
            post_id: Identifiant de la publication à supprimer.
            
        Returns:
            bool: True si la suppression réussit, False sinon.
            
        Raises:
            SocialMediaAPIError: Si la suppression échoue.
        """
        pass
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Récupère les informations sur les limites de taux de l'API.
        
        Returns:
            Dict contenant les informations sur les limites de taux.
        """
        return self.rate_limit_info.copy()
    
    def wait_for_rate_limit(self) -> None:
        """
        Attend si nécessaire pour respecter les limites de taux.
        """
        if 'reset_time' in self.rate_limit_info:
            reset_time = self.rate_limit_info['reset_time']
            if isinstance(reset_time, (int, float)):
                current_time = datetime.now().timestamp()
                if current_time < reset_time:
                    wait_time = reset_time - current_time
                    logging.info(f"Waiting {wait_time:.1f}s for rate limit reset")
                    import time
                    time.sleep(wait_time)
    
    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """
        Met à jour les informations de limite de taux à partir des headers HTTP.
        
        Args:
            headers: Headers de la réponse HTTP contenant les infos de rate limit.
        """
        # À implémenter par chaque plateforme selon ses headers spécifiques
        pass
    
    def _handle_api_error(self, response) -> None:
        """
        Gère les erreurs de l'API.
        
        Args:
            response: Réponse HTTP de l'API.
            
        Raises:
            SocialMediaAPIError: En cas d'erreur API.
        """
        if response.status_code == 401:
            raise SocialMediaAuthenticationError(
                f"Authentication failed for {self.platform_name}"
            )
        elif response.status_code == 429:
            raise SocialMediaAPIError(
                f"Rate limit exceeded for {self.platform_name}"
            )
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                error_message = error_data.get('message', f'API error: {response.status_code}')
            except:
                error_message = f'API error: {response.status_code}'
            
            raise SocialMediaAPIError(
                f"{self.platform_name} API error: {error_message}"
            )
    
    def disconnect(self) -> bool:
        """
        Ferme la connexion avec la plateforme.
        
        Returns:
            bool: True si la déconnexion réussit.
        """
        if self.session:
            self.session.close()
            self.session = None
        self.authenticated = False
        return True
    
    def test_connection(self) -> bool:
        """
        Test la connexion avec la plateforme.
        
        Returns:
            bool: True si la connexion fonctionne.
        """
        try:
            if not self.authenticated:
                self.authenticate()
            
            # Test simple en récupérant les infos du profil
            profile = self.get_profile_info()
            return bool(profile)
            
        except Exception as e:
            logging.error(f"Connection test failed for {self.platform_name}: {e}")
            return False
