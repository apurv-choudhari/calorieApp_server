import pytest
from app import app, mongo
from flask import url_for
from datetime import datetime

# Mock daily challenges
DAILY_CHALLENGES = [
    "Drink 8 glasses of water", "Walk 5,000 steps", "Avoid sugary drinks",
    "Eat at least 3 servings of vegetables", "Complete a 15-minute meditation",
    "Do a 30-minute workout", "Sleep for at least 7 hours"
]


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['email'] = "testuser@example.com"

        # Insert mock user data into MongoDB
        mongo.db.users.insert_one({
            "email": "testuser@example.com",
            "completed_challenges": {}
        })

        yield client

        # Cleanup the mock data
        mongo.db.users.delete_one({"email": "testuser@example.com"})


def test_daily_challenges_render(client):
    """Test that daily challenges render correctly on the page."""
    response = client.get(url_for('daily_challenge'))
    assert response.status_code == 200
    for challenge in DAILY_CHALLENGES[:
                                      3]:  # Assuming 3 daily challenges are displayed
        assert challenge.encode() in response.data


def test_mark_challenge_completed(client):
    """Test marking a daily challenge as completed."""
    today = datetime.today().strftime('%Y-%m-%d')
    challenge_to_complete = DAILY_CHALLENGES[0]

    response = client.post(url_for('daily_challenge'),
                           data={"completed_challenge": challenge_to_complete})

    # Verify the challenge is marked as completed in the database
    user_data = mongo.db.users.find_one({"email": "testuser@example.com"})
    completed_key = f"{today}_{challenge_to_complete}"
    assert user_data["completed_challenges"].get(completed_key) == True
    assert response.status_code == 302  # Check for redirect after completing the challenge


def test_shareable_message_when_all_challenges_completed(client):
    """Test the shareable message appears when all challenges are completed."""
    today = datetime.today().strftime('%Y-%m-%d')
    challenges = DAILY_CHALLENGES[:
                                  3]  # Assuming the first 3 are displayed as daily challenges

    # Mark all challenges as completed
    for challenge in challenges:
        client.post(url_for('daily_challenge'),
                    data={"completed_challenge": challenge})

    response = client.get(url_for('daily_challenge'))

    # Check if the shareable message is present in the page content
    shareable_message = "I completed all my daily challenges today! Feeling great and staying on track with #CalorieApp."
    assert shareable_message.encode() in response.data
