"""
Tests pour le module connectors.
"""

import pytest
from unittest.mock import Mock, patch
from connectors import BaseConnector, registry, create_connector
from connectors.exceptions import ConfigurationError, ConnectionError


class MockConnector(BaseConnector):
    """Connecteur mock pour les tests."""
    
    def connect(self):
        self._connected = True
    
    def disconnect(self):
        self._connected = False
    
    def test_connection(self) -> bool:
        return self._connected


class TestBaseConnector:
    """Tests pour BaseConnector."""
    
    def test_init(self):
        """Test d'initialisation."""
        config = {"timeout": 30, "metrics_enabled": True}
        connector = MockConnector(config, "test_connector")
        
        assert connector.config == config
        assert connector.connector_name == "test_connector"
        assert not connector.is_connected
        assert connector.metrics is not None
    
    def test_context_manager(self):
        """Test du context manager."""
        config = {"timeout": 30}
        connector = MockConnector(config)
        
        with connector:
            assert connector.is_connected
        
        assert not connector.is_connected
    
    def test_connection_context_manager(self):
        """Test du context manager de connexion."""
        config = {"timeout": 30}
        connector = MockConnector(config)
        
        with connector.connection():
            assert connector.is_connected
        
        assert not connector.is_connected
    
    def test_metrics_disabled(self):
        """Test avec métriques désactivées."""
        config = {"metrics_enabled": False}
        connector = MockConnector(config)
        
        assert connector.metrics is None
        
        # Test execute_with_metrics sans métriques
        result = connector.execute_with_metrics("test", lambda: "result")
        assert result == "result"


class TestRegistry:
    """Tests pour le registre de connecteurs."""
    
    def test_register_connector(self):
        """Test d'enregistrement d'un connecteur."""
        registry.register("mock", MockConnector)
        assert "mock" in registry.list_connectors()
        
        # Nettoyage
        registry.unregister("mock")
    
    def test_create_connector(self):
        """Test de création d'un connecteur."""
        registry.register("mock", MockConnector)
        
        config = {"timeout": 30}
        connector = registry.create_connector("mock", config, "test_instance")
        
        assert isinstance(connector, MockConnector)
        assert connector.config == config
        
        # Test récupération d'instance
        same_connector = registry.get_instance("test_instance")
        assert same_connector is connector
        
        # Nettoyage
        registry.cleanup_instances()
        registry.unregister("mock")
    
    def test_unknown_connector(self):
        """Test avec un connecteur inconnu."""
        with pytest.raises(ConfigurationError):
            registry.get_connector_class("unknown")
        
        with pytest.raises(ConfigurationError):
            registry.create_connector("unknown", {})
    
    def test_invalid_connector_class(self):
        """Test avec une classe invalide."""
        class InvalidConnector:
            pass
        
        with pytest.raises(ConfigurationError):
            registry.register("invalid", InvalidConnector)


def test_create_connector_function():
    """Test de la fonction create_connector."""
    registry.register("mock", MockConnector)
    
    config = {"timeout": 30}
    connector = create_connector("mock", config)
    
    assert isinstance(connector, MockConnector)
    
    # Nettoyage
    registry.unregister("mock")
