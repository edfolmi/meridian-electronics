from fastapi.testclient import TestClient

from app.api import auth
from app.api import routes
from app.main import create_app
from app.schemas.chat import ChatResponse


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint_uses_orchestrator(monkeypatch) -> None:
    class FakeOrchestrator:
        def __init__(self, _settings) -> None:
            pass

        async def respond(self, _messages, _customer):
            return ChatResponse(
                message="Verified by Meridian tools.",
                request_id="req123",
                tool_calls=[],
            )

    monkeypatch.setattr(routes, "ChatOrchestrator", FakeOrchestrator)
    client = TestClient(create_app())

    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "Do you have monitors?"}]},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Verified by Meridian tools."


def test_chat_endpoint_accepts_safe_customer_context(monkeypatch) -> None:
    seen_customer = None

    class FakeOrchestrator:
        def __init__(self, _settings) -> None:
            pass

        async def respond(self, _messages, customer):
            nonlocal seen_customer
            seen_customer = customer
            return ChatResponse(message="Orders ready.", request_id="req456")

    monkeypatch.setattr(routes, "ChatOrchestrator", FakeOrchestrator)
    client = TestClient(create_app())

    response = client.post(
        "/api/chat",
        json={
            "messages": [{"role": "user", "content": "Show my orders"}],
            "customer": {
                "customer_id": "41c2903a-f1a5-47b7-a81d-86b50ade220f",
                "name": "Donald Garcia",
                "email": "donaldgarcia@example.net",
                "role": "admin",
            },
        },
    )

    assert response.status_code == 200
    assert seen_customer.customer_id == "41c2903a-f1a5-47b7-a81d-86b50ade220f"


def test_auth_endpoint_returns_safe_customer_session(monkeypatch) -> None:
    class FakeMcpClient:
        def __init__(self, _url) -> None:
            pass

        async def call_tool(self, name, arguments):
            assert name == "verify_customer_pin"
            assert arguments == {"email": "donaldgarcia@example.net", "pin": "7912"}
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Customer verified: Donald Garcia\n"
                            "Customer ID: 41c2903a-f1a5-47b7-a81d-86b50ade220f\n"
                            "Email: donaldgarcia@example.net\n"
                            "Role: admin"
                        ),
                    }
                ],
                "isError": False,
            }

    monkeypatch.setattr(auth, "McpClient", FakeMcpClient)
    client = TestClient(create_app())

    response = client.post(
        "/api/auth/sign-in",
        json={"email": "donaldgarcia@example.net", "pin": "7912"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["customer"]["customer_id"] == "41c2903a-f1a5-47b7-a81d-86b50ade220f"
    assert "pin" not in body["customer"]
