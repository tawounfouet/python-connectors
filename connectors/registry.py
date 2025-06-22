"""
Registre pour l'enregistrement dynamique des connecteurs.
"""

from typing import Dict, Type, Any, Optional
import logging

from .base import BaseConnector
from .exceptions import ConfigurationError
from .utils.logger import global_logger

logger = global_logger


class ConnectorRegistry:
    """Registre pour les connecteurs."""
    
    def __init__(self):
        self._connectors: Dict[str, Type[BaseConnector]] = {}
        self._instances: Dict[str, BaseConnector] = {}
    
    def register(self, name: str, connector_class: Type[BaseConnector]):
        """
        Enregistre un connecteur.
        
        Args:
            name: Nom du connecteur
            connector_class: Classe du connecteur
        """
        if not issubclass(connector_class, BaseConnector):
            raise ConfigurationError(f"Connector class must inherit from BaseConnector: {connector_class}")
        
        self._connectors[name] = connector_class
        logger.info(f"Registered connector: {name} -> {connector_class.__name__}")
    
    def unregister(self, name: str):
        """Désenregistre un connecteur."""
        if name in self._connectors:
            del self._connectors[name]
            logger.info(f"Unregistered connector: {name}")
        
        # Supprime aussi l'instance si elle existe
        if name in self._instances:
            instance = self._instances[name]
            if hasattr(instance, 'disconnect') and instance.is_connected:
                instance.disconnect()
            del self._instances[name]
    
    def get_connector_class(self, name: str) -> Type[BaseConnector]:
        """
        Retourne la classe d'un connecteur.
        
        Args:
            name: Nom du connecteur
            
        Returns:
            Classe du connecteur
            
        Raises:
            ConfigurationError: Si le connecteur n'est pas trouvé
        """
        if name not in self._connectors:
            available = list(self._connectors.keys())
            raise ConfigurationError(f"Connector '{name}' not found. Available: {available}")
        
        return self._connectors[name]
    
    def create_connector(self, name: str, config: Dict[str, Any], 
                        instance_name: Optional[str] = None) -> BaseConnector:
        """
        Crée une instance de connecteur.
        
        Args:
            name: Nom du connecteur
            config: Configuration du connecteur
            instance_name: Nom de l'instance (optionnel)
            
        Returns:
            Instance du connecteur
        """
        connector_class = self.get_connector_class(name)
        instance = connector_class(config, connector_name=instance_name or name)
        
        # Stocke l'instance si un nom est fourni
        if instance_name:
            self._instances[instance_name] = instance
        
        logger.info(f"Created connector instance: {name} (instance: {instance_name or 'anonymous'})")
        return instance
    
    def get_instance(self, instance_name: str) -> BaseConnector:
        """
        Retourne une instance de connecteur existante.
        
        Args:
            instance_name: Nom de l'instance
            
        Returns:
            Instance du connecteur
            
        Raises:
            ConfigurationError: Si l'instance n'est pas trouvée
        """
        if instance_name not in self._instances:
            available = list(self._instances.keys())
            raise ConfigurationError(f"Connector instance '{instance_name}' not found. Available: {available}")
        
        return self._instances[instance_name]
    
    def list_connectors(self) -> Dict[str, str]:
        """Retourne la liste des connecteurs enregistrés."""
        return {name: cls.__name__ for name, cls in self._connectors.items()}
    
    def list_instances(self) -> Dict[str, str]:
        """Retourne la liste des instances créées."""
        return {name: instance.__class__.__name__ for name, instance in self._instances.items()}
    
    def cleanup_instances(self):
        """Ferme toutes les instances et nettoie le registre."""
        for name, instance in list(self._instances.items()):
            try:
                if hasattr(instance, 'disconnect') and instance.is_connected:
                    instance.disconnect()
                    logger.info(f"Disconnected instance: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting instance {name}: {e}")
        
        self._instances.clear()
        logger.info("Cleaned up all connector instances")


# Instance globale du registre
registry = ConnectorRegistry()


def register_connector(name: str):
    """
    Décorateur pour enregistrer automatiquement un connecteur.
    
    Usage:
        @register_connector("postgres")
        class PostgreSQLConnector(DatabaseConnector):
            pass
    """
    def decorator(connector_class: Type[BaseConnector]):
        registry.register(name, connector_class)
        return connector_class
    return decorator


# Fonctions de convenance
def create_connector(name: str, config: Dict[str, Any], 
                    instance_name: Optional[str] = None) -> BaseConnector:
    """Crée un connecteur via le registre global."""
    return registry.create_connector(name, config, instance_name)


def get_connector(instance_name: str) -> BaseConnector:
    """Récupère une instance de connecteur via le registre global."""
    return registry.get_instance(instance_name)


def list_available_connectors() -> Dict[str, str]:
    """Liste tous les connecteurs disponibles."""
    return registry.list_connectors()
