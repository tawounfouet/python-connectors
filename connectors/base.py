"""
Classes de base pour tous les connecteurs.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from contextlib import contextmanager
import os

from .config import ConnectorConfig
from .exceptions import ConnectorError, ConnectionError
from .utils import MetricsCollector, retry_on_exception
from .utils.logger import setup_logger, global_logger

# Logger pour ce module
logger = global_logger


class BaseConnector(ABC):
    """Classe de base pour tous les connecteurs."""
    
    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        """
        Initialise le connecteur.
        
        Args:
            config: Configuration du connecteur
            connector_name: Nom du connecteur (pour les métriques)
        """
        self.config = config
        self.connector_name = connector_name or self.__class__.__name__
        self._connected = False
        
        # Initialisation des métriques si activées
        if config.get('metrics_enabled', True):
            self.metrics = MetricsCollector(self.connector_name)
        else:
            self.metrics = None
        
        # Configuration du logging
        if config.get('logging', {}):
            log_config = config.get('logging', {})
            self.logger = setup_logger(
                name=f"connectors.{self.connector_name}",
                config=log_config
            )
        else:
            # Utiliser le logger global avec le nom du connecteur
            self.logger = logging.getLogger(f"connectors.{self.connector_name}")
            log_level = config.get('log_level', 'INFO')
            self.logger.setLevel(getattr(logging, log_level))
        
        self.logger.info(f"Initialized connector: {self.connector_name}")
    
    @abstractmethod
    def connect(self):
        """Établit la connexion au système externe."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Ferme la connexion au système externe."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Teste la connexion au système externe.
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        pass
    
    def connect_with_retry(self):
        """Établit la connexion avec retry automatique."""
        retry_config = self.config.get('retry', {})
        
        @retry_on_exception(
            max_attempts=retry_config.get('max_attempts', 3),
            backoff_factor=retry_config.get('backoff_factor', 2.0),
            initial_delay=retry_config.get('initial_delay', 1.0),
            max_delay=retry_config.get('max_delay', 60.0),
            exceptions=(ConnectionError,)
        )        
        def _connect():
            return self.connect()
        
        result = _connect()
        if self.metrics:
            self.metrics.increment_connection_count()
        
        self._connected = True
        self.logger.debug(f"Connection established for {self.connector_name}")
        return result
    
    def execute_with_metrics(self, operation_name: str, func, *args, **kwargs):
        """
        Exécute une fonction en collectant les métriques.
        
        Args:
            operation_name: Nom de l'opération pour les métriques
            func: Fonction à exécuter
            *args, **kwargs: Arguments pour la fonction
        """
        if not self.metrics:
            if callable(func):
                return func(*args, **kwargs)
            else:
                return func
        
        metric = self.metrics.start_operation(operation_name)
        try:
            if callable(func):
                result = func(*args, **kwargs)
            else:
                result = func
            self.metrics.end_operation(metric, success=True)
            return result
        except Exception as e:
            self.metrics.end_operation(metric, success=False, error_message=str(e))
            raise
    
    @contextmanager
    def connection(self):
        """
        Context manager pour la gestion automatique des connexions.
        
        Usage:
            with connector.connection():
                # Utilisation du connecteur
                pass
        """
        try:
            if not self._connected:
                self.connect_with_retry()
            yield self
        except Exception as e:
            self.logger.error(f"Error in connection context: {e}")
            raise
        finally:
            if self._connected:
                try:
                    self.disconnect()
                    self._connected = False
                except Exception as e:
                    self.logger.error(f"Error during disconnect: {e}")
    
    def __enter__(self):
        """Support pour with statement."""
        self.connect_with_retry()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support pour with statement."""
        if self._connected:
            self.disconnect()
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Retourne True si le connecteur est connecté."""
        return self._connected
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des métriques."""
        if not self.metrics:
            return {"metrics_enabled": False}
        
        metrics = self.metrics.get_metrics()
        return {
            "connector_name": metrics.connector_name,
            "total_operations": len(metrics.operations),
            "success_rate": metrics.success_rate,
            "average_duration": metrics.average_duration,
            "total_connections": metrics.connection_count,
            "metrics_enabled": True
        }


class DatabaseConnector(BaseConnector):
    """Classe de base spécialisée pour les connecteurs de bases de données."""
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête SQL."""
        pass
    
    @abstractmethod
    def execute_many(self, query: str, params_list: list):
        """Exécute une requête avec plusieurs jeux de paramètres."""
        pass
    
    @abstractmethod
    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête et retourne un seul résultat."""
        pass
    
    @abstractmethod
    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête et retourne tous les résultats."""
        pass


class FileSystemConnector(BaseConnector):
    """Classe de base pour les connecteurs de systèmes de fichiers."""
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str):
        """Upload un fichier."""
        pass
    
    @abstractmethod
    def download_file(self, remote_path: str, local_path: str):
        """Download un fichier."""
        pass
    
    @abstractmethod
    def list_files(self, path: str) -> list:
        """Liste les fichiers dans un répertoire."""
        pass
    
    @abstractmethod
    def delete_file(self, path: str):
        """Supprime un fichier."""
        pass


class MessagingConnector(BaseConnector):
    """Classe de base pour les connecteurs de messagerie."""
    
    @abstractmethod
    def send_message(self, message: str, recipient: str, **kwargs):
        """Envoie un message."""
        pass
    
    @abstractmethod
    def receive_messages(self, **kwargs) -> list:
        """Reçoit des messages."""
        pass
