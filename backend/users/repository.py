"""Couche d’accès aux données (Supabase) pour le domaine Utilisateurs.
Contient les fonctions de lecture/écriture sur les tables users, commandes, offres.
Les exceptions sont « catchées » et transforment les résultats en valeurs neutres ([], None, False) afin de ne pas casser l’UX.
"""
from typing import Any, Dict, List, Optional
from backend.infra.supabase_client import get_supabase, get_service_supabase

def get_user_orders(user_id: str) -> List[Dict[str, Any]]:
    """Retourne les commandes de l’utilisateur, jointes avec les infos d’offre.
    - Table: commandes
    - Select: id, token, price_paid, created_at, offre_id, offres(title, price)
    - Filtre: eq(user_id, <id>) et tri desc(created_at)
    - En cas d’erreur: liste vide
    """
    # Remplacer par la logique locale si besoin
    # ... déjà défini dans ce fichier ...
    # Sert les commandes de l'utilisateur avec la jointure vers offres(title, price)
    if not user_id:
        return []
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, price_paid, created_at, offre_id, offres(title, price)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def get_offers() -> List[Dict[str, Any]]:
    """Liste les offres disponibles pour l’UI publique et /session.
    - Table: offres
    - Tri: price asc (si la colonne existe)
    - En cas d’erreur: liste vide
    """
    # ... déjà défini dans ce fichier ...
    # Récupère les offres disponibles (triées par prix croissant si la colonne existe)
    try:
        res = (
            get_supabase()
            .table("offres")
            .select("*")
            .order("price", desc=False)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def get_user_by_email(email: str) -> Optional[dict]:
    """Récupère un utilisateur par email (table users).
    - Retour: dict utilisateur ou None si introuvable/erreur
    """
    try:
        res = get_supabase().table("users").select("*").eq("email", email).single().execute()
        return res.data or None
    except Exception:
        return None

def upsert_user_profile(user_id: str, email: str, role: Optional[str] = None, bio: Optional[str] = None) -> bool:
    """Crée ou met à jour le profil utilisateur (table users) via la clé de service.
    - Utilise get_service_supabase() pour bypasser les policies RLS sur certaines opérations serveur.
    - Champs écrits: id (si fourni), email, role (optionnel), bio (optionnel)
    - Retour: True si succès, False sinon
    """
    if not email and not user_id:
        return False
    payload: Dict[str, Any] = {"email": email}
    if user_id:
        payload["id"] = user_id
    if role:
        payload["role"] = role
    if bio:
        payload["bio"] = bio
    try:
        get_service_supabase().table("users").upsert(payload).execute()
        return True
    except Exception:
        return False

def get_user_by_id(user_id: str) -> Optional[dict]:
    """Récupère un utilisateur par id (table users).
    - Retour: dict utilisateur ou None si introuvable/erreur
    """
    if not user_id:
        return None
    try:
        res = get_supabase().table("users").select("*").eq("id", user_id).single().execute()
        return res.data or None
    except Exception:
        return None