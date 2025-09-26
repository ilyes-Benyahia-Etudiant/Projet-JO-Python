# Module-level imports & constants
from locust import HttpUser, task, between
import os
import csv
import threading
from urllib.parse import urlparse  # <-- [NOUVEAU]
COOKIE_NAME = "sb_access"  # <-- [NOUVEAU]

_CREDENTIALS: list[tuple[str, str]] = []
_CRED_LOCK = threading.Lock()
_CRED_IDX = 0

def _ensure_credentials_loaded():
    global _CREDENTIALS
    if _CREDENTIALS:
        return
    csv_path = os.path.join(os.path.dirname(__file__), "users.csv")
    if os.path.exists(csv_path):
        # Essaye d'abord avec DictReader (nécessite en-têtes email,password)
        with open(csv_path, newline="", encoding="utf-8") as f:
            sample = f.read().splitlines()
        if sample:
            header = sample[0].lower()
            if "email" in header and "password" in header:
                with open(csv_path, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email = (row.get("email") or "").strip()
                        password = (row.get("password") or "").strip()
                        if email and password:
                            _CREDENTIALS.append((email, password))
            else:
                # Fallback: CSV sans en-tête, lignes "email,password"
                for line in sample:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2 and "@" in parts[0]:
                        _CREDENTIALS.append((parts[0], parts[1]))
    if not _CREDENTIALS:
        env_email = os.getenv("LOCUST_EMAIL", "").strip()
        env_password = os.getenv("LOCUST_PASSWORD", "").strip()
        if env_email and env_password:
            _CREDENTIALS.append((env_email, env_password))
    if not _CREDENTIALS and not os.getenv("LOCUST_BEARER", "").strip():
        raise RuntimeError("Fournissez des identifiants via tests/load/users.csv (email,password), "
                           "variables d’environnement LOCUST_EMAIL/LOCUST_PASSWORD, "
                           "ou un token via LOCUST_BEARER.")

def _next_credential() -> tuple[str, str]:
    global _CRED_IDX
    with _CRED_LOCK:
        cred = _CREDENTIALS[_CRED_IDX % len(_CREDENTIALS)]
        _CRED_IDX += 1
        return cred

class WebsiteUser(HttpUser):
    wait_time = between(0.5, 2.0)

    # Helpers pour le cookie de session
    def _cookie_domain(self) -> str:
        try:
            host = getattr(self.environment, "host", "") or ""
            return urlparse(host).hostname or "127.0.0.1"
        except Exception:
            return "127.0.0.1"

    def _set_session_cookie(self, token: str):
        domain = self._cookie_domain()
        try:
            # Dépose le cookie attendu par le backend
            self.client.cookies.set(COOKIE_NAME, token, domain=domain, path="/")
        except Exception:
            # Fallback sans domaine
            self.client.cookies.set(COOKIE_NAME, token, path="/")

    def on_start(self):
        self.auth_headers = {"Accept": "application/json"}
        bearer = os.getenv("LOCUST_BEARER", "").strip()

        if bearer:
            # Bypass login avec Bearer
            self.auth_headers["Authorization"] = f"Bearer {bearer}"
            self._set_session_cookie(bearer)  # <-- [NOUVEAU] assure le cookie sb_access
            me = self.client.get("/api/v1/auth/me", name="GET /api/v1/auth/me", headers=self.auth_headers)
            if me.status_code != 200:
                # Bearer invalide: bascule sur login si identifiants dispo
                self.auth_headers.pop("Authorization", None)
                _ensure_credentials_loaded()
                self.email, self.password = _next_credential()
                self._login()
        else:
            _ensure_credentials_loaded()
            self.email, self.password = _next_credential()
            self._login()

    def _login(self):
        with self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            headers={"Accept": "application/json"},
            name="POST /api/v1/auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Login failed ({resp.status_code}): {resp.text[:200]}")
                return
            try:
                data = resp.json()
                token = data.get("access_token")
            except Exception:
                token = None
            if not token:
                resp.failure("Login ok mais 'access_token' manquant dans la réponse")
                return

            # Auth côté API + cookie session côté pages protégées
            self.auth_headers["Authorization"] = f"Bearer {token}"
            self._set_session_cookie(token)  # <-- [NOUVEAU]

            me = self.client.get("/api/v1/auth/me", name="GET /api/v1/auth/me", headers=self.auth_headers)
            if me.status_code != 200:
                resp.failure(f"Login session not active, /auth/me => {me.status_code}: {me.text[:200]}")
            else:
                resp.success()

    @task
    def auth_then_session(self):
        # Public
        self.client.get("/api/v1/evenements", name="GET /api/v1/evenements", headers=self.auth_headers)
        # Protégé (nécessite Bearer ou cookie sb_access)
        if "Authorization" in self.auth_headers:
            self.client.get("/session", name="GET /session", headers=self.auth_headers)
        else:
            # Si pas authentifié, éviter de spammer des 401
            pass