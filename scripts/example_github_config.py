#!/usr/bin/env python
"""
Exemple d'utilisation du connecteur GitHub avec la configuration structurée.

Ce script démontre comment utiliser le connecteur GitHub avec
la classe GitHubConfig pour une meilleure validation des paramètres.

Usage:
    python example_github_config.py
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Ajout du répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from connectors import create_connector
from connectors.config.social_media import GitHubConfig, create_social_config_from_dict
from connectors.exceptions.connector_exceptions import (
    SocialMediaConnectionError,
    SocialMediaAuthenticationError,
    SocialMediaAPIError,
)


def setup_logging():
    """Configure le logging."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def main():
    """Fonction principale."""
    setup_logging()

    # Charger les variables d'environnement
    load_dotenv()

    # Récupération du token GitHub depuis l'environnement
    github_token = os.environ.get("GITHUB_ACCESS_TOKEN")
    if not github_token:
        print("Erreur: Variable d'environnement GITHUB_ACCESS_TOKEN non définie")
        print("Veuillez la définir avec votre token d'accès GitHub")
        return 1

    # Configuration avec la classe GitHubConfig (validation intégrée)
    try:
        github_config = GitHubConfig(
            access_token=github_token,
            default_owner=os.environ.get("GITHUB_DEFAULT_OWNER"),
            default_repo=os.environ.get("GITHUB_DEFAULT_REPO"),
            metrics_enabled=True,
        )

        # Création d'une config pour plusieurs réseaux sociaux
        # (si vous avez besoin de configurer plusieurs connecteurs)
        social_config = create_social_config_from_dict(
            {
                "github": github_config.dict(),
                # D'autres plateformes peuvent être ajoutées ici
            }
        )

        print(f"Plateformes configurées: {social_config.get_configured_platforms()}")

        # Pour le connecteur, on utilise directement la config GitHub
        config = github_config.dict()

    except ValueError as e:
        print(f"Erreur de configuration: {e}")
        return 1

    try:
        # Création du connecteur avec la configuration validée
        github = create_connector("github", config, "my_github")

        # Test de connexion
        with github.connection():
            print("Connecté à GitHub! Configuration validée avec succès.")

            # Récupérer les informations du profil
            profile = github.get_profile_info()
            print(f"Utilisateur connecté: {profile['login']} ({profile['name'] or 'Non spécifié'})")
            print(
                f"Repos: {profile['public_repos']} repos publics, {profile['private_repos']} repos privés"
            )

            # Afficher les dépôts par défaut configurés
            print(
                f"\nDépôt par défaut configuré: {github_config.default_owner}/{github_config.default_repo}"
            )

            # Avantages de l'utilisation de GitHubConfig:
            print("\nAvantages de l'utilisation de GitHubConfig:")
            print("✓ Validation automatique des paramètres obligatoires")
            print("✓ Structure cohérente avec les autres connecteurs")
            print("✓ Intégration avec le framework de configuration")
            print("✓ Possibilité d'extension avec des validateurs personnalisés")

    except SocialMediaConnectionError as e:
        print(f"Erreur de connexion: {e}")
        return 1
    except SocialMediaAuthenticationError as e:
        print(f"Erreur d'authentification: {e}")
        print("Vérifiez que votre token est valide et possède les permissions requises")
        return 1
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
