import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities_state():
    # Keep tests isolated because the app stores data in-memory.
    original_state = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(original_state)


client = TestClient(app)


def test_root_redirects_to_static_index():
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_map():
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert "Chess Club" in payload


def test_signup_for_activity_success():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    encoded_name = quote(activity_name, safe="")

    # Act
    response = client.post(f"/activities/{encoded_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_not_found():
    # Arrange

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_for_activity_duplicate_student():
    # Arrange
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]
    encoded_name = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{encoded_name}/signup", params={"email": existing_email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_unregister_participant_success():
    # Arrange
    activity_name = "Programming Class"
    email = activities[activity_name]["participants"][0]
    encoded_name = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_unregister_participant_not_found_for_activity():
    # Arrange
    activity_name = "Chess Club"
    email = "absent.student@mergington.edu"
    encoded_name = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"


def test_unregister_participant_activity_not_found():
    # Arrange

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/participants",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
