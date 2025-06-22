#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example script demonstrating OAuth 2.0 authentication with Gmail.

This script shows how to:
1. Set up OAuth 2.0 for Gmail
2. Send an email using OAuth authentication
3. Read emails using OAuth authentication

Prerequisites:
1. Create a Google Cloud project: https://console.cloud.google.com/
2. Enable the Gmail API in your project
3. Create OAuth 2.0 credentials (Client ID and Client Secret)
4. Obtain a refresh token (this script helps with that)
"""

import os
import sys
import logging
import webbrowser
from dotenv import load_dotenv
import json
from datetime import datetime
import argparse
from tabulate import tabulate

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("oauth_gmail.log")],
)
logger = logging.getLogger(__name__)

# Import connectors
try:
    from connectors import create_connector
    from connectors.messaging.oauth_utils import OAuth2Manager, generate_gmail_oauth_config
except ImportError as e:
    logger.error(f"Failed to import connector: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Constants
TOKEN_FILE = os.path.expanduser("~/.gmail_oauth_token.json")
SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
]


def setup_oauth_configuration():
    """
    Configure OAuth 2.0 credentials interactively.
    """
    print("\n=== OAuth 2.0 Configuration for Gmail ===\n")

    # Get credentials from environment or user input
    client_id = os.getenv("GOOGLE_CLIENT_ID") or input("Enter OAuth Client ID: ")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or input("Enter OAuth Client Secret: ")
    email = os.getenv("GMAIL_USERNAME") or input("Enter Gmail address: ")

    if not client_id or not client_secret or not email:
        logger.error("Client ID, Client Secret, and Gmail address are required")
        sys.exit(1)

    # Initialize OAuth manager
    oauth_manager = OAuth2Manager(
        client_id=client_id, client_secret=client_secret, scopes=SCOPES, token_file=TOKEN_FILE
    )

    # Check if we already have tokens
    try:
        if os.path.exists(TOKEN_FILE):
            oauth_manager._load_credentials_from_file()
            if oauth_manager.credentials and not oauth_manager.credentials.expired:
                logger.info(f"Loaded valid credentials from {TOKEN_FILE}")
                return {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": oauth_manager.credentials.refresh_token,
                    "access_token": oauth_manager.credentials.token,
                    "email": email,
                }
    except Exception as e:
        logger.warning(f"Error loading existing token: {e}")

    # If we don't have valid tokens, get new ones
    print("\nYou need to authorize this application to access your Gmail account.")
    print("A browser window will open. Please log in and grant access.")

    # Generate authorization URL
    auth_url = oauth_manager.generate_oauth_url()
    print(f"\nAuthorization URL: {auth_url}")

    # Open browser automatically if possible
    try:
        webbrowser.open(auth_url)
    except Exception:
        print("Please copy and paste the URL into your browser.")

    # Get authorization code from user
    auth_code = input("\nEnter the authorization code from the browser: ")

    # Exchange code for tokens
    tokens = oauth_manager.get_token_from_code(auth_code)

    # Save credentials
    logger.info(f"Successfully obtained OAuth tokens")

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": tokens["refresh_token"],
        "access_token": tokens["access_token"],
        "email": email,
    }


def send_email_with_oauth(oauth_config):
    """
    Send an email using Gmail with OAuth 2.0 authentication.
    """
    try:
        # Create Gmail SMTP connector with OAuth
        gmail_connector = create_connector(
            "gmail",
            {
                "username": oauth_config["email"],
                "use_oauth": True,
                "oauth": {
                    "client_id": oauth_config["client_id"],
                    "client_secret": oauth_config["client_secret"],
                    "refresh_token": oauth_config["refresh_token"],
                    "access_token": oauth_config["access_token"],
                },
            },
        )

        # Connect to Gmail
        gmail_connector.connect()
        logger.info("Connected to Gmail SMTP using OAuth 2.0")

        # Prepare email content
        recipient = input("\nEnter recipient email address: ")
        subject = input("Enter email subject: ")
        body = input("Enter email message (plain text): ")

        # Send email
        gmail_connector.send_message(
            body,
            recipient,
            subject=subject,
            sender_name="OAuth Test",
            html_content=f"<h2>{subject}</h2><p>{body}</p><p>Sent with OAuth 2.0 authentication!</p>",
        )

        logger.info(f"Email sent successfully to {recipient}")

    except Exception as e:
        logger.error(f"Error sending email: {e}")
    finally:
        # Disconnect
        if "gmail_connector" in locals() and gmail_connector._connected:
            gmail_connector.disconnect()
            logger.info("Disconnected from Gmail SMTP")


def read_emails_with_oauth(oauth_config):
    """
    Read emails using Gmail IMAP with OAuth 2.0 authentication.
    """
    try:
        # Create Gmail IMAP connector with OAuth
        gmail_connector = create_connector(
            "gmail_imap",
            {
                "username": oauth_config["email"],
                "use_oauth": True,
                "oauth": {
                    "client_id": oauth_config["client_id"],
                    "client_secret": oauth_config["client_secret"],
                    "refresh_token": oauth_config["refresh_token"],
                    "access_token": oauth_config["access_token"],
                },
            },
        )

        # Connect to Gmail
        gmail_connector.connect()
        logger.info("Connected to Gmail IMAP using OAuth 2.0")

        # List available labels (folders/mailboxes)
        labels = gmail_connector.get_all_labels()
        logger.info(f"Available labels: {', '.join(labels[:10])}...")

        # Let user choose a label
        selected_label = input(f"\nEnter label to read from (default: INBOX): ") or "INBOX"

        # Select mailbox
        num_messages = gmail_connector.select_mailbox(selected_label)
        logger.info(f"Selected '{selected_label}' with {num_messages} messages")

        # Get email limit from user
        limit = int(input(f"\nHow many emails to display (default: 5): ") or "5")

        # Read emails
        messages = gmail_connector.receive_messages(
            mailbox=selected_label, limit=limit, newest_first=True, unread_only=False
        )

        # Display results
        if not messages:
            logger.info(f"No messages found in '{selected_label}'")
            return

        # Display emails in a table
        table_data = []
        for msg in messages:
            table_data.append(
                [
                    msg["id"],
                    msg["date"],
                    msg["from"][:40] + ("..." if len(msg["from"]) > 40 else ""),
                    msg["subject"][:40] + ("..." if len(msg["subject"]) > 40 else ""),
                    "✓" if msg["has_attachments"] else "",
                ]
            )

        print(
            tabulate(
                table_data,
                headers=["ID", "Date", "From", "Subject", "Attachments"],
                tablefmt="pretty",
            )
        )

    except Exception as e:
        logger.error(f"Error reading emails: {e}")
    finally:
        # Disconnect
        if "gmail_connector" in locals() and gmail_connector._connected:
            gmail_connector.disconnect()
            logger.info("Disconnected from Gmail IMAP")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Gmail OAuth 2.0 Example")
    parser.add_argument("--setup", action="store_true", help="Setup OAuth credentials")
    parser.add_argument("--send", action="store_true", help="Send an email using OAuth")
    parser.add_argument("--read", action="store_true", help="Read emails using OAuth")

    args = parser.parse_args()

    # If no arguments, show help
    if not (args.setup or args.send or args.read):
        print("Gmail OAuth 2.0 Example\n")
        print("Available options:")
        print("  --setup  Setup OAuth credentials")
        print("  --send   Send an email using OAuth")
        print("  --read   Read emails using OAuth")
        print("\nExample: python example_oauth_gmail.py --setup --send")
        return

    # Setup OAuth if requested or if no token file exists
    oauth_config = None
    if args.setup or not os.path.exists(TOKEN_FILE):
        oauth_config = setup_oauth_configuration()
    else:
        # Load existing configuration
        try:
            with open(TOKEN_FILE, "r") as f:
                token_data = json.load(f)

            oauth_config = {
                "client_id": token_data.get("client_id"),
                "client_secret": token_data.get("client_secret"),
                "refresh_token": token_data.get("refresh_token"),
                "access_token": token_data.get("access_token"),
                "email": os.getenv("GMAIL_USERNAME") or input("Enter Gmail address: "),
            }
            logger.info(f"Loaded OAuth configuration from {TOKEN_FILE}")
        except Exception as e:
            logger.error(f"Error loading OAuth configuration: {e}")
            oauth_config = setup_oauth_configuration()

    # Send email if requested
    if args.send:
        send_email_with_oauth(oauth_config)

    # Read emails if requested
    if args.read:
        read_emails_with_oauth(oauth_config)


if __name__ == "__main__":
    main()
