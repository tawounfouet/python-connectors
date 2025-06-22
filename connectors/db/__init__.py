"""
Connecteurs de bases de données.
"""

# Import automatique des connecteurs disponibles
__all__ = []

try:
    from .postgresql import PostgreSQLConnector
    __all__.append('PostgreSQLConnector')
except ImportError:
    pass

try:
    from .mysql import MySQLConnector
    __all__.append('MySQLConnector')
except ImportError:
    pass

try:
    from .sqlserver import SQLServerConnector
    __all__.append('SQLServerConnector')
except ImportError:
    pass

try:
    from .snowflake import SnowflakeConnector
    __all__.append('SnowflakeConnector')
except ImportError:
    pass
