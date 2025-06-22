#!/usr/bin/env python
"""
Exemple d'utilisation du connecteur Gmail.

Ce script démontre comment utiliser le connecteur Gmail pour envoyer des emails.

Usage:
    python example_gmail.py
"""

import os
import sys
import logging
from dotenv import load_dotenv
from datetime import datetime

# Ajout du répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from connectors import create_connector
from connectors.utils.logger import setup_logger


def setup_logging():
    """Configure le logging."""
    return setup_logger(
        name="example_gmail",
        log_dir="logs",
        log_file="example_gmail.log",
        level=logging.INFO,
        console_output=True,
    )


def main():
    """Fonction principale."""
    logger = setup_logging()

    # Charger les variables d'environnement
    load_dotenv()

    # Configuration Gmail
    gmail_password = os.environ.get("GMAIL_PASSWORD")
    gmail_username = os.environ.get("GMAIL_USERNAME")

    if not gmail_username or not gmail_password:
        logger.error(
            "Les variables d'environnement GMAIL_USERNAME et GMAIL_PASSWORD doivent être définies"
        )
        logger.info("Ajoutez-les à votre fichier .env :")
        logger.info("GMAIL_USERNAME=votre.email@gmail.com")
        logger.info("GMAIL_PASSWORD=votre_mot_de_passe_ou_mot_de_passe_d_application")
        return 1

    config = {
        "username": gmail_username,
        "password": gmail_password,
        # Les options suivantes sont définies automatiquement par le connecteur Gmail
        # 'host': 'smtp.gmail.com',
        # 'port': 587,
        # 'use_tls': True
    }

    try:
        # Création du connecteur
        gmail = create_connector("gmail", config, "my_gmail")

        # Test de connexion
        logger.info("Test de connexion à Gmail...")
        if gmail.test_connection():
            logger.info("✅ Connexion à Gmail réussie")

            # Préparation de l'email
            recipient = input("Adresse email du destinataire: ").strip()
            subject = input("Sujet de l'email: ").strip() or "Test du connecteur Gmail"
            html_mode = input("Mode HTML? (o/n): ").strip().lower() == "o"

            # Corps du message
            if html_mode:
                message = f"""
                <html>
                <body>
                    <h1>Test du connecteur Gmail</h1>
                    <p>Ceci est un message de test envoyé depuis le connecteur Gmail.</p>
                    <p>Date et heure: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
                    <hr>
                    <p><em>Message généré automatiquement</em></p>
                </body>
                </html>
                """
            else:
                message = f"""
                Test du connecteur Gmail
                ======================
                
                Ceci est un message de test envoyé depuis le connecteur Gmail.
                Date et heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                
                --
                Message généré automatiquement
                """

            # Envoi de l'email
            logger.info(f"Envoi d'un email à {recipient}...")
            with gmail.connection():
                result = gmail.send_message(
                    message=message,
                    recipient=recipient,
                    subject=subject,
                    from_name="Connecteur Gmail",
                    html=html_mode,
                )

                logger.info(f"✅ Email envoyé avec succès: {result}")

                # Afficher les métriques
                metrics = gmail.get_metrics_summary()
                logger.info(f"Métriques: {metrics}")
        else:
            logger.error("❌ Échec de la connexion à Gmail")

    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return 1

    logger.info("Terminé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
