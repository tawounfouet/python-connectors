"""
Connecteurs pour data lakes et stockage cloud.
"""

# Import automatique des connecteurs disponibles
__all__ = []

try:
    from .s3 import S3Connector
    __all__.append('S3Connector')
except ImportError:
    pass

# TODO: Ajouter d'autres connecteurs (Azure Blob, GCS, etc.)
