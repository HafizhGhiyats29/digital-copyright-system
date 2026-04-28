from fastapi.testclient import TestClient  # Import client untuk test FastAPI

from app import create_app  # Import factory aplikasi gateway


def test_health_endpoint_returns_gateway_status():  # Test endpoint health gateway
    # TestClient runs the app lifespan, including the shared HTTP client setup.
    with TestClient(create_app()) as client:  # Membuat test client dan menjalankan lifespan app
        response = client.get("/health")  # Kirim request GET ke endpoint health

    # Health endpoint should identify the gateway and return request tracing.
    assert response.status_code == 200  # Pastikan status HTTP berhasil
    assert response.json()["status"] == "ok"  # Pastikan body menandakan status ok
    assert response.json()["service"] == "api-gateway"  # Pastikan service yang menjawab adalah gateway
    assert "X-Request-ID" in response.headers  # Pastikan middleware menambahkan request id
