from typing import Optional, Dict, Any

class AuthResponse:
    def __init__(
        self,
        success: bool,
        user: Optional[Dict[str, Any]] = None,
        session: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.user = user
        self.session = session
        self.error = error
    # Propriétés pour compatibilité avec le routeur
    @property
    def access_token(self):
        return (self.session or {}).get("access_token")

    @property
    def refresh_token(self):
        return (self.session or {}).get("refresh_token")