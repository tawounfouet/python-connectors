"""
Test simple pour debug du module connectors.
"""


#import sys
#import os

# Ajouter le répertoire parent (racine du projet) au chemin Python
#current_dir = os.path.dirname(os.path.abspath(__file__))
#parent_dir = os.path.dirname(current_dir)
#sys.path.insert(0, parent_dir)


import logging
import os
from connectors import create_connector
from connectors.config.loader import load_config

# Charger les variables d'environnement depuis .env si disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger_dotenv = logging.getLogger(__name__)
    logger_dotenv.info("✅ .env file loaded")
except ImportError:
    pass  # dotenv n'est pas installé, pas grave

# Configuration du logging pour voir les détails
#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger(__name__)

from connectors import setup_logger

# Configuration du logger global
logger = setup_logger(
    name="debug_logger",
    log_dir="logs",
    log_file="debug_test.log",
    level=logging.DEBUG,
    console_output=True,
    rotate_logs=True,
    max_bytes=1024 * 1024,  # 1 MB
    backup_count=3
)


def test_postgresql_debug():
    """Test de debug pour PostgreSQL."""
    
    # Charger la configuration depuis le fichier INI
    try:
        config = load_config("postgresql")
        logger.info(f"✅ Configuration loaded from config.ini: {config}")
    except Exception as e:
        logger.error(f"Failed to load config from INI file: {e}")
        logger.warning("Falling back to .env configuration")
        
        # Fallback vers la configuration de .env
        if os.getenv("POSTGRESQL_HOST"):
            config = {
                "host": os.getenv("POSTGRESQL_HOST"),
                "port": int(os.getenv("POSTGRESQL_PORT", 5432)),
                "database": os.getenv("POSTGRESQL_DATABASE"),
                "username": os.getenv("POSTGRESQL_USERNAME"),
                "password": os.getenv("POSTGRESQL_PASSWORD"),
                "timeout": int(os.getenv("POSTGRESQL_TIMEOUT", 30)),
                "sslmode": os.getenv("POSTGRESQL_SSLMODE", "prefer"),
                "metrics_enabled": os.getenv("POSTGRESQL_METRICS_ENABLED", "false").lower() == "true"
            }
            logger.info("✅ Configuration loaded from .env file")
        else:
            # Configuration par défaut en derniers recours
            config = {
                "host": "ep-old-boat-a2gt5jte.eu-central-1.aws.neon.tech",
                "port": 5432,
                "database": "geoshop_db",
                "username": "geoshop_db_owner",
                "password": "JRdKeBf48tmu",
                "timeout": 5,
                "metrics_enabled": False,
                "sslmode": "require"
            }
            logger.warning("Using fallback hardcoded configuration")
    
    try:
        # Création du connecteur
        postgres = create_connector("postgresql", config)
        logger.info("✅ PostgreSQL connector created")
        
        # Test de connexion manuelle
        logger.info("Testing manual connection...")
        postgres.connect()
        logger.info(f"Connected: {postgres.is_connected}")
        logger.info(f"Cursor: {postgres.cursor}")
        
        if postgres.cursor:
            # Test simple sans metrics
            postgres.cursor.execute("SELECT 1 as test")
            #postgres.cursor.execute("SELECT * FROM students_student")

            result = postgres.cursor.fetchone()
            logger.info(f"Direct query result: {result}")
        
        postgres.disconnect()
        logger.info("✅ PostgreSQL test completed")
        
    except Exception as e:
        logger.error(f"PostgreSQL test failed: {e}")
        import traceback
        traceback.print_exc()


def test_mock_simple():
    """Test avec un connecteur mock très simple."""
    
    from connectors.base import BaseConnector
    from connectors.registry import register_connector
    
    @register_connector("simple_mock")
    class SimpleMockConnector(BaseConnector):
        def connect(self):
            self._connected = True
            print("SimpleMock: Connected!")
        
        def disconnect(self):
            self._connected = False
            print("SimpleMock: Disconnected!")
        
        def test_connection(self) -> bool:
            return self._connected
        
        def simple_operation(self):
            return "Simple operation result"
    
    config = {"metrics_enabled": False}
    
    try:
        mock = create_connector("simple_mock", config)
        logger.info("✅ Simple mock connector created")
        
        # Test manuel
        mock.connect()
        logger.info(f"Connected: {mock.is_connected}")
        
        result = mock.simple_operation()
        logger.info(f"Operation result: {result}")
        
        # Test avec métriques (même si désactivées)
        result2 = mock.execute_with_metrics("test_op", mock.simple_operation)
        logger.info(f"Metrics operation result: {result2}")
        
        mock.disconnect()
        logger.info("✅ Simple mock test completed")
        
    except Exception as e:
        logger.error(f"Simple mock test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logger.info("=== Debug Tests ===")
    
    #logger.info("\n--- Simple Mock Test ---")
    #test_mock_simple()
    
    logger.info("\n--- PostgreSQL Debug Test ---")
    test_postgresql_debug()
