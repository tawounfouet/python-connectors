"""
Connecteur Amazon S3.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    from connectors.base import FileSystemConnector
    from connectors.registry import register_connector
    from connectors.exceptions import ConnectionError, ConfigurationError
    from connectors.config import S3Config
except ImportError:
    # Import relatif si l'import absolu échoue
    from ..base import FileSystemConnector
    from ..registry import register_connector
    from ..exceptions import ConnectionError, ConfigurationError
    from ..config import S3Config

logger = logging.getLogger(__name__)


@register_connector("s3")
class S3Connector(FileSystemConnector):
    """Connecteur pour Amazon S3."""
    
    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        super().__init__(config, connector_name)
        
        # Validation de la configuration
        try:
            self.s3_config = S3Config(**config)
        except Exception as e:
            raise ConfigurationError(f"Invalid S3 configuration: {e}")
        
        self.s3_client = None
        self.s3_resource = None
    
    def connect(self):
        """Établit la connexion à S3."""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
        except ImportError:
            raise ConfigurationError("boto3 is required for S3 connector. Install with: pip install boto3")
        
        try:
            session_config = {
                'aws_access_key_id': self.s3_config.access_key_id,
                'aws_secret_access_key': self.s3_config.secret_access_key,
                'region_name': self.s3_config.region
            }
            
            if self.s3_config.endpoint_url:
                session_config['endpoint_url'] = self.s3_config.endpoint_url
            
            self.s3_client = boto3.client('s3', **session_config)
            self.s3_resource = boto3.resource('s3', **session_config)
            
            logger.info(f"Connected to S3: {self.s3_config.bucket_name} in {self.s3_config.region}")
            self._connected = True
            
        except (ClientError, NoCredentialsError) as e:
            raise ConnectionError(f"Failed to connect to S3: {e}")
    
    def disconnect(self):
        """Ferme la connexion S3."""
        # boto3 ne nécessite pas de fermeture explicite
        self.s3_client = None
        self.s3_resource = None
        self._connected = False
        logger.info("Disconnected from S3")
    
    def test_connection(self) -> bool:
        """Teste la connexion S3."""
        try:
            if not self._connected:
                self.connect()
            
            # Test avec head_bucket
            self.s3_client.head_bucket(Bucket=self.s3_config.bucket_name)
            return True
            
        except Exception as e:
            logger.error(f"S3 connection test failed: {e}")
            return False
    
    def upload_file(self, local_path: str, remote_path: str, **kwargs):
        """Upload un fichier vers S3."""
        if not self._connected:
            raise ConnectionError("Not connected to S3")
        
        def _upload():
            extra_args = kwargs.get('extra_args', {})
            self.s3_client.upload_file(
                local_path, 
                self.s3_config.bucket_name, 
                remote_path,
                ExtraArgs=extra_args
            )
            return f"s3://{self.s3_config.bucket_name}/{remote_path}"
        
        return self.execute_with_metrics("upload_file", _upload)
    
    def download_file(self, remote_path: str, local_path: str):
        """Download un fichier depuis S3."""
        if not self._connected:
            raise ConnectionError("Not connected to S3")
        
        def _download():
            # Créer le répertoire local si nécessaire
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(
                self.s3_config.bucket_name,
                remote_path,
                local_path
            )
            return local_path
        
        return self.execute_with_metrics("download_file", _download)
    
    def list_files(self, prefix: str = "", max_keys: int = 1000) -> List[Dict[str, Any]]:
        """Liste les fichiers dans S3."""
        if not self._connected:
            raise ConnectionError("Not connected to S3")
        
        def _list_files():
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_config.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return files
        
        return self.execute_with_metrics("list_files", _list_files)
    
    def delete_file(self, remote_path: str):
        """Supprime un fichier dans S3."""
        if not self._connected:
            raise ConnectionError("Not connected to S3")
        
        def _delete():
            self.s3_client.delete_object(
                Bucket=self.s3_config.bucket_name,
                Key=remote_path
            )
            return f"Deleted s3://{self.s3_config.bucket_name}/{remote_path}"
        
        return self.execute_with_metrics("delete_file", _delete)
    
    def file_exists(self, remote_path: str) -> bool:
        """Vérifie si un fichier existe dans S3."""
        if not self._connected:
            raise ConnectionError("Not connected to S3")
        
        try:
            self.s3_client.head_object(
                Bucket=self.s3_config.bucket_name,
                Key=remote_path
            )
            return True
        except Exception:
            return False
    
    def get_file_info(self, remote_path: str) -> Dict[str, Any]:
        """Retourne les informations d'un fichier S3."""
        if not self._connected:
            raise ConnectionError("Not connected to S3")
        
        def _get_info():
            response = self.s3_client.head_object(
                Bucket=self.s3_config.bucket_name,
                Key=remote_path
            )
            
            return {
                'size': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
        
        return self.execute_with_metrics("get_file_info", _get_info)
    
    def upload_folder(self, local_folder: str, remote_prefix: str = ""):
        """Upload un dossier complet vers S3."""
        if not self._connected:
            raise ConnectionError("Not connected to S3")
        
        local_path = Path(local_folder)
        if not local_path.exists():
            raise FileNotFoundError(f"Local folder not found: {local_folder}")
        
        uploaded_files = []
        
        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_path)
                remote_path = f"{remote_prefix}/{relative_path}".lstrip("/")
                
                self.upload_file(str(file_path), remote_path)
                uploaded_files.append(remote_path)
        
        logger.info(f"Uploaded {len(uploaded_files)} files from {local_folder}")
        return uploaded_files
    
    def create_presigned_url(self, remote_path: str, expiration: int = 3600) -> str:
        """Crée une URL pré-signée pour un fichier S3."""
        if not self._connected:
            raise ConnectionError("Not connected to S3")
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.s3_config.bucket_name,
                    'Key': remote_path
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            raise ConnectionError(f"Failed to create presigned URL: {e}")
