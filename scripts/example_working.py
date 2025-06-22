"""
Exemple d'utilisation du module connectors avec configurations de test.
"""

import sys
import os

# Ajouter le répertoire parent (racine du projet) au chemin Python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


import logging
from connectors import create_connector, list_available_connectors

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def exemple_base_connector():
    """Exemple avec un connecteur mock."""
    from connectors.base import BaseConnector
    from connectors.registry import register_connector
    
    @register_connector("mock")
    class MockConnector(BaseConnector):
        """Connecteur mock pour démonstration."""
        
        def connect(self):
            logger.info("Mock: Connexion établie")
            self._connected = True
        
        def disconnect(self):
            logger.info("Mock: Connexion fermée")
            self._connected = False
        
        def test_connection(self) -> bool:
            return self._connected
        
        def operation_example(self, data):
            """Exemple d'opération avec métriques."""
            return f"Processed: {data}"
    
    # Configuration
    config = {
        "timeout": 30,
        "retry": {
            "max_attempts": 3,
            "backoff_factor": 2.0
        },
        "metrics_enabled": True
    }
    
    # Création du connecteur
    mock = create_connector("mock", config, "my_mock")
    
    # Utilisation avec context manager
    with mock.connection():
        # Test de connexion
        if mock.test_connection():
            logger.info("✅ Mock connector is working!")
            
            # Exemple d'opération avec métriques
            result = mock.execute_with_metrics(
                "example_operation",
                lambda: mock.operation_example("test data")
            )
            logger.info(f"Operation result: {result}")
        else:
            logger.error("❌ Mock connection failed!")
    
    # Afficher les métriques
    metrics = mock.get_metrics_summary()
    logger.info(f"Mock Metrics: {metrics}")


def exemple_postgresql_local():
    """Exemple PostgreSQL avec configuration locale (optionnel)."""
    
    # Configuration pour une base PostgreSQL locale
    config = {
        "host": "localhost",
        "port": 5432,
        "database": "postgres",  # Base par défaut
        "username": "postgres",
        "password": "password",
        "timeout": 5,
        "retry": {
            "max_attempts": 2,
            "backoff_factor": 1.5
        },
        "metrics_enabled": True
    }
    
    try:
        # Création du connecteur
        postgres = create_connector("postgresql", config, "test_postgres")
        
        # Test de connexion seulement
        logger.info("Tentative de connexion PostgreSQL...")
        with postgres.connection():
            if postgres.test_connection():
                logger.info("✅ PostgreSQL connection successful!")
                
                # Exemple simple de requête
                result = postgres.fetch_one("SELECT version() as version")
                if result:
                    logger.info(f"PostgreSQL version: {result.get('version', 'Unknown')[:50]}...")
            else:
                logger.error("❌ PostgreSQL connection test failed!")
        
        # Afficher les métriques
        metrics = postgres.get_metrics_summary()
        logger.info(f"PostgreSQL Metrics: {metrics}")
        
    except Exception as e:
        logger.warning(f"PostgreSQL example skipped (no local DB?): {e}")


def exemple_configurations():
    """Exemples de différentes configurations."""
    
    # Configuration avec retry agressif
    config_retry = {
        "timeout": 10,
        "retry": {
            "max_attempts": 5,
            "backoff_factor": 3.0,
            "initial_delay": 0.5,
            "max_delay": 30.0
        },
        "metrics_enabled": True,
        "log_level": "DEBUG"
    }
    
    # Configuration sans métriques
    config_no_metrics = {
        "timeout": 15,
        "metrics_enabled": False,
        "log_level": "WARNING"
    }
    
    logger.info("=== Configuration avec retry agressif ===")
    from connectors.base import BaseConnector
    from connectors.registry import register_connector
    
    @register_connector("config_test")
    class ConfigTestConnector(BaseConnector):
        def connect(self):
            self._connected = True
        def disconnect(self):
            self._connected = False
        def test_connection(self) -> bool:
            return True
    
    # Test avec métriques
    test1 = create_connector("config_test", config_retry, "test_with_metrics")
    with test1.connection():
        result = test1.execute_with_metrics("test_op", lambda: "success")
        logger.info(f"Result with metrics: {result}")
    
    # Test sans métriques
    test2 = create_connector("config_test", config_no_metrics, "test_no_metrics")
    with test2.connection():
        result = test2.execute_with_metrics("test_op", lambda: "success")
        logger.info(f"Result without metrics: {result}")
    
    # Comparaison des métriques
    logger.info(f"Metrics enabled: {test1.get_metrics_summary()}")
    logger.info(f"Metrics disabled: {test2.get_metrics_summary()}")


def main():
    """Fonction principale d'exemple."""
    
    # Lister les connecteurs disponibles
    connectors = list_available_connectors()
    logger.info(f"Available connectors: {connectors}")
    
    # Exemples fonctionnels
    logger.info("\n=== Mock Connector Example ===")
    try:
        exemple_base_connector()
    except Exception as e:
        logger.error(f"Mock example failed: {e}")
    
    logger.info("\n=== Configuration Examples ===")
    try:
        exemple_configurations()
    except Exception as e:
        logger.error(f"Configuration examples failed: {e}")
    
    logger.info("\n=== PostgreSQL Local Test (optional) ===")
    try:
        exemple_postgresql_local()
    except Exception as e:
        logger.warning(f"PostgreSQL example skipped: {e}")
    
    logger.info("\n=== Module test completed! ===")


if __name__ == "__main__":
    main()
