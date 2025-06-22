#!/usr/bin/env python
"""
Exemple d'utilisation du connecteur SMTP.

Ce script démontre comment utiliser le connecteur SMTP pour envoyer des emails.

Usage:
    python example_smtp.py
"""

import os
import sys
import logging
from dotenv import load_dotenv
from datetime import datetime

# Ajout du répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from connectors import create_connector


def main():
    """Fonction principale."""
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Charger les variables d'environnement
    load_dotenv()

    print("=== Exemple du connecteur SMTP ===")

    # Configuration SMTP
    config = {
        "host": "smtp.example.com",  # Remplacez par votre serveur SMTP
        "port": 587,
        "username": "your-username",  # Remplacez par votre nom d'utilisateur
        "password": "your-password",  # Remplacez par votre mot de passe
        "use_tls": True,
        "timeout": 30,
    }

    # Pour Gmail, utilisez plutôt le connecteur Gmail spécifique:
    # gmail_config = {
    #     'username': 'your-email@gmail.com',
    #     'password': 'your-password-or-app-password'
    # }
    # smtp = create_connector("gmail", gmail_config)

    try:
        # Création du connecteur
        smtp = create_connector("smtp", config)

        print("Configuration du connecteur SMTP:")
        print(f"- Serveur: {config['host']}:{config['port']}")
        print(f"- TLS activé: {'Oui' if config['use_tls'] else 'Non'}")
        print()

        print(
            "Pour tester l'envoi d'emails, décommentez le code ci-dessous et ajoutez vos informations."
        )

        # Exemple d'envoi d'un email simple
        # with smtp.connection():
        #     result = smtp.send_message(
        #         message="Ceci est un message de test.",
        #         recipient="destinataire@example.com",
        #         subject="Test du connecteur SMTP",
        #         from_name="Connecteur Python"
        #     )
        #     print(f"Email envoyé avec succès: {result}")

        # Exemple d'envoi d'un email HTML avec pièce jointe
        # with smtp.connection():
        #     result = smtp.send_message(
        #         message="<h1>Test HTML</h1><p>Ceci est un <b>message HTML</b> de test.</p>",
        #         recipient="destinataire@example.com",
        #         subject="Test HTML avec pièce jointe",
        #         from_name="Connecteur Python",
        #         html=True,
        #         cc=["copie@example.com"],
        #         attachments=["chemin/vers/fichier.pdf"]
        #     )
        #     print(f"Email HTML envoyé avec succès: {result}")

    except Exception as e:
        logger.error(f"Erreur: {e}")

    print("\nPour utiliser Gmail, voir l'exemple dans example_gmail.py")


if __name__ == "__main__":
    main()
