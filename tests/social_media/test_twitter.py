"""
Tests unitaires pour le connecteur Twitter.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest

from connectors.social_media.twitter import TwitterConnector
from connectors.exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError,
    SocialMediaAPIError
)


class TestTwitterConnector(unittest.TestCase):
    """Tests pour le connecteur Twitter."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.config = {
            'bearer_token': 'test_bearer_token',
            'api_key': 'test_api_key',
            'api_secret': 'test_api_secret'
        }
        self.connector = TwitterConnector(self.config)
    
    def test_init_with_valid_config(self):
        """Test d'initialisation avec une configuration valide."""
        self.assertEqual(self.connector.bearer_token, 'test_bearer_token')
        self.assertEqual(self.connector.api_key, 'test_api_key')
        self.assertFalse(self.connector.authenticated)
    
    def test_init_without_bearer_token(self):
        """Test d'initialisation sans bearer token."""
        config = {'api_key': 'test_api_key'}
        with self.assertRaises(SocialMediaConnectionError):
            TwitterConnector(config)
    
    @patch('connectors.social_media.twitter.requests.Session')
    def test_successful_authentication(self, mock_session):
        """Test d'authentification réussie."""
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'id': '123456789',
                'name': 'Test User',
                'username': 'testuser'
            }
        }
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Test
        result = self.connector.connect()
        
        # Vérifications
        self.assertTrue(result)
        self.assertTrue(self.connector.authenticated)
        mock_session_instance.get.assert_called_once()
    
    @patch('connectors.social_media.twitter.requests.Session')
    def test_failed_authentication(self, mock_session):
        """Test d'authentification échouée."""
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 401
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Test
        with self.assertRaises(SocialMediaAuthenticationError):
            self.connector.authenticate()
    
    @patch('connectors.social_media.twitter.requests.Session')
    def test_post_message_success(self, mock_session):
        """Test de publication d'un message réussie."""
        # Configuration du connecteur comme authentifié
        self.connector.authenticated = True
        self.connector.session = Mock()
        
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {
                'id': '1234567890',
                'text': 'Test tweet'
            }
        }
        mock_response.headers = {}
        
        self.connector.session.post.return_value = mock_response
        
        # Test
        result = self.connector.post_message("Test tweet")
        
        # Vérifications
        self.assertEqual(result['id'], '1234567890')
        self.assertEqual(result['text'], 'Test tweet')
        self.assertEqual(result['platform'], 'twitter')
        self.assertIn('url', result)
    
    def test_post_message_not_authenticated(self):
        """Test de publication sans authentification."""
        with self.assertRaises(SocialMediaAuthenticationError):
            self.connector.post_message("Test tweet")
    
    def test_post_message_too_long(self):
        """Test de publication avec un message trop long."""
        self.connector.authenticated = True
        long_message = "x" * 281  # Plus de 280 caractères
        
        with self.assertRaises(SocialMediaAPIError):
            self.connector.post_message(long_message)
    
    @patch('connectors.social_media.twitter.requests.Session')
    def test_get_feed_success(self, mock_session):
        """Test de récupération du flux réussie."""
        # Configuration du connecteur comme authentifié
        self.connector.authenticated = True
        self.connector.session = Mock()
        
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': '1',
                    'text': 'First tweet',
                    'created_at': '2023-01-01T00:00:00Z'
                },
                {
                    'id': '2', 
                    'text': 'Second tweet',
                    'created_at': '2023-01-02T00:00:00Z'
                }
            ]
        }
        mock_response.headers = {}
        
        self.connector.session.get.return_value = mock_response
        
        # Test
        result = self.connector.get_feed(limit=5)
        
        # Vérifications
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], '1')
        self.assertEqual(result[0]['text'], 'First tweet')
        self.assertEqual(result[0]['platform'], 'twitter')
    
    def test_get_feed_not_authenticated(self):
        """Test de récupération du flux sans authentification."""
        with self.assertRaises(SocialMediaAuthenticationError):
            self.connector.get_feed()
    
    @patch('connectors.social_media.twitter.requests.Session')
    def test_get_profile_info_success(self, mock_session):
        """Test de récupération des infos de profil réussie."""
        # Configuration du connecteur comme authentifié
        self.connector.authenticated = True
        self.connector.session = Mock()
        
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'id': '123456789',
                'name': 'Test User',
                'username': 'testuser',
                'description': 'Test bio',
                'public_metrics': {
                    'followers_count': 1000,
                    'following_count': 500,
                    'tweet_count': 100
                },
                'verified': False
            }
        }
        mock_response.headers = {}
        
        self.connector.session.get.return_value = mock_response
        
        # Test
        result = self.connector.get_profile_info()
        
        # Vérifications
        self.assertEqual(result['id'], '123456789')
        self.assertEqual(result['name'], 'Test User')
        self.assertEqual(result['username'], 'testuser')
        self.assertEqual(result['followers_count'], 1000)
        self.assertEqual(result['platform'], 'twitter')
    
    def test_disconnect(self):
        """Test de déconnexion."""
        # Configuration d'une session mockée
        self.connector.session = Mock()
        self.connector.authenticated = True
        
        # Test
        result = self.connector.disconnect()
        
        # Vérifications
        self.assertTrue(result)
        self.assertFalse(self.connector.authenticated)
        self.connector.session.close.assert_called_once()
        self.assertIsNone(self.connector.session)
    
    def test_rate_limit_info_update(self):
        """Test de mise à jour des informations de rate limit."""
        headers = {
            'x-rate-limit-limit': '300',
            'x-rate-limit-remaining': '299',
            'x-rate-limit-reset': '1609459200'
        }
        
        self.connector._update_rate_limit_info(headers)
        
        rate_info = self.connector.get_rate_limit_info()
        self.assertEqual(rate_info['limit'], 300)
        self.assertEqual(rate_info['remaining'], 299)
        self.assertEqual(rate_info['reset_time'], 1609459200)


if __name__ == '__main__':
    unittest.main()
