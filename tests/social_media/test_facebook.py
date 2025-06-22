"""
Tests unitaires pour le connecteur Facebook.
"""

import unittest
from unittest.mock import Mock, patch
import pytest

from connectors.social_media.facebook import FacebookConnector
from connectors.exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError
)


class TestFacebookConnector(unittest.TestCase):
    """Tests pour le connecteur Facebook."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.config = {
            'access_token': 'test_access_token',
            'page_id': 'test_page_id'
        }
        self.connector = FacebookConnector(self.config)
    
    def test_init_with_valid_config(self):
        """Test d'initialisation avec une configuration valide."""
        self.assertEqual(self.connector.access_token, 'test_access_token')
        self.assertEqual(self.connector.page_id, 'test_page_id')
        self.assertFalse(self.connector.authenticated)
    
    def test_init_without_access_token(self):
        """Test d'initialisation sans access token."""
        config = {'page_id': 'test_page_id'}
        with self.assertRaises(SocialMediaConnectionError):
            FacebookConnector(config)


if __name__ == '__main__':
    unittest.main()
