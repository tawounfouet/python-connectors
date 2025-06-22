"""
Exemple d'utilisation du système de logging des connecteurs.
"""


import sys
import os

# Ajouter le répertoire parent (racine du projet) au chemin Python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


import logging
from connectors import create_connector, setup_logger

# Configuration du logger global
logger = setup_logger(
    name="example_app",
    log_dir="logs",
    log_file="example_app.log",
    level=logging.DEBUG,
    console_output=True,
    rotate_logs=True,
    max_bytes=1024 * 1024,  # 1 MB
    backup_count=3
)

# Configuration d'un connecteur avec options de logging personnalisées
postgres_config = {
    "host": "localhost",
    "port": 5432,
    "database": "test",
    "username": "postgres",
    "password": "password",
    "logging": {
        "log_level": "DEBUG",
        "log_dir": "logs",
        "log_file": "postgres_connector.log",
        "rotate_logs": True,
        "max_bytes": 5 * 1024 * 1024,  # 5 MB
        "backup_count": 5,
        "console_output": False  # Logs uniquement dans le fichier
    }
}

# Démonstration d'utilisation du logger
def main():
    logger.info("Démarrage de l'exemple de logging")
    
    try:
        # Créer un connecteur (sachant que dans cet exemple, il ne pourra pas vraiment se connecter)
        logger.debug("Création d'un connecteur PostgreSQL test")
        
        # La ligne ci-dessous échouerait en pratique car on n'a pas de serveur PostgreSQL réel
        # mais c'est juste pour montrer comment les logs seraient gérés
        # postgres = create_connector("postgresql", postgres_config, "demo_postgres")
        
        # Simuler une erreur
        logger.warning("Simulation d'une erreur de connexion")
        raise ConnectionError("Impossible de se connecter à la base de données")
        
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {e}", exc_info=True)
    
    logger.info("Fin de l'exemple de logging")
    
    # Afficher où se trouvent les logs
    log_path = os.path.abspath("logs")
    print(f"\nLes logs ont été écrits dans: {log_path}")
    print("Fichiers de logs:")
    for file in sorted(os.listdir("logs")):
        file_size = os.path.getsize(os.path.join("logs", file)) / 1024  # KB
        print(f"  - {file} ({file_size:.1f} KB)")


if __name__ == "__main__":
    # Créer le dossier logs s'il n'existe pas
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    main()
