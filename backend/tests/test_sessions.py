import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_unknown_session_returns_404():

    session_id = (
        "unknown-"
        + str(uuid.uuid4())
    )

    response = client.get(
        f"/sessions/{session_id}/messages"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "session not found"
    }