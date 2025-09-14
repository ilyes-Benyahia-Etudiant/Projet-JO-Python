# Façade "M" (Models) en MVT.
# On expose les types/Helpers (métier) et les cas d’usage. La couche Models est autonome.
from .supabase import (
    sign_in_password,
    sign_up_account,
    send_reset_password,
    update_user_password,
)

# Expose uniquement les fonctions “public/user” via db
from .db import (
    fetch_offres,
    fetch_user_commandes,
)
from backend.health.service import health_supabase_info

# Shim de compatibilité pour les tests existants (conftest.py)
from backend.payments.stripe_client import require_stripe

# Compatibilité Payments (réexport vers backend.payments.*)
from backend.config import CHECKOUT_SUCCESS_PATH, CHECKOUT_CANCEL_PATH
from backend.payments import (
    to_line_items,
    get_offers_map,
    process_cart_purchase,
    extract_metadata,
    extract_metadata_from_session,
    make_metadata,
)
from backend.payments.stripe_client import (
    create_session as _payments_create_session,
    get_session as get_session,
    parse_event as parse_event,
)

def create_session(base_url: str, line_items, metadata):
    """
    Wrapper legacy (ancien backend.models.payments.create_session):
    - construit success_url et cancel_url depuis base_url + CHECKOUT_*_PATH
    - appelle le client Stripe moderne en mode 'payment'
    """
    sep = "&" if "?" in CHECKOUT_SUCCESS_PATH else "?"
    success_url = f"{base_url}{CHECKOUT_SUCCESS_PATH}{sep}session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}{CHECKOUT_CANCEL_PATH}"
    return _payments_create_session(
        line_items=line_items,
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )

__all__ = [
    # Accès bas niveau
    "sign_in_password",
    "sign_up_account",
    "send_reset_password",
    "update_user_password",
    # Public/catalog
    "fetch_offres",
    "fetch_user_commandes",
    # Health
    "health_supabase_info",
    # Payments (compat tests)
    "require_stripe",
    "create_session",
    "parse_event",
    "get_offers_map",
    "to_line_items",
    "process_cart_purchase",
    "extract_metadata",
    "extract_metadata_from_session",
    "make_metadata",
    "get_session",
]
