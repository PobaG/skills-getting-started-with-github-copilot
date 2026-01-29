"""
Tests for the FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state after each test"""
    # Store original state
    original = {k: {"participants": v["participants"].copy()} for k, v in activities.items()}
    yield
    # Restore original state
    for activity_name, activity_data in activities.items():
        activity_data["participants"] = original[activity_name]["participants"]


class TestGetActivities:
    """Test GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that GET /activities returns all expected activities"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert "Debate Team" in data
        assert "Art Club" in data
        assert "Programming Class" in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Test POST /activities/{activity_name}/signup endpoint"""

    def test_signup_with_valid_data_returns_200(self, client, reset_activities):
        """Test successful signup returns status 200"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup adds participant to activity"""
        email = "newstudent@mergington.edu"
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 200
        assert len(activities["Chess Club"]["participants"]) == initial_count + 1
        assert email in activities["Chess Club"]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signup to nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        """Test that duplicate signup returns 400"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_response_message(self, client, reset_activities):
        """Test signup response message"""
        email = "newstudent@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]


class TestUnregister:
    """Test DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_with_valid_data_returns_200(self, client, reset_activities):
        """Test successful unregister returns status 200"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes participant from activity"""
        email = "michael@mergington.edu"
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregister from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_nonexistent_participant_returns_404(self, client, reset_activities):
        """Test that unregister of nonexistent participant returns 404"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"]

    def test_unregister_response_message(self, client, reset_activities):
        """Test unregister response message"""
        email = "michael@mergington.edu"
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]


class TestRoot:
    """Test GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
