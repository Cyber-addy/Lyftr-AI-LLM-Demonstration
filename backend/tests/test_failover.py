import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_all_keys_failure_returns_503():

    session_id = (
        "all-fail-"
        + str(uuid.uuid4())
    )

    response = client.post(
        "/chat",
        headers={
            "X-Simulate-Failure": "*=429"
        },
        json={
            "session_id": session_id,
            "message": "This request must fail.",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "all providers unavailable"
    }


def test_failed_request_not_stored():

    session_id = (
        "failed-history-"
        + str(uuid.uuid4())
    )

    response = client.post(
        "/chat",
        headers={
            "X-Simulate-Failure": "*=429"
        },
        json={
            "session_id": session_id,
            "message": "Do not store this.",
        },
    )

    assert response.status_code == 503

    history = client.get(
        f"/sessions/{session_id}/messages"
    )

    assert history.status_code == 404