"""
Connecteur MySQL.
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

try:
    from connectors.base import DatabaseConnector
    from connectors.registry import register_connector
    from connectors.exceptions import ConnectionError, ConfigurationError
    from connectors.config import DatabaseConfig
except ImportError:
    # Import relatif si l'import absolu échoue
    from ..base import DatabaseConnector
    from ..registry import register_connector
    from ..exceptions import ConnectionError, ConfigurationError
    from ..config import DatabaseConfig

logger = logging.getLogger(__name__)


@register_connector("mysql")
class MySQLConnector(DatabaseConnector):
    """Connecteur pour MySQL."""
    
    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        super().__init__(config, connector_name)
        
        # Validation de la configuration
        try:
            self.db_config = DatabaseConfig(**config)
        except Exception as e:
            raise ConfigurationError(f"Invalid MySQL configuration: {e}")
        
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Établit la connexion à MySQL."""
        try:
            import mysql.connector
            from mysql.connector import Error
        except ImportError:
            raise ConfigurationError("mysql-connector-python is required for MySQL connector. Install with: pip install mysql-connector-python")
        
        try:
            if self.db_config.connection_string:
                # Parse connection string si fournie
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(self.db_config.connection_string)
                connection_params = {
                    'host': parsed.hostname,
                    'port': parsed.port or 3306,
                    'database': parsed.path.lstrip('/'),
                    'user': parsed.username,
                    'password': parsed.password,
                }
            else:
                connection_params = {
                    'host': self.db_config.host,
                    'port': self.db_config.port or 3306,
                    'database': self.db_config.database,
                    'user': self.db_config.username,
                    'password': self.db_config.password,
                    'connection_timeout': self.db_config.timeout,
                    'autocommit': True,
                }
                
                if self.db_config.ssl_enabled:
                    connection_params['ssl_verify_cert'] = True
                    connection_params['ssl_verify_identity'] = True
            
            self.connection = mysql.connector.connect(**connection_params)
            self.cursor = self.connection.cursor(dictionary=True)
            
            logger.info(f"Connected to MySQL: {self.db_config.host}:{self.db_config.port or 3306}/{self.db_config.database}")
            self._connected = True
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MySQL: {e}")
    
    def disconnect(self):
        """Ferme la connexion MySQL."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            
            self.cursor = None
            self.connection = None
            self._connected = False
            
            logger.info("Disconnected from MySQL")
            
        except Exception as e:
            logger.error(f"Error disconnecting from MySQL: {e}")
    
    def test_connection(self) -> bool:
        """Teste la connexion MySQL."""
        try:
            if not self._connected:
                self.connect()
            
            # Test simple avec une requête
            self.cursor.execute("SELECT 1 as test")
            result = self.cursor.fetchone()
            
            return result is not None and result['test'] == 1
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête SQL."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _execute():
            self.cursor.execute(query, params)
            return self.cursor.rowcount
        
        return self.execute_with_metrics("execute_query", _execute)
    
    def execute_many(self, query: str, params_list: List[Dict[str, Any]]):
        """Exécute une requête avec plusieurs jeux de paramètres."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _execute_many():
            # Convertir les dictionnaires en tuples pour executemany
            param_tuples = [tuple(params.values()) if isinstance(params, dict) else params 
                           for params in params_list]
            self.cursor.executemany(query, param_tuples)
            return self.cursor.rowcount
        
        return self.execute_with_metrics("execute_many", _execute_many)
    
    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête et retourne un seul résultat."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _fetch_one():
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        
        return self.execute_with_metrics("fetch_one", _fetch_one)
    
    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête et retourne tous les résultats."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _fetch_all():
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        
        return self.execute_with_metrics("fetch_all", _fetch_all)
    
    @contextmanager
    def transaction(self):
        """Context manager pour les transactions."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        # Désactiver l'autocommit pour la transaction
        old_autocommit = self.connection.autocommit
        self.connection.autocommit = False
        
        try:
            yield self
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            self.connection.autocommit = old_autocommit
    
    def create_table(self, table_name: str, columns: Dict[str, str]):
        """Crée une table."""
        columns_def = ", ".join([f"{col} {col_type}" for col, col_type in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})"
        return self.execute_query(query)
    
    def insert_data(self, table_name: str, data: Dict[str, Any]):
        """Insert des données dans une table."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"%({key})s" for key in data.keys()])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.execute_query(query, data)
    
    def get_table_info(self, table_name: str):
        """Retourne les informations d'une table."""
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = %(table_name)s AND table_schema = DATABASE()
        ORDER BY ordinal_position
        """
        return self.fetch_all(query, {"table_name": table_name})
    
    def show_tables(self):
        """Retourne la liste des tables."""
        query = "SHOW TABLES"
        results = self.fetch_all(query)
        # MySQL retourne un dictionnaire avec une clé variable, on extrait les valeurs
        return [list(row.values())[0] for row in results]
