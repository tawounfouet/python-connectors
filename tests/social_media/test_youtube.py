"""
Tests unitaires pour le connecteur YouTube.
"""

import unittest
from unittest.mock import Mock, patch
import pytest

from connectors.social_media.youtube import YouTubeConnector
from connectors.exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError
)


class TestYouTubeConnector(unittest.TestCase):
    """Tests pour le connecteur YouTube."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.config = {
            'api_key': 'test_api_key',
            'access_token': 'test_access_token'
        }
        self.connector = YouTubeConnector(self.config)
    
    def test_init_with_valid_config(self):
        """Test d'initialisation avec une configuration valide."""
        self.assertEqual(self.connector.api_key, 'test_api_key')
        self.assertEqual(self.connector.access_token, 'test_access_token')
        self.assertFalse(self.connector.authenticated)
    
    def test_init_without_api_key(self):
        """Test d'initialisation sans clé API."""
        config = {'access_token': 'test_access_token'}
        with self.assertRaises(SocialMediaConnectionError):
            YouTubeConnector(config)


if __name__ == '__main__':
    unittest.main()
