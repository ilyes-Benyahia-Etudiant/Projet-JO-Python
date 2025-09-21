from backend.validation.repository import get_ticket_by_token, get_last_validation, insert_validation
from typing import Tuple, Dict, Any, Optional

class ValidationError(Exception):
    def __init__(self, message: str, code: str = "invalid"):
        super().__init__(message)
        self.code = code

def validate_ticket_token(token: str, admin_id: str, admin_token: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Valide un billet à partir d'une clé scannée.
    Exige la clé composite 'user_key.token_achat'.
    Retourne l'un des statuts: 'validated', 'already_validated', 'not_found', 'invalid'.
    """
    provided_user_key: Optional[str] = None
    raw = (token or "").strip().strip('"').strip("'")

    # Exiger le token composite "user_key.token"
    if "." not in raw:
        return ("invalid", {"message": "Clé utilisateur requise", "reason": "user_key_required"})

    parts = raw.split(".", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return ("invalid", {"message": "Format de clé invalide", "reason": "invalid_composite_token"})

    provided_user_key = parts[0].strip().strip('"').strip("'")
    raw_token = parts[1].strip().strip('"').strip("'")
    if not provided_user_key or not raw_token:
        return ("invalid", {"message": "Format de clé invalide", "reason": "invalid_composite_token"})

    ticket = get_ticket_by_token(raw_token)
    if not ticket:
        return ("not_found", {"message": "Billet introuvable", "reason": "ticket_not_found"})

    # Vérification stricte de la clé utilisateur (users.bio)
    stored_user_key = ((ticket.get("users") or {}).get("bio") or "").strip()
    if not stored_user_key or stored_user_key != provided_user_key:
        return ("invalid", {"message": "Clé utilisateur invalide", "reason": "user_key_mismatch"})

    created = insert_validation(token=raw_token, commande_id=ticket["id"], admin_id=admin_id, status="validated", user_token=admin_token)
    if created is None:
        # Doublon (déjà validé)
        last = get_last_validation(raw_token)
        return ("already_validated", {
            "token": raw_token,
            "commande_id": ticket["id"],
            "offre": ticket.get("offres"),
            "user": ticket.get("users"),
            "validation": last or None
        })

    last = get_last_validation(raw_token)
    if last:
        return ("validated", {
            "token": raw_token,
            "commande_id": ticket["id"],
            "offre": ticket.get("offres"),
            "user": ticket.get("users"),
            "validation": last
        })
    return ("Scanned", {"token": raw_token})