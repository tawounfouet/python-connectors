"""
Tests unitaires pour le connecteur GitHub.
"""

import unittest
from unittest.mock import patch, MagicMock
import requests
import json
from datetime import datetime

from connectors.social_media.github import GitHubConnector
from connectors.exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError,
    SocialMediaAPIError,
)


class TestGitHubConnector(unittest.TestCase):
    """Tests unitaires pour le connecteur GitHub."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.config = {
            "access_token": "fake_token",
            "default_owner": "test_owner",
            "default_repo": "test_repo",
        }
        self.connector = GitHubConnector(self.config)

    @patch("requests.Session.get")
    def test_authentication_success(self, mock_get):
        """Test authentification réussie."""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "test_user", "id": 12345}
        mock_get.return_value = mock_response

        # Test
        result = self.connector.authenticate()

        # Vérifications
        self.assertTrue(result)
        self.assertTrue(self.connector.authenticated)
        mock_get.assert_called_once_with(
            "https://api.github.com/user", headers=self.connector.headers
        )

    @patch("requests.Session.get")
    def test_authentication_failure(self, mock_get):
        """Test échec d'authentification."""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Bad credentials"
        mock_get.return_value = mock_response

        # Test
        with self.assertRaises(SocialMediaAuthenticationError):
            self.connector.authenticate()

        # Vérifications
        self.assertFalse(self.connector.authenticated)

    @patch("requests.Session.post")
    def test_create_issue(self, mock_post):
        """Test création d'une issue."""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123456,
            "number": 42,
            "html_url": "https://github.com/test_owner/test_repo/issues/42",
            "created_at": "2023-01-01T12:00:00Z",
        }
        mock_post.return_value = mock_response

        # Simuler l'authentification
        self.connector.authenticated = True

        # Test
        result = self.connector.post_message(
            content="Test issue content", options={"title": "Test Issue", "labels": ["bug"]}
        )

        # Vérifications
        self.assertEqual(result["number"], 42)
        self.assertEqual(result["url"], "https://github.com/test_owner/test_repo/issues/42")
        mock_post.assert_called_once()

        # Vérification des données envoyées
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(
            json.loads(call_kwargs["data"]),
            {"title": "Test Issue", "body": "Test issue content", "labels": ["bug"]},
        )

    @patch("requests.Session.get")
    def test_get_feed(self, mock_get):
        """Test récupération du flux d'activité."""
        # Configuration du mock pour les issues
        mock_issues_response = MagicMock()
        mock_issues_response.status_code = 200
        mock_issues_response.json.return_value = [
            {
                "id": 123,
                "number": 42,
                "title": "Test Issue",
                "html_url": "https://github.com/test_owner/test_repo/issues/42",
                "state": "open",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T13:00:00Z",
                "user": {"login": "test_user"},
            }
        ]

        # Configuration du mock pour les pull requests
        mock_pulls_response = MagicMock()
        mock_pulls_response.status_code = 200
        mock_pulls_response.json.return_value = [
            {
                "id": 456,
                "number": 43,
                "title": "Test PR",
                "html_url": "https://github.com/test_owner/test_repo/pull/43",
                "state": "open",
                "created_at": "2023-01-01T14:00:00Z",
                "updated_at": "2023-01-01T15:00:00Z",
                "user": {"login": "test_user"},
                "head": {"ref": "feature-branch"},
            }
        ]

        # Configuration du comportement du mock pour les deux appels
        mock_get.side_effect = [mock_issues_response, mock_pulls_response]

        # Simuler l'authentification
        self.connector.authenticated = True

        # Test
        result = self.connector.get_feed(limit=5, type="all")

        # Vérifications
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "pull_request")
        self.assertEqual(result[0]["number"], 43)
        self.assertEqual(result[1]["type"], "issue")
        self.assertEqual(result[1]["number"], 42)

        # Vérification des appels API
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.Session.get")
    def test_get_profile_info(self, mock_get):
        """Test récupération des informations du profil."""
        # Configuration du mock pour les infos user
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "login": "test_user",
            "id": 12345,
            "name": "Test User",
            "html_url": "https://github.com/test_user",
            "avatar_url": "https://github.com/avatar/test_user",
            "public_repos": 10,
            "followers": 42,
            "following": 15,
            "company": "Test Company",
            "blog": "https://test.com",
            "location": "Test City",
            "email": "test@example.com",
            "bio": "Test bio",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }

        # Configuration du mock pour les repos
        mock_repos_response = MagicMock()
        mock_repos_response.status_code = 200
        mock_repos_response.headers = {
            "Link": '<https://api.github.com/user/repos?page=15>; rel="last"'
        }

        # Configuration du comportement du mock pour les deux appels
        mock_get.side_effect = [mock_user_response, mock_repos_response]

        # Simuler l'authentification
        self.connector.authenticated = True

        # Test
        result = self.connector.get_profile_info()

        # Vérifications
        self.assertEqual(result["login"], "test_user")
        self.assertEqual(result["name"], "Test User")
        self.assertEqual(result["public_repos"], 10)
        self.assertEqual(result["private_repos"], 15 - 10)  # Total - public

        # Vérification des appels API
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.Session.patch")
    def test_delete_issue(self, mock_patch):
        """Test fermeture d'une issue (delete)."""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        # Simuler l'authentification
        self.connector.authenticated = True

        # Test
        result = self.connector.delete_post("issue:test_owner:test_repo:42")

        # Vérifications
        self.assertTrue(result)
        mock_patch.assert_called_once_with(
            "https://api.github.com/repos/test_owner/test_repo/issues/42",
            headers=self.connector.headers,
            json={"state": "closed"},
        )

    @patch("requests.Session.delete")
    def test_delete_comment(self, mock_delete):
        """Test suppression d'un commentaire."""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        # Simuler l'authentification
        self.connector.authenticated = True

        # Test
        result = self.connector.delete_post("comment:test_owner:test_repo:42")

        # Vérifications
        self.assertTrue(result)
        mock_delete.assert_called_once_with(
            "https://api.github.com/repos/test_owner/test_repo/issues/comments/42",
            headers=self.connector.headers,
        )


if __name__ == "__main__":
    unittest.main()
