import pytest
from unittest.mock import patch, MagicMock
from backend.payments.repository import insert_commande_with_token

def test_insert_commande_with_token():
    # Arrange
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = {"data": [{"id": "123"}]}

    user_id = "user-123"
    offre_id = "offre-456"
    token = "token-789"
    price_paid = "10.00"
    user_token = "jwt-token-xyz"

    # Act
    with patch("backend.infra.supabase_client.get_user_supabase", return_value=mock_client) as mock_get_user_supabase:
        result = insert_commande_with_token(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid, user_token=user_token)

    # Assert
    mock_get_user_supabase.assert_called_once_with(user_token)
    mock_client.table.assert_called_once_with("commandes")
    mock_table.insert.assert_called_once_with({"user_id": user_id, "offre_id": offre_id, "token": token, "price_paid": price_paid})
    mock_insert.execute.assert_called_once()
    assert result == {"status": "ok"}

def test_insert_commande_with_token_exception():
    # Arrange
    user_id = "user-123"
    offre_id = "offre-456"
    token = "token-789"
    price_paid = "10.00"
    user_token = "jwt-token-xyz"

    # Act
    # Simule une erreur côté get_user_supabase (ou dans la chaîne d'appel)
    with patch("backend.infra.supabase_client.get_user_supabase", side_effect=Exception("Test exception")):
        result = insert_commande_with_token(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid, user_token=user_token)

    # Assert
    assert result is None