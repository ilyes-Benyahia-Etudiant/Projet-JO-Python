import json
from backend.utils import stripe_client as stripe_utils

def test_extract_metadata_ok():
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {
                    "user_id": "u1",
                    "cart": json.dumps([{"id":"1","quantity":2}]),
                }
            }
        }
    }
    user_id, cart = stripe_utils.extract_metadata(event)
    assert user_id == "u1"
    assert cart == [{"id":"1","quantity":2}]