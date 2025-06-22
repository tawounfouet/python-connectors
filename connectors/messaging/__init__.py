"""
Connecteurs de messagerie.

Ce module fournit des connecteurs pour différents systèmes de messagerie,
permettant l'envoi et la réception de messages.
"""

from .smtp import SMTPConnector, GmailConnector

__all__ = ["SMTPConnector", "GmailConnector"]
