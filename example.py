"""
Exemple d'utilisation du module connectors.
"""

import logging
from connectors import create_connector, list_available_connectors

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def exemple_postgresql():
    """Exemple d'utilisation du connecteur PostgreSQL."""
    
    config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "username": "user",
        "password": "password",
        "timeout": 30,
        "retry": {
            "max_attempts": 3,
            "backoff_factor": 2.0
        },
        "metrics_enabled": True
    }
    
    # Création du connecteur
    postgres = create_connector("postgresql", config, "my_postgres")
    
    # Utilisation avec context manager
    with postgres.connection():
        # Créer une table d'exemple
        postgres.create_table("users", {
            "id": "SERIAL PRIMARY KEY",
            "name": "VARCHAR(100)",
            "email": "VARCHAR(100) UNIQUE"
        })
        
        # Insérer des données
        postgres.insert_data("users", {
            "name": "John Doe",
            "email": "john@example.com"
        })
        
        # Requête des données
        users = postgres.fetch_all("SELECT * FROM users")
        logger.info(f"Users found: {users}")
        
        # Informations sur la table
        table_info = postgres.get_table_info("users")
        logger.info(f"Table structure: {table_info}")
    
    # Afficher les métriques
    metrics = postgres.get_metrics_summary()
    logger.info(f"Metrics: {metrics}")


def exemple_s3():
    """Exemple d'utilisation du connecteur S3."""
    
    config = {
        "access_key_id": "your_access_key",
        "secret_access_key": "your_secret_key",
        "bucket_name": "your-bucket",
        "region": "us-east-1",
        "timeout": 30,
        "metrics_enabled": True
    }
    
    # Création du connecteur
    s3 = create_connector("s3", config, "my_s3")
    
    # Utilisation avec context manager
    with s3.connection():
        # Test de connexion
        if s3.test_connection():
            logger.info("S3 connection successful!")
            
            # Lister les fichiers
            files = s3.list_files(prefix="documents/")
            logger.info(f"Files found: {len(files)}")
            
            # Upload d'un fichier (exemple)
            # s3.upload_file("local_file.txt", "remote_file.txt")
            
            # Créer une URL pré-signée
            # url = s3.create_presigned_url("remote_file.txt", expiration=3600)
            # logger.info(f"Presigned URL: {url}")
        else:
            logger.error("S3 connection failed!")
    
    # Afficher les métriques
    metrics = s3.get_metrics_summary()
    logger.info(f"S3 Metrics: {metrics}")


def main():
    """Fonction principale d'exemple."""
    
    # Lister les connecteurs disponibles
    connectors = list_available_connectors()
    logger.info(f"Available connectors: {connectors}")
    
    # Exemples d'utilisation
    logger.info("=== PostgreSQL Example ===")
    try:
        exemple_postgresql()
    except Exception as e:
        logger.error(f"PostgreSQL example failed: {e}")
    
    logger.info("=== S3 Example ===")
    try:
        exemple_s3()
    except Exception as e:
        logger.error(f"S3 example failed: {e}")


if __name__ == "__main__":
    main()
