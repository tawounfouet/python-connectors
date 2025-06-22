"""
Tests unitaires pour le connecteur Instagram.
"""

import unittest
from unittest.mock import Mock, patch
import pytest

from connectors.social_media.instagram import InstagramConnector
from connectors.exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError
)


class TestInstagramConnector(unittest.TestCase):
    """Tests pour le connecteur Instagram."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.config = {
            'access_token': 'test_access_token',
            'user_id': 'test_user_id'
        }
        self.connector = InstagramConnector(self.config)
    
    def test_init_with_valid_config(self):
        """Test d'initialisation avec une configuration valide."""
        self.assertEqual(self.connector.access_token, 'test_access_token')
        self.assertEqual(self.connector.user_id, 'test_user_id')
        self.assertFalse(self.connector.authenticated)
    
    def test_init_without_access_token(self):
        """Test d'initialisation sans access token."""
        config = {'user_id': 'test_user_id'}
        with self.assertRaises(SocialMediaConnectionError):
            InstagramConnector(config)


if __name__ == '__main__':
    unittest.main()
