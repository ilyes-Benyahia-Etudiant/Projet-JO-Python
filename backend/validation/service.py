from typing import Any, Dict, Tuple, Optional
from backend.validation.repository import get_ticket_by_token, get_last_validation, insert_validation

class ValidationError(Exception):
    def __init__(self, message: str, code: str = "invalid"):
        super().__init__(message)
        self.code = code

def validate_ticket_token(token: str, admin_id: str, admin_token: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Valide un billet à partir de son token. Retourne (status, payload)
    - status: "validated", "already_validated", "not_found", "error"
    - payload: détails billet et validation
    """
    ticket = get_ticket_by_token(token)
    if not ticket:
        return ("not_found", {"message": "Billet introuvable"})

    last = get_last_validation(token)
    if last and last.get("status") == "validated":
        return ("already_validated", {
            "ticket": ticket,
            "validation": last,
            "message": "Billet déjà validé",
        })

    created = insert_validation(token=token, commande_id=ticket["id"], admin_id=admin_id, status="validated", user_token=admin_token)
    if not created:
        return ("error", {"message": "Impossible d'enregistrer la validation"})

    return ("validated", {
        "ticket": ticket,
        "validation": created,
        "message": "Validation enregistrée",
    })