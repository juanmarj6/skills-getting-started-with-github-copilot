from copy import deepcopy

import pytest


def test_root_redirects_to_frontend(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client, activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities
    assert activities
    for activity in response.json().values():
        assert {"description", "schedule", "max_participants", "participants"} <= activity.keys()
        assert isinstance(activity["participants"], list)


def test_signup_updates_activities(client, activities):
    email = "new-student@mergington.edu"
    expected = deepcopy(activities)
    expected["Chess Club"]["participants"].append(email)

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    updated = client.get("/activities").json()
    assert updated == expected
    assert updated["Chess Club"]["participants"].count(email) == 1


def test_duplicate_signup_preserves_activities(client, activities):
    expected = deepcopy(activities)
    email = activities["Chess Club"]["participants"][0]

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert client.get("/activities").json() == expected


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_unknown_activity_preserves_activities(client, activities, method):
    expected = deepcopy(activities)

    response = client.request(
        method,
        "/activities/Unknown Activity/signup",
        params={"email": "new-student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == expected


def test_unregister_updates_activities(client, activities):
    expected = deepcopy(activities)
    email = expected["Chess Club"]["participants"].pop(0)

    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    updated = client.get("/activities").json()
    assert updated == expected
    assert email not in updated["Chess Club"]["participants"]


def test_unregister_unknown_participant_preserves_activities(client, activities):
    expected = deepcopy(activities)

    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "not-registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert client.get("/activities").json() == expected


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_missing_email_preserves_activities(client, activities, method):
    expected = deepcopy(activities)

    response = client.request(method, "/activities/Chess Club/signup")

    assert response.status_code == 422
    assert any(error["loc"] == ["query", "email"] for error in response.json()["detail"])
    assert client.get("/activities").json() == expected


def test_signup_then_unregister_restores_activities(client, activities):
    expected = deepcopy(activities)
    params = {"email": "roundtrip-student@mergington.edu"}

    signup = client.post("/activities/Chess Club/signup", params=params)
    unregister = client.delete("/activities/Chess Club/signup", params=params)

    assert signup.status_code == 200
    assert unregister.status_code == 200
    assert client.get("/activities").json() == expected