#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example script for IMAP connector.
This script demonstrates how to use the IMAP connector to list emails.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from tabulate import tabulate
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import connectors
try:
    from connectors import get_connector, create_connector
except ImportError as e:
    logger.error(f"Failed to import connector: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()


def list_emails_with_imap():
    """List emails using IMAP connector."""
    # Configuration for general IMAP server
    imap_config = {
        "host": os.getenv("IMAP_HOST", "imap.example.com"),
        "port": int(os.getenv("IMAP_PORT", "993")),
        "username": os.getenv("IMAP_USERNAME", "user@example.com"),
        "password": os.getenv("IMAP_PASSWORD", "password"),
        "use_ssl": True,  # Default to SSL
        "mailbox": "INBOX",  # Default mailbox to read from
    }

    try:
        # Create connector instance
        imap_connector = create_connector("imap", imap_config)

        # Connect to IMAP server
        imap_connector.connect()
        logger.info("Connected to IMAP server.")

        # List available mailboxes
        mailboxes = imap_connector.list_mailboxes()
        logger.info(f"Available mailboxes: {', '.join(mailboxes)}")

        # Select mailbox
        mailbox = imap_config["mailbox"]
        num_messages = imap_connector.select_mailbox(mailbox)
        logger.info(f"Selected mailbox '{mailbox}' with {num_messages} messages")

        # Get latest 10 messages
        messages = imap_connector.receive_messages(
            mailbox=mailbox, limit=10, newest_first=True, unread_only=False
        )

        if not messages:
            logger.info(f"No messages found in '{mailbox}'")
            return

        # Display messages in a table
        table_data = []
        for msg in messages:
            table_data.append(
                [
                    msg["id"],
                    msg["date"],
                    msg["from"],
                    msg["subject"][:50] + ("..." if len(msg["subject"]) > 50 else ""),
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
        logger.error(f"Error: {e}")
    finally:
        # Ensure we disconnect properly
        if "imap_connector" in locals() and imap_connector._connected:
            imap_connector.disconnect()
            logger.info("Disconnected from IMAP server.")


def list_emails_with_gmail():
    """List emails using Gmail IMAP connector."""
    # Configuration for Gmail IMAP server
    gmail_config = {
        "username": os.getenv("GMAIL_USERNAME", "user@gmail.com"),
        "password": os.getenv("GMAIL_PASSWORD", "app_password"),
        # No need to specify host/port as GmailIMAPConnector will set these
    }

    try:
        # Create connector instance
        gmail_connector = create_connector("gmail_imap", gmail_config)

        # Connect to Gmail
        gmail_connector.connect()
        logger.info("Connected to Gmail IMAP.")

        # List available labels (in Gmail, labels are equivalent to folders/mailboxes)
        labels = gmail_connector.get_all_labels()
        logger.info(f"Available Gmail labels: {', '.join(labels)}")

        # Select INBOX
        mailbox = "INBOX"
        num_messages = gmail_connector.select_mailbox(mailbox)
        logger.info(f"Selected mailbox '{mailbox}' with {num_messages} messages")

        # Get latest 10 messages
        messages = gmail_connector.receive_messages(
            mailbox=mailbox, limit=10, newest_first=True, unread_only=False
        )

        if not messages:
            logger.info(f"No messages found in '{mailbox}'")
            return

        # Display messages in a table
        table_data = []
        for msg in messages:
            table_data.append(
                [
                    msg["id"],
                    msg["date"],
                    msg["from"],
                    msg["subject"][:50] + ("..." if len(msg["subject"]) > 50 else ""),
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

        # Optionally, display the content of the first email
        if messages:
            first_email = messages[0]
            print("\nContent of the first email:")
            print(f"Subject: {first_email['subject']}")
            print(f"From: {first_email['from']}")
            print(f"To: {first_email['to']}")
            print(f"Date: {first_email['date']}")
            print("\nBody:")
            print(
                first_email["body"] or first_email["html"][:500] + "..."
                if len(first_email["html"]) > 500
                else first_email["html"]
            )

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Ensure we disconnect properly
        if "gmail_connector" in locals() and gmail_connector._connected:
            gmail_connector.disconnect()
            logger.info("Disconnected from Gmail IMAP.")


def main():
    print("=== IMAP Email Example ===")
    print("1. List emails with standard IMAP")
    print("2. List emails with Gmail IMAP")
    choice = input("Choose an option (1-2): ")

    if choice == "1":
        list_emails_with_imap()
    elif choice == "2":
        list_emails_with_gmail()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
