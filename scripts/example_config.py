"""
Exemple d'utilisation des configurations depuis le fichier INI.
"""

import logging
from connectors import create_connector
from connectors.config.loader import load_config, config_loader

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_all_configured_connectors():
    """Test tous les connecteurs configurés dans le fichier INI."""
    
    # Lister toutes les configurations disponibles
    available_configs = config_loader.get_section_names()
    logger.info(f"Configurations disponibles: {available_configs}")
    
    for connector_type in available_configs:
        try:
            logger.info(f"\n--- Test de {connector_type.upper()} ---")
            
            # Charger la configuration
            config = load_config(connector_type)
            logger.info(f"Configuration chargée: {config}")
            
            # Créer le connecteur (ne pas se connecter pour éviter les erreurs de connexion)
            connector = create_connector(connector_type, config)
            logger.info(f"✅ Connecteur {connector_type} créé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur avec {connector_type}: {e}")


def test_specific_connector(connector_type: str):
    """Test un connecteur spécifique."""
    try:
        logger.info(f"\n--- Test spécifique de {connector_type.upper()} ---")
        
        # Vérifier si la configuration existe
        if not config_loader.has_section(connector_type):
            logger.error(f"Configuration '{connector_type}' non trouvée")
            return
        
        # Charger et afficher la configuration
        config = load_config(connector_type)
        logger.info(f"Configuration: {config}")
        
        # Créer le connecteur
        connector = create_connector(connector_type, config)
        logger.info(f"✅ Connecteur {connector_type} créé")
        
        # Test de base (sans connexion réelle)
        logger.info(f"Connecté: {connector.is_connected}")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_postgresql_with_connection():
    """Test PostgreSQL avec connexion réelle."""
    try:
        logger.info("\n--- Test PostgreSQL avec connexion ---")
        
        config = load_config("postgresql")
        postgres = create_connector("postgresql", config)
        
        # Tentative de connexion
        postgres.connect()
        logger.info(f"✅ Connexion PostgreSQL établie: {postgres.is_connected}")
        
        if postgres.is_connected and postgres.cursor:
            # Test simple
            postgres.cursor.execute("SELECT 1 as test, 'Hello from config!' as message")
            result = postgres.cursor.fetchone()
            logger.info(f"Résultat de la requête: {result}")
        
        postgres.disconnect()
        logger.info("✅ Déconnexion PostgreSQL")
        
    except Exception as e:
        logger.error(f"❌ Erreur PostgreSQL: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logger.info("=== Test des configurations INI ===")
    
    # Test de tous les connecteurs configurés
    test_all_configured_connectors()
    
    # Test spécifique de PostgreSQL
    test_specific_connector("postgresql")
    
    # Test avec connexion réelle (PostgreSQL)
    test_postgresql_with_connection()
