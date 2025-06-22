#!/usr/bin/env python
"""
Exemple d'utilisation du connecteur GitHub.

Ce script démontre comment utiliser le connecteur GitHub pour interagir
avec l'API GitHub, créer des issues et récupérer des informations.

Usage:
    python example_github.py
"""

import os
import sys
import logging
from pprint import pprint

# Ajout du répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from connectors import create_connector
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

    # Récupération du token GitHub depuis l'environnement
    github_token = os.environ.get("GITHUB_ACCESS_TOKEN")
    if not github_token:
        print("Erreur: Variable d'environnement GITHUB_ACCESS_TOKEN non définie")
        print("Veuillez la définir avec votre token d'accès GitHub")
        return 1

    # config = {
    #     'access_token': 'your_personal_access_token',
    #     'default_owner': 'username',
    #     'default_repo': 'repository'
    # }

    # Configuration du connecteur (méthode simple)
    config = {
        "access_token": github_token,
        # Optionnels, peuvent être spécifiés dans les méthodes
        "default_owner": os.environ.get("GITHUB_DEFAULT_OWNER"),
        "default_repo": os.environ.get("GITHUB_DEFAULT_REPO"),
        "metrics_enabled": True,
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }

    # Alternative: utiliser la classe de configuration (méthode recommandée)
    # from connectors.config.social_media import GitHubConfig, create_social_config_from_dict
    # github_config = GitHubConfig(
    #     access_token=github_token,
    #     default_owner=os.environ.get("GITHUB_DEFAULT_OWNER"),
    #     default_repo=os.environ.get("GITHUB_DEFAULT_REPO"),
    #     metrics_enabled=True,
    # )
    # social_config = create_social_config_from_dict({"github": github_config.dict()})
    # config = github_config.dict()

    try:
        # Création du connecteur
        github = create_connector("github", config, "my_github")

        # Utilisation du connecteur avec context manager pour la connexion/déconnexion
        with github.connection():
            print("Connecté à GitHub! Démonstration des fonctionnalités:")
            print("-" * 50)

            # 1. Récupération des informations du profil
            print("\n1. Informations du profil:")
            profile = github.get_profile_info()
            print(f"Utilisateur: {profile['login']} ({profile['name']})")
            print(f"Repos: {profile['public_repos']} publics, {profile['private_repos']} privés")
            print(f"Abonnés: {profile['followers']}, Abonnements: {profile['following']}")

            # 2. Récupération des issues/PRs récentes
            print("\n2. Activité récente:")

            # Utiliser le dépôt par défaut ou en spécifier un
            owner = (
                input(
                    "Propriétaire du dépôt [default: {}]: ".format(
                        github.default_owner or "non défini"
                    )
                )
                or github.default_owner
            )

            if not owner:
                print("Erreur: Aucun propriétaire spécifié")
                return 1

            repo = (
                input("Nom du dépôt [default: {}]: ".format(github.default_repo or "non défini"))
                or github.default_repo
            )

            if not repo:
                print("Erreur: Aucun dépôt spécifié")
                return 1

            # Récupération du feed
            try:
                activity = github.get_feed(
                    limit=5, type="all", state="open", owner=owner, repo=repo
                )

                if not activity:
                    print(f"Aucune activité trouvée dans {owner}/{repo}")
                else:
                    for item in activity:
                        if item["type"] == "issue":
                            print(f"Issue #{item['number']}: {item['title']}")
                        else:
                            print(f"PR #{item['number']}: {item['title']} ({item['branch']})")
            except SocialMediaAPIError as e:
                print(f"Erreur lors de la récupération des activités: {e}")

            # 3. Demander si l'utilisateur veut créer une issue de test
            print("\n3. Création d'une issue de test:")
            create_issue = input("Souhaitez-vous créer une issue de test? (o/n): ")

            if create_issue.lower() == "o":
                issue_title = input("Titre de l'issue: ")
                issue_content = input("Contenu de l'issue: ")

                try:
                    issue = github.post_message(
                        content=issue_content,
                        options={
                            "owner": owner,
                            "repo": repo,
                            "title": issue_title,
                            "labels": ["documentation", "test"],
                        },
                    )
                    print(f"Issue #{issue['number']} créée avec succès: {issue['url']}")

                    # 4. Ajouter un commentaire à l'issue créée
                    add_comment = input("Ajouter un commentaire à cette issue? (o/n): ")

                    if add_comment.lower() == "o":
                        comment_content = input("Contenu du commentaire: ")

                        comment = github.post_message(
                            content=comment_content,
                            options={"owner": owner, "repo": repo, "issue_number": issue["number"]},
                        )
                        print(f"Commentaire ajouté: {comment['url']}")

                        # 5. Demander si l'utilisateur veut supprimer le commentaire
                        delete_comment = input("Supprimer ce commentaire? (o/n): ")

                        if delete_comment.lower() == "o":
                            comment_id = comment["url"].split("/")[-1]
                            github.delete_post(f"comment:{owner}:{repo}:{comment_id}")
                            print("Commentaire supprimé!")

                    # 6. Demander si l'utilisateur veut fermer l'issue
                    close_issue = input("Fermer cette issue? (o/n): ")

                    if close_issue.lower() == "o":
                        github.delete_post(f"issue:{owner}:{repo}:{issue['number']}")
                        print("Issue fermée!")

                except SocialMediaAPIError as e:
                    print(f"Erreur lors de la création de l'issue: {e}")

            # 7. Afficher les métriques d'utilisation
            print("\n7. Métriques d'utilisation:")
            metrics = github.get_metrics_summary()
            pprint(metrics)

            # 8. Afficher les limites de taux
            print("\n8. Informations sur les limites de taux:")
            rate_limits = github.get_rate_limit_info()
            print(f"Requêtes utilisées: {rate_limits.get('used', 'N/A')}")
            print(f"Requêtes restantes: {rate_limits.get('remaining', 'N/A')}")

            print("\nDémonstration terminée avec succès!")

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
