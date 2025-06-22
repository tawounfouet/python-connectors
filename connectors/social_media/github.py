"""
Connecteur pour GitHub.

Ce module fournit un connecteur pour interagir avec l'API GitHub,
permettant de créer des issues, des commentaires, récupérer les informations du profil
et gérer les dépôts.
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import base64
import logging

from .base_social import SocialMediaConnector
from ..exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError,
    SocialMediaAPIError,
)
from ..registry import register_connector


@register_connector("github")
class GitHubConnector(SocialMediaConnector):
    """
    Connecteur pour GitHub utilisant l'API v3.

    Supporte l'authentification par token personnel et les opérations de base
    comme créer des issues, des commentaires, et gérer les repositories.
    """

    def __init__(self, config: Dict[str, Any], connector_name: Optional[str] = None):
        """
        Initialise le connecteur GitHub.

        Args:
            config: Configuration contenant :
                - access_token: Token d'accès personnel GitHub
                - default_owner: Propriétaire par défaut pour les opérations (optionnel)
                - default_repo: Repository par défaut pour les opérations (optionnel)
                - connector_name: Nom du connecteur (pour les métriques)
        """
        super().__init__(config, connector_name)
        self.api_base_url = "https://api.github.com"
        self.access_token = config.get("access_token")
        self.default_owner = config.get("default_owner")
        self.default_repo = config.get("default_repo")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        self.session = requests.Session()

    def connect(self) -> bool:
        """
        Établit la connexion avec l'API GitHub.

        Returns:
            bool: True si la connexion est établie avec succès.

        Raises:
            SocialMediaConnectionError: Si la connexion échoue.
        """
        try:
            self.authenticate()
            return True
        except SocialMediaAuthenticationError as e:
            self.logger.error(f"Failed to connect to GitHub: {e}")
            raise SocialMediaConnectionError(f"Failed to connect to GitHub: {e}")

    def disconnect(self) -> bool:
        """
        Ferme la connexion avec l'API GitHub.

        Returns:
            bool: True si la déconnexion est réussie.
        """
        if self.session:
            self.session.close()
            self.authenticated = False
            self.logger.info("Disconnected from GitHub API")
            return True
        return False

    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API GitHub.

        Returns:
            bool: True si la connexion fonctionne correctement.
        """
        try:
            response = self.session.get(f"{self.api_base_url}/user", headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"GitHub connection test failed: {e}")
            return False

    def authenticate(self) -> bool:
        """
        Authentifie auprès de l'API GitHub en utilisant le token personnel.

        Returns:
            bool: True si l'authentification réussit.

        Raises:
            SocialMediaAuthenticationError: Si l'authentification échoue.
        """
        if not self.access_token:
            raise SocialMediaAuthenticationError("GitHub access token not provided")

        self.headers["Authorization"] = f"token {self.access_token}"

        try:
            response = self.session.get(f"{self.api_base_url}/user", headers=self.headers)

            if response.status_code != 200:
                error_message = (
                    f"GitHub authentication failed: {response.status_code} - {response.text}"
                )
                self.logger.error(error_message)
                raise SocialMediaAuthenticationError(error_message)

            self.authenticated = True
            self.logger.info("Successfully authenticated with GitHub API")
            return True

        except requests.RequestException as e:
            error_message = f"GitHub authentication failed: {str(e)}"
            self.logger.error(error_message)
            raise SocialMediaAuthenticationError(error_message)

    def post_message(
        self,
        content: str,
        media: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Crée une issue ou un commentaire sur GitHub.

        Dans le contexte GitHub, cette méthode crée une nouvelle issue par défaut,
        mais peut aussi être utilisée pour créer un commentaire sur une issue existante
        en spécifiant l'option 'issue_number'.

        Args:
            content: Le contenu textuel du message.
            media: Non utilisé pour GitHub (ignoré).
            options: Options supplémentaires :
                - owner: Propriétaire du dépôt (par défaut: default_owner)
                - repo: Nom du dépôt (par défaut: default_repo)
                - title: Titre de l'issue (obligatoire pour création d'issue)
                - issue_number: Numéro de l'issue pour commenter (optionnel)
                - labels: Liste des labels à appliquer (optionnel)

        Returns:
            Dict contenant les informations sur l'issue ou le commentaire créé.

        Raises:
            SocialMediaAPIError: Si la création échoue.
        """
        if not self.authenticated:
            self.authenticate()

        options = options or {}
        owner = options.get("owner") or self.default_owner
        repo = options.get("repo") or self.default_repo

        if not owner or not repo:
            raise SocialMediaAPIError("Owner and repository must be provided")

        # Traiter comme un commentaire si issue_number est fourni
        if "issue_number" in options:
            return self._create_issue_comment(owner, repo, options["issue_number"], content)
        else:
            # Sinon, créer une nouvelle issue
            title = options.get("title")
            if not title:
                raise SocialMediaAPIError("Title must be provided when creating an issue")

            data = {"title": title, "body": content}

            if "labels" in options:
                data["labels"] = options["labels"]

            try:
                response = self.session.post(
                    f"{self.api_base_url}/repos/{owner}/{repo}/issues",
                    headers=self.headers,
                    json=data,
                )
                self._update_rate_limit_info(response.headers)

                if response.status_code not in [201]:
                    error_message = (
                        f"Failed to create issue: {response.status_code} - {response.text}"
                    )
                    self.logger.error(error_message)
                    raise SocialMediaAPIError(error_message)

                issue_data = response.json()
                self.logger.info(f"Created issue #{issue_data['number']}: {title}")

                return {
                    "id": str(issue_data["id"]),
                    "number": issue_data["number"],
                    "url": issue_data["html_url"],
                    "created_at": issue_data["created_at"],
                }

            except requests.RequestException as e:
                error_message = f"Failed to create issue: {str(e)}"
                self.logger.error(error_message)
                raise SocialMediaAPIError(error_message)

    def _create_issue_comment(
        self, owner: str, repo: str, issue_number: int, content: str
    ) -> Dict[str, Any]:
        """
        Crée un commentaire sur une issue existante.

        Args:
            owner: Propriétaire du dépôt
            repo: Nom du dépôt
            issue_number: Numéro de l'issue
            content: Contenu du commentaire

        Returns:
            Dict contenant les informations sur le commentaire créé.

        Raises:
            SocialMediaAPIError: Si la création échoue.
        """
        try:
            response = self.session.post(
                f"{self.api_base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments",
                headers=self.headers,
                json={"body": content},
            )
            self._update_rate_limit_info(response.headers)

            if response.status_code != 201:
                error_message = (
                    f"Failed to create comment: {response.status_code} - {response.text}"
                )
                self.logger.error(error_message)
                raise SocialMediaAPIError(error_message)

            comment_data = response.json()
            self.logger.info(f"Created comment on issue #{issue_number}")

            return {
                "id": str(comment_data["id"]),
                "url": comment_data["html_url"],
                "created_at": comment_data["created_at"],
            }

        except requests.RequestException as e:
            error_message = f"Failed to create comment: {str(e)}"
            self.logger.error(error_message)
            raise SocialMediaAPIError(error_message)

    def get_feed(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Récupère les dernières activités (issues, pull requests) d'un dépôt.

        Args:
            limit: Nombre maximum d'éléments à récupérer (max: 100)
            **kwargs: Options supplémentaires :
                - owner: Propriétaire du dépôt (par défaut: default_owner)
                - repo: Nom du dépôt (par défaut: default_repo)
                - state: État des issues ('open', 'closed', 'all') (défaut: 'open')
                - type: Type d'élément ('issues', 'pulls', 'all') (défaut: 'all')

        Returns:
            Liste des activités récentes du dépôt

        Raises:
            SocialMediaAPIError: Si la récupération échoue
        """
        if not self.authenticated:
            self.authenticate()

        owner = kwargs.get("owner") or self.default_owner
        repo = kwargs.get("repo") or self.default_repo
        state = kwargs.get("state", "open")
        item_type = kwargs.get("type", "all")

        if not owner or not repo:
            raise SocialMediaAPIError("Owner and repository must be provided")

        try:
            results = []

            # Récupération des issues si demandé
            if item_type in ["issues", "all"]:
                params = {
                    "state": state,
                    "per_page": min(limit, 100),
                    "sort": "updated",
                    "direction": "desc",
                }

                response = self.session.get(
                    f"{self.api_base_url}/repos/{owner}/{repo}/issues",
                    headers=self.headers,
                    params=params,
                )
                self._update_rate_limit_info(response.headers)

                if response.status_code == 200:
                    issues = response.json()
                    # Filtrer les pull requests des issues
                    issues = [issue for issue in issues if "pull_request" not in issue]

                    for issue in issues[:limit]:
                        results.append(
                            {
                                "id": str(issue["id"]),
                                "number": issue["number"],
                                "title": issue["title"],
                                "type": "issue",
                                "url": issue["html_url"],
                                "state": issue["state"],
                                "created_at": issue["created_at"],
                                "updated_at": issue["updated_at"],
                                "author": issue["user"]["login"],
                                "labels": [label["name"] for label in issue.get("labels", [])],
                            }
                        )

            # Récupération des pull requests si demandé
            if item_type in ["pulls", "all"] and len(results) < limit:
                remaining = limit - len(results)
                params = {
                    "state": state,
                    "per_page": min(remaining, 100),
                    "sort": "updated",
                    "direction": "desc",
                }

                response = self.session.get(
                    f"{self.api_base_url}/repos/{owner}/{repo}/pulls",
                    headers=self.headers,
                    params=params,
                )
                self._update_rate_limit_info(response.headers)

                if response.status_code == 200:
                    pulls = response.json()

                    for pull in pulls[:remaining]:
                        results.append(
                            {
                                "id": str(pull["id"]),
                                "number": pull["number"],
                                "title": pull["title"],
                                "type": "pull_request",
                                "url": pull["html_url"],
                                "state": pull["state"],
                                "created_at": pull["created_at"],
                                "updated_at": pull["updated_at"],
                                "author": pull["user"]["login"],
                                "branch": pull["head"]["ref"],
                            }
                        )

            # Tri par date de mise à jour
            results.sort(key=lambda x: x["updated_at"], reverse=True)
            return results[:limit]

        except requests.RequestException as e:
            error_message = f"Failed to retrieve feed: {str(e)}"
            self.logger.error(error_message)
            raise SocialMediaAPIError(error_message)

    def get_profile_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du profil GitHub connecté.

        Returns:
            Dict contenant les informations du profil

        Raises:
            SocialMediaAPIError: Si la récupération échoue
        """
        if not self.authenticated:
            self.authenticate()

        try:
            response = self.session.get(f"{self.api_base_url}/user", headers=self.headers)
            self._update_rate_limit_info(response.headers)

            if response.status_code != 200:
                error_message = (
                    f"Failed to retrieve profile: {response.status_code} - {response.text}"
                )
                self.logger.error(error_message)
                raise SocialMediaAPIError(error_message)

            user_data = response.json()

            # Récupération du nombre de repos
            repos_response = self.session.get(
                f"{self.api_base_url}/user/repos?per_page=1", headers=self.headers
            )
            repos_count = 0
            if "Link" in repos_response.headers:
                link_header = repos_response.headers["Link"]
                if 'rel="last"' in link_header:
                    import re

                    # Extraction du nombre total de pages
                    match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if match:
                        repos_count = int(match.group(1))

            profile = {
                "login": user_data["login"],
                "id": user_data["id"],
                "name": user_data.get("name"),
                "url": user_data["html_url"],
                "avatar_url": user_data["avatar_url"],
                "public_repos": user_data["public_repos"],
                "private_repos": repos_count - user_data["public_repos"] if repos_count > 0 else 0,
                "followers": user_data["followers"],
                "following": user_data["following"],
                "company": user_data.get("company"),
                "blog": user_data.get("blog"),
                "location": user_data.get("location"),
                "email": user_data.get("email"),
                "bio": user_data.get("bio"),
                "created_at": user_data["created_at"],
                "updated_at": user_data["updated_at"],
            }

            return profile

        except requests.RequestException as e:
            error_message = f"Failed to retrieve profile: {str(e)}"
            self.logger.error(error_message)
            raise SocialMediaAPIError(error_message)

    def delete_post(self, post_id: str) -> bool:
        """
        Supprime une issue ou un commentaire.

        Args:
            post_id: Format 'type:owner:repo:number' où type est 'issue' ou 'comment'
                    Par exemple: 'issue:username:repo:42' ou 'comment:username:repo:123'

        Returns:
            bool: True si la suppression réussit, False sinon.

        Raises:
            SocialMediaAPIError: Si la suppression échoue.
        """
        if not self.authenticated:
            self.authenticate()

        try:
            parts = post_id.split(":")
            if len(parts) != 4:
                raise SocialMediaAPIError(f"Invalid post_id format: {post_id}")

            post_type, owner, repo, number = parts

            if post_type == "issue":
                # GitHub ne permet pas de supprimer des issues via l'API, seulement les fermer
                response = self.session.patch(
                    f"{self.api_base_url}/repos/{owner}/{repo}/issues/{number}",
                    headers=self.headers,
                    json={"state": "closed"},
                )

                if response.status_code != 200:
                    error_message = (
                        f"Failed to close issue: {response.status_code} - {response.text}"
                    )
                    self.logger.error(error_message)
                    raise SocialMediaAPIError(error_message)

                self.logger.info(f"Closed issue #{number}")

            elif post_type == "comment":
                response = self.session.delete(
                    f"{self.api_base_url}/repos/{owner}/{repo}/issues/comments/{number}",
                    headers=self.headers,
                )

                if response.status_code != 204:
                    error_message = (
                        f"Failed to delete comment: {response.status_code} - {response.text}"
                    )
                    self.logger.error(error_message)
                    raise SocialMediaAPIError(error_message)

                self.logger.info(f"Deleted comment {number}")

            else:
                raise SocialMediaAPIError(f"Invalid post type: {post_type}")

            return True

        except requests.RequestException as e:
            error_message = f"Failed to delete post: {str(e)}"
            self.logger.error(error_message)
            raise SocialMediaAPIError(error_message)

    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """
        Met à jour les informations de limite de taux à partir des headers HTTP GitHub.

        Args:
            headers: Headers de la réponse HTTP contenant les infos de rate limit.
        """
        try:
            if "X-RateLimit-Limit" in headers:
                self.rate_limit_info["limit"] = int(headers["X-RateLimit-Limit"])

            if "X-RateLimit-Remaining" in headers:
                self.rate_limit_info["remaining"] = int(headers["X-RateLimit-Remaining"])

            if "X-RateLimit-Reset" in headers:
                self.rate_limit_info["reset_time"] = int(headers["X-RateLimit-Reset"])

            if "X-RateLimit-Used" in headers:
                self.rate_limit_info["used"] = int(headers["X-RateLimit-Used"])
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error parsing rate limit headers: {e}")
