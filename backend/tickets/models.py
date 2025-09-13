from typing import List, Dict
from backend.tickets.repository import list_user_tickets

def fetch_user_tickets(user_id: str) -> List[Dict]:
    """
    Legacy shim: délègue désormais au repository.
    """
    return list_user_tickets(user_id)