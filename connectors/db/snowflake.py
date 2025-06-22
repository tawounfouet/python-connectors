"""
Connecteur Snowflake.
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

try:
    from connectors.base import DatabaseConnector
    from connectors.registry import register_connector
    from connectors.exceptions import ConnectionError, ConfigurationError
    from connectors.config import SnowflakeConfig
except ImportError:
    # Import relatif si l'import absolu échoue
    from ..base import DatabaseConnector
    from ..registry import register_connector
    from ..exceptions import ConnectionError, ConfigurationError
    from ..config import SnowflakeConfig

logger = logging.getLogger(__name__)


@register_connector("snowflake")
class SnowflakeConnector(DatabaseConnector):
    """Connecteur pour Snowflake."""
    
    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        super().__init__(config, connector_name)
        
        # Validation de la configuration
        try:
            self.snowflake_config = SnowflakeConfig(**config)
        except Exception as e:
            raise ConfigurationError(f"Invalid Snowflake configuration: {e}")
        
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Établit la connexion à Snowflake."""
        try:
            import snowflake.connector
            from snowflake.connector import DictCursor
        except ImportError:
            raise ConfigurationError("snowflake-connector-python is required for Snowflake connector. Install with: pip install snowflake-connector-python")
        
        try:
            connection_params = self.snowflake_config.get_connection_params()
            
            # Ajouter les paramètres de timeout
            connection_params.update({
                'login_timeout': self.snowflake_config.timeout or 30,
                'network_timeout': (self.snowflake_config.timeout or 30) * 2,
            })
            
            # Options SSL/TLS
            if getattr(self.snowflake_config, 'ssl_enabled', True):
                connection_params['insecure_mode'] = False
            
            self.connection = snowflake.connector.connect(**connection_params)
            self.cursor = self.connection.cursor(DictCursor)
            
            logger.info(f"Connected to Snowflake: {self.snowflake_config.account}/{self.snowflake_config.database}/{self.snowflake_config.schema_name}")
            self._connected = True
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Snowflake: {e}")
    
    def disconnect(self):
        """Ferme la connexion Snowflake."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            
            self.cursor = None
            self.connection = None
            self._connected = False
            
            logger.info("Disconnected from Snowflake")
            
        except Exception as e:
            logger.error(f"Error disconnecting from Snowflake: {e}")
    
    def test_connection(self) -> bool:
        """Teste la connexion Snowflake."""
        try:
            if not self._connected:
                self.connect()
            
            # Test simple avec une requête
            self.cursor.execute("SELECT 1 as test")
            result = self.cursor.fetchone()
            
            return result is not None and result['TEST'] == 1
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête SQL."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _execute():
            if params:
                # Snowflake utilise des paramètres nommés avec %(name)s
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.rowcount
        
        return self.execute_with_metrics("execute_query", _execute)
    
    def execute_many(self, query: str, params_list: List[Dict[str, Any]]):
        """Exécute une requête avec plusieurs jeux de paramètres."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _execute_many():
            self.cursor.executemany(query, params_list)
            return self.cursor.rowcount
        
        return self.execute_with_metrics("execute_many", _execute_many)
    
    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête et retourne un seul résultat."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _fetch_one():
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        
        return self.execute_with_metrics("fetch_one", _fetch_one)
    
    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête et retourne tous les résultats."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _fetch_all():
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        
        return self.execute_with_metrics("fetch_all", _fetch_all)
    
    @contextmanager
    def transaction(self):
        """Context manager pour les transactions."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        try:
            self.cursor.execute("BEGIN TRANSACTION")
            yield self
            self.cursor.execute("COMMIT")
        except Exception as e:
            self.cursor.execute("ROLLBACK")
            logger.error(f"Transaction rolled back: {e}")
            raise
    
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
        WHERE table_name = %(table_name)s 
        AND table_schema = %(schema)s
        ORDER BY ordinal_position
        """
        return self.fetch_all(query, {"table_name": table_name.upper(), "schema": self.snowflake_config.schema_name.upper()})
    
    def show_tables(self):
        """Retourne la liste des tables."""
        query = f"SHOW TABLES IN SCHEMA {self.snowflake_config.schema_name}"
        results = self.fetch_all(query)
        return [row['name'] for row in results]
    
    def use_warehouse(self, warehouse: str):
        """Change le warehouse actuel."""
        query = f"USE WAREHOUSE {warehouse}"
        self.execute_query(query)
        # Mettre à jour la configuration
        self.snowflake_config.warehouse = warehouse
        logger.info(f"Switched to warehouse: {warehouse}")
    
    def use_database(self, database: str):
        """Change la base de données actuelle."""
        query = f"USE DATABASE {database}"
        self.execute_query(query)
        # Mettre à jour la configuration
        self.snowflake_config.database = database
        logger.info(f"Switched to database: {database}")
    
    def use_schema(self, schema: str):
        """Change le schéma actuel."""
        query = f"USE SCHEMA {schema}"
        self.execute_query(query)
        # Mettre à jour la configuration
        self.snowflake_config.schema_name = schema
        logger.info(f"Switched to schema: {schema}")
    
    def get_warehouses(self):
        """Retourne la liste des warehouses disponibles."""
        query = "SHOW WAREHOUSES"
        results = self.fetch_all(query)
        return [row['name'] for row in results]
    
    def get_databases(self):
        """Retourne la liste des bases de données disponibles."""
        query = "SHOW DATABASES"
        results = self.fetch_all(query)
        return [row['name'] for row in results]
    
    def get_schemas(self, database: Optional[str] = None):
        """Retourne la liste des schémas disponibles."""
        if database:
            query = f"SHOW SCHEMAS IN DATABASE {database}"
        else:
            query = "SHOW SCHEMAS"
        results = self.fetch_all(query)
        return [row['name'] for row in results]
