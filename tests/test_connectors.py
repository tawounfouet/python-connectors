"""
Tests pour les connecteurs spécifiques.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from connectors.exceptions import ConfigurationError, ConnectionError


class TestPostgreSQLConnector:
    """Tests pour PostgreSQLConnector."""
    
    @patch('connectors.db.postgresql.psycopg2')
    def test_postgresql_connection(self, mock_psycopg2):
        """Test de connexion PostgreSQL."""
        from connectors.db.postgresql import PostgreSQLConnector
        
        # Mock de la connexion
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        config = {
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "user",
            "password": "password"
        }
        
        connector = PostgreSQLConnector(config)
        connector.connect()
        
        assert connector.is_connected
        mock_psycopg2.connect.assert_called_once()
    
    def test_postgresql_invalid_config(self):
        """Test avec configuration PostgreSQL invalide."""
        from connectors.db.postgresql import PostgreSQLConnector
        
        invalid_config = {"host": "localhost"}  # Config incomplète
        
        with pytest.raises(ConfigurationError):
            PostgreSQLConnector(invalid_config)


class TestS3Connector:
    """Tests pour S3Connector."""
    
    @patch('connectors.data_lake.s3.boto3')
    def test_s3_connection(self, mock_boto3):
        """Test de connexion S3."""
        from connectors.data_lake.s3 import S3Connector
        
        # Mock des clients boto3
        mock_client = Mock()
        mock_resource = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = mock_resource
        
        config = {
            "access_key_id": "test_key",
            "secret_access_key": "test_secret",
            "bucket_name": "test-bucket",
            "region": "us-east-1"
        }
        
        connector = S3Connector(config)
        connector.connect()
        
        assert connector.is_connected
        mock_boto3.client.assert_called_once()
        mock_boto3.resource.assert_called_once()
    
    @patch('connectors.data_lake.s3.boto3')
    def test_s3_upload_file(self, mock_boto3):
        """Test d'upload de fichier S3."""
        from connectors.data_lake.s3 import S3Connector
        
        # Mock du client
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        
        config = {
            "access_key_id": "test_key",
            "secret_access_key": "test_secret",
            "bucket_name": "test-bucket",
            "region": "us-east-1"
        }
        
        connector = S3Connector(config)
        connector.connect()
        
        # Test upload
        result = connector.upload_file("local_file.txt", "remote_file.txt")
        
        mock_client.upload_file.assert_called_once_with(
            "local_file.txt", "test-bucket", "remote_file.txt", ExtraArgs={}
        )
        assert result == "s3://test-bucket/remote_file.txt"
    
    def test_s3_invalid_config(self):
        """Test avec configuration S3 invalide."""
        from connectors.data_lake.s3 import S3Connector
        
        invalid_config = {"access_key_id": "test"}  # Config incomplète
        
        with pytest.raises(ConfigurationError):
            S3Connector(invalid_config)
