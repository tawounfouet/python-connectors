"""
Tests unitaires pour le connecteur LinkedIn.
"""

import unittest
from unittest.mock import Mock, patch
import pytest

from connectors.social_media.linkedin import LinkedInConnector
from connectors.exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError,
    SocialMediaAPIError
)


class TestLinkedInConnector(unittest.TestCase):
    """Tests pour le connecteur LinkedIn."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.config = {
            'access_token': 'test_access_token',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret'
        }
        self.connector = LinkedInConnector(self.config)
    
    def test_init_with_valid_config(self):
        """Test d'initialisation avec une configuration valide."""
        self.assertEqual(self.connector.access_token, 'test_access_token')
        self.assertEqual(self.connector.client_id, 'test_client_id')
        self.assertFalse(self.connector.authenticated)
    
    def test_init_without_access_token(self):
        """Test d'initialisation sans access token."""
        config = {'client_id': 'test_client_id'}
        with self.assertRaises(SocialMediaConnectionError):
            LinkedInConnector(config)
    
    @patch('connectors.social_media.linkedin.requests.Session')
    def test_successful_authentication(self, mock_session):
        """Test d'authentification réussie."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'test_user_id',
            'firstName': {'localized': {'en_US': 'John'}},
            'lastName': {'localized': {'en_US': 'Doe'}}
        }
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        result = self.connector.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.connector.authenticated)
    
    def test_get_profile_info_structure(self):
        """Test de la structure des informations de profil."""
        self.connector.authenticated = True
        self.connector.session = Mock()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'test_user_id',
            'firstName': {'localized': {'en_US': 'John'}},
            'lastName': {'localized': {'en_US': 'Doe'}},
            'headline': {'localized': {'en_US': 'Software Engineer'}}
        }
        mock_response.headers = {}
        
        self.connector.session.get.return_value = mock_response
        
        result = self.connector.get_profile_info()
        
        self.assertIn('platform', result)
        self.assertEqual(result['platform'], 'linkedin')
        self.assertIn('name', result)
        self.assertIn('id', result)


if __name__ == '__main__':
    unittest.main()
