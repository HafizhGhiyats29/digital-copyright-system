from fastapi.testclient import TestClient  # Import test client
from app import app  # Import aplikasi FastAPI


client = TestClient(app)  # Membuat instance client


def test_upload():  # Fungsi test upload

    with open("test.jpg", "rb") as f:  # Membuka file test
        response = client.post("/upload", files={"file": ("test.jpg", f, "image/jpeg")})

    assert response.status_code == 200  # Mengecek status response