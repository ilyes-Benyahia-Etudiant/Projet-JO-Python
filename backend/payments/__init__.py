"""
Module 'payments' (feature-first): point d'entrée public.
Réunit logique panier, metadata Stripe, client Stripe, repository BD, et services.
"""

from .cart import aggregate_quantities, _price_from_offer, price_from_offer, make_metadata, to_line_items
from .metadata import extract_metadata, extract_metadata_from_session
from .stripe_client import require_stripe, create_session, get_session, parse_event
from .repository import (
    get_offers_map,
    insert_commande,
    insert_commande_with_token,
    insert_commande_service,
)
from .service import process_cart_purchase, confirm_session_by_id

__all__ = [
    # cart
    "aggregate_quantities",
    "price_from_offer",
    "_price_from_offer",
    "make_metadata",
    "to_line_items",
    # metadata
    "extract_metadata",
    "extract_metadata_from_session",
    # stripe
    "require_stripe",
    "create_session",
    "get_session",
    "parse_event",
    # repository
    "get_offers_map",
    "insert_commande",
    "insert_commande_with_token",
    "insert_commande_service",
    # services
    "process_cart_purchase",
    "confirm_session_by_id",
]