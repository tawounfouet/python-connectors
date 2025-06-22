#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example script for more advanced IMAP search operations.
This script demonstrates how to filter emails with various criteria.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from tabulate import tabulate
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import connectors
try:
    from connectors import create_connector
except ImportError as e:
    logger.error(f"Failed to import connector: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()


def search_emails(criteria=None, is_gmail=False):
    """
    Search and filter emails using more advanced criteria.

    Args:
        criteria: Dictionary of search criteria
        is_gmail: Whether to use Gmail IMAP or generic IMAP
    """
    if criteria is None:
        criteria = {"unread_only": True, "limit": 5}

    if is_gmail:
        # Configuration for Gmail IMAP
        config = {
            "username": os.getenv("GMAIL_USERNAME", "user@gmail.com"),
            "password": os.getenv("GMAIL_PASSWORD", "app_password"),
        }
        connector_name = "gmail_imap"
        logger.info("Using Gmail IMAP connector")
    else:
        # Configuration for general IMAP
        config = {
            "host": os.getenv("IMAP_HOST", "imap.example.com"),
            "port": int(os.getenv("IMAP_PORT", "993")),
            "username": os.getenv("IMAP_USERNAME", "user@example.com"),
            "password": os.getenv("IMAP_PASSWORD", "password"),
            "use_ssl": True,
        }
        connector_name = "imap"
        logger.info("Using standard IMAP connector")

    # Add default mailbox
    mailbox = criteria.get("mailbox", "INBOX")

    try:
        # Create connector instance
        imap_connector = create_connector(connector_name, config)

        # Connect to server
        imap_connector.connect()
        logger.info(f"Connected to {connector_name}")

        # Select mailbox
        num_messages = imap_connector.select_mailbox(mailbox)
        logger.info(f"Selected mailbox '{mailbox}' with {num_messages} messages")

        # Get messages with criteria
        messages = imap_connector.receive_messages(
            mailbox=mailbox,
            limit=criteria.get("limit", 10),
            unread_only=criteria.get("unread_only", False),
            newest_first=criteria.get("newest_first", True),
        )

        if not messages:
            logger.info(f"No messages found matching your criteria")
            return

        # Display messages in a table
        table_data = []
        for msg in messages:
            table_data.append(
                [
                    msg["id"],
                    msg["date"],
                    msg["from"][:40] + ("..." if len(msg["from"]) > 40 else ""),
                    msg["subject"][:30] + ("..." if len(msg["subject"]) > 30 else ""),
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

        # If we want to demonstrate how to mark emails as read
        if criteria.get("mark_as_read", False) and messages:
            # Get IDs of all fetched messages
            email_ids = [msg["id"] for msg in messages]
            logger.info(f"Marking {len(email_ids)} emails as read...")
            imap_connector.mark_as_read(email_ids, mailbox)
            logger.info("Emails marked as read")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Ensure we disconnect properly
        if "imap_connector" in locals() and imap_connector._connected:
            imap_connector.disconnect()
            logger.info("Disconnected from server")


def main():
    parser = argparse.ArgumentParser(description="Search emails with IMAP")
    parser.add_argument(
        "--gmail", action="store_true", help="Use Gmail IMAP instead of standard IMAP"
    )
    parser.add_argument("--unread", action="store_true", help="Show only unread messages")
    parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of messages to retrieve"
    )
    parser.add_argument("--mark-read", action="store_true", help="Mark retrieved emails as read")
    parser.add_argument("--mailbox", default="INBOX", help="Mailbox to search in")

    args = parser.parse_args()

    # Build search criteria from arguments
    criteria = {
        "unread_only": args.unread,
        "limit": args.limit,
        "mailbox": args.mailbox,
        "mark_as_read": args.mark_read,
        "newest_first": True,
    }

    # Display search parameters
    print(f"Searching emails with the following criteria:")
    for key, value in criteria.items():
        print(f"  - {key}: {value}")
    print()

    # Execute the search
    search_emails(criteria, args.gmail)


if __name__ == "__main__":
    main()
