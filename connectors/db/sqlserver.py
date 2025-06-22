"""
Connecteur SQL Server.
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


@register_connector("sqlserver")
class SQLServerConnector(DatabaseConnector):
    """Connecteur pour SQL Server."""
    
    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        super().__init__(config, connector_name)
        
        # Validation de la configuration
        try:
            self.db_config = DatabaseConfig(**config)
        except Exception as e:
            raise ConfigurationError(f"Invalid SQL Server configuration: {e}")
        
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Établit la connexion à SQL Server."""
        try:
            import pyodbc
        except ImportError:
            raise ConfigurationError("pyodbc is required for SQL Server connector. Install with: pip install pyodbc")
        
        try:
            if self.db_config.connection_string:
                connection_string = self.db_config.connection_string
            else:
                # Construction de la chaîne de connexion
                connection_string = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.db_config.host},{self.db_config.port or 1433};"
                    f"DATABASE={self.db_config.database};"
                    f"UID={self.db_config.username};"
                    f"PWD={self.db_config.password};"
                    f"TIMEOUT={self.db_config.timeout};"
                )
                
                if self.db_config.ssl_enabled:
                    connection_string += "Encrypt=yes;TrustServerCertificate=no;"
                else:
                    connection_string += "Encrypt=no;"
            
            self.connection = pyodbc.connect(connection_string)
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
            
            logger.info(f"Connected to SQL Server: {self.db_config.host}:{self.db_config.port or 1433}/{self.db_config.database}")
            self._connected = True
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SQL Server: {e}")
    
    def disconnect(self):
        """Ferme la connexion SQL Server."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            
            self.cursor = None
            self.connection = None
            self._connected = False
            
            logger.info("Disconnected from SQL Server")
            
        except Exception as e:
            logger.error(f"Error disconnecting from SQL Server: {e}")
    
    def test_connection(self) -> bool:
        """Teste la connexion SQL Server."""
        try:
            if not self._connected:
                self.connect()
            
            # Test simple avec une requête
            self.cursor.execute("SELECT 1 as test")
            result = self.cursor.fetchone()
            
            return result is not None and result[0] == 1
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête SQL."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _execute():
            if params:
                # Convertir les paramètres nommés en paramètres positionnels pour pyodbc
                param_values = list(params.values())
                # Remplacer les placeholders nommés par des ?
                formatted_query = query
                for key in params.keys():
                    formatted_query = formatted_query.replace(f"%({key})s", "?")
                    formatted_query = formatted_query.replace(f":{key}", "?")
                self.cursor.execute(formatted_query, param_values)
            else:
                self.cursor.execute(query)
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
            
            # Remplacer les placeholders nommés par des ?
            formatted_query = query
            if params_list and isinstance(params_list[0], dict):
                for key in params_list[0].keys():
                    formatted_query = formatted_query.replace(f"%({key})s", "?")
                    formatted_query = formatted_query.replace(f":{key}", "?")
            
            self.cursor.executemany(formatted_query, param_tuples)
            return self.cursor.rowcount
        
        return self.execute_with_metrics("execute_many", _execute_many)
    
    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête et retourne un seul résultat."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _fetch_one():
            if params:
                param_values = list(params.values())
                formatted_query = query
                for key in params.keys():
                    formatted_query = formatted_query.replace(f"%({key})s", "?")
                    formatted_query = formatted_query.replace(f":{key}", "?")
                self.cursor.execute(formatted_query, param_values)
            else:
                self.cursor.execute(query)
            
            row = self.cursor.fetchone()
            if row:
                # Convertir en dictionnaire avec les noms de colonnes
                columns = [column[0] for column in self.cursor.description]
                return dict(zip(columns, row))
            return None
        
        return self.execute_with_metrics("fetch_one", _fetch_one)
    
    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une requête et retourne tous les résultats."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        def _fetch_all():
            if params:
                param_values = list(params.values())
                formatted_query = query
                for key in params.keys():
                    formatted_query = formatted_query.replace(f"%({key})s", "?")
                    formatted_query = formatted_query.replace(f":{key}", "?")
                self.cursor.execute(formatted_query, param_values)
            else:
                self.cursor.execute(query)
            
            rows = self.cursor.fetchall()
            if rows:
                # Convertir en liste de dictionnaires avec les noms de colonnes
                columns = [column[0] for column in self.cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        
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
        columns_def = ", ".join([f"[{col}] {col_type}" for col, col_type in columns.items()])
        query = f"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U') CREATE TABLE [{table_name}] ({columns_def})"
        return self.execute_query(query)
    
    def insert_data(self, table_name: str, data: Dict[str, Any]):
        """Insert des données dans une table."""
        columns = ", ".join([f"[{col}]" for col in data.keys()])
        placeholders = ", ".join(["?" for _ in data.keys()])
        query = f"INSERT INTO [{table_name}] ({columns}) VALUES ({placeholders})"
        # Convertir le dictionnaire en liste pour SQL Server
        param_values = list(data.values())
        self.cursor.execute(query, param_values)
        return self.cursor.rowcount
    
    def get_table_info(self, table_name: str):
        """Retourne les informations d'une table."""
        query = """
        SELECT 
            COLUMN_NAME as column_name,
            DATA_TYPE as data_type,
            IS_NULLABLE as is_nullable,
            COLUMN_DEFAULT as column_default
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        return self.fetch_all(query, {"table_name": table_name})
    
    def show_tables(self):
        """Retourne la liste des tables."""
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        results = self.fetch_all(query)
        return [row['TABLE_NAME'] for row in results]
