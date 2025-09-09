# Façade "M" (Models) en MVT.
# On expose les types/Helpers (métier) et les cas d’usage. La couche Models est autonome.
from .auth import AuthResponse, build_user_dict, build_session_dict, make_auth_response
from .usecases_auth import (
    sign_in,
    sign_up,
    send_reset_email,
    update_password,
)
from .supabase import (
    sign_in_password,
    sign_up_account,
    send_reset_password,
    update_user_password,
)
from .offres import (
    fetch_offres,
    fetch_admin_commandes,
    fetch_user_commandes,
    get_offre,
    create_offre,
    update_offre,
    delete_offre,
)
from .health import health_supabase_info
from .payments import (
    require_stripe,
    create_session,
    parse_event,
    extract_metadata,
    get_session,
    extract_metadata_from_session,
    process_cart_purchase,
    confirm_session_by_id,  # ajouter ceci
)
from .payments_cart import (
    aggregate_quantities,
    get_offers_map,
    to_line_items,
    make_metadata,
)

__all__ = [
    # Modèles/Helpers
    "AuthResponse",
    "build_user_dict",
    "build_session_dict",
    "make_auth_response",
    # Cas d’usage
    "sign_in",
    "sign_up",
    "send_reset_email",
    "update_password",
    # Accès bas niveau (si besoin)
    "sign_in_password",
    "sign_up_account",
    "send_reset_password",
    "update_user_password",
    # Offres/Commandes
    "fetch_offres",
    "fetch_admin_commandes",
    "fetch_user_commandes",
    "get_offre",
    "create_offre",
    "update_offre",
    "delete_offre",
    # Health
    "health_supabase_info",
    # Payments
    "require_stripe",
    "create_session",
    "parse_event",
    "extract_metadata",
    "get_session",
    "extract_metadata_from_session",
    "aggregate_quantities",
    "get_offers_map",
    "to_line_items",
    "make_metadata",
    "process_cart_purchase",
    "confirm_session_by_id",  # et ceci
]