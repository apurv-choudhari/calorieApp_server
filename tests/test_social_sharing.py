import pytest
from app import app, mongo  # Adjust if app is imported from another module
from flask import url_for
from urllib.parse import urlencode


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['email'] = "testuser@example.com"  # Mock user session

        # Insert mock user data into MongoDB
        mongo.db.users.insert_one({
            "email": "testuser@example.com",
            "completed_challenges": {
                "2024-11-01_SomeChallenge": True
            }
        })

        yield client

        # Cleanup the mock data
        mongo.db.users.delete_one({"email": "testuser@example.com"})


def test_sharing_buttons_render(client):
    """Test that the sharing buttons are rendered on the friends page."""
    response = client.get(url_for('friends'))
    assert b'Share on Twitter' in response.data
    assert b'Share on Facebook' in response.data
    assert b'Share on LinkedIn' in response.data


def test_share_link_structure(client):
    """Test that the share links contain the correct message and format."""
    share_message = "Burning 500 calories daily to stay on track with #CalorieApp"

    # Expected URLs for social sharing
    twitter_url = f"https://twitter.com/intent/tweet?text={urlencode({'text': share_message})}"
    facebook_url = f"https://www.facebook.com/sharer/sharer.php?u=https://calorieapp.com&quote={urlencode({'quote': share_message})}"

    response = client.get(url_for('friends'))
    assert twitter_url.encode() in response.data
    assert facebook_url.encode() in response.data


def test_log_share_action(client):
    """Test the /api/share endpoint for logging a share action."""
    response = client.post(url_for('log_share'), json={"platform": "Twitter"})
    assert response.status_code == 200
    assert response.json["status"] == "success"
