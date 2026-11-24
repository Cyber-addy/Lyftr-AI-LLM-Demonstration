from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_empty_message_returns_422():

    response = client.post(
        "/chat",
        json={
            "session_id": "validation-test-1",
            "message": "   ",
        },
    )

    assert response.status_code == 422


def test_message_over_4000_returns_422():

    response = client.post(
        "/chat",
        json={
            "session_id": "validation-test-2",
            "message": "a" * 4001,
        },
    )

    assert response.status_code == 422


def test_empty_session_id_returns_422():

    response = client.post(
        "/chat",
        json={
            "session_id": "",
            "message": "Hello",
        },
    )

    assert response.status_code == 422