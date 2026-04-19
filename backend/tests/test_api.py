from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_rejects_non_pdf_extension() -> None:
    response = client.post(
        "/api/v1/passport",
        files={"file": ("not-a-passport.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file format should be .pdf"
