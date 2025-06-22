"""
Configuration globale du logging pour les connecteurs.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration par défaut
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_DIR = 'logs'
DEFAULT_LOG_FILE = 'connectors.log'


def setup_logger(
    name: Optional[str] = None,
    level: Optional[int] = None,
    log_format: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    rotate_logs: bool = True,
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 5,
    console_output: bool = True,
    config: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """
    Configure un logger avec une configuration standard.
    
    Args:
        name: Nom du logger (par défaut: 'connectors')
        level: Niveau de logging (par défaut: INFO)
        log_format: Format du log (par défaut: voir DEFAULT_LOG_FORMAT)
        log_dir: Répertoire des logs (par défaut: 'logs')
        log_file: Nom du fichier de log (par défaut: 'connectors.log')
        rotate_logs: Activer la rotation des logs (par défaut: True)
        max_bytes: Taille maximale du fichier avant rotation (par défaut: 10 MB)
        backup_count: Nombre de fichiers de backup (par défaut: 5)
        console_output: Activer la sortie console (par défaut: True)
        config: Configuration optionnelle en tant que dictionnaire
        
    Returns:
        Logger configuré
    """
    # Utiliser la configuration si fournie
    if config:
        level = get_level_from_config(config.get('log_level')) if config.get('log_level') else level
        log_dir = config.get('log_dir', log_dir)
        log_file = config.get('log_file', log_file)
        rotate_logs = config.get('rotate_logs', rotate_logs)
        max_bytes = config.get('max_bytes', max_bytes)
        backup_count = config.get('backup_count', backup_count)
        console_output = config.get('console_output', console_output)
    
    # Valeurs par défaut
    name = name or 'connectors'
    level = level or DEFAULT_LOG_LEVEL
    log_format = log_format or DEFAULT_LOG_FORMAT
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_file = log_file or DEFAULT_LOG_FILE
    
    # Créer le logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Nettoyer les handlers existants
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    formatter = logging.Formatter(log_format)
    
    # Créer le répertoire de logs s'il n'existe pas
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_path = os.path.join(log_dir, log_file)
    
    # Configurer le handler de fichier
    if rotate_logs:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
    else:
        file_handler = logging.FileHandler(log_path)
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Ajouter un handler pour la console si demandé
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_level_from_config(level_str: str) -> int:
    """
    Convertit une chaîne de niveau de log en constante logging.
    
    Args:
        level_str: Chaîne de niveau (DEBUG, INFO, etc.)
        
    Returns:
        Constante de niveau logging correspondante
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    return level_map.get(level_str.upper(), DEFAULT_LOG_LEVEL)


# Logger global pour le module connectors
global_logger = setup_logger()
