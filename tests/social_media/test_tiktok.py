"""
Tests unitaires pour le connecteur TikTok.
"""

import unittest
from unittest.mock import Mock, patch
import pytest

from connectors.social_media.tiktok import TikTokConnector
from connectors.exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError
)


class TestTikTokConnector(unittest.TestCase):
    """Tests pour le connecteur TikTok."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.config = {
            'access_token': 'test_access_token',
            'client_key': 'test_client_key'
        }
        self.connector = TikTokConnector(self.config)
    
    def test_init_with_valid_config(self):
        """Test d'initialisation avec une configuration valide."""
        self.assertEqual(self.connector.access_token, 'test_access_token')
        self.assertEqual(self.connector.client_key, 'test_client_key')
        self.assertFalse(self.connector.authenticated)
    
    def test_init_without_access_token(self):
        """Test d'initialisation sans access token."""
        config = {'client_key': 'test_client_key'}
        with self.assertRaises(SocialMediaConnectionError):
            TikTokConnector(config)


if __name__ == '__main__':
    unittest.main()
