import pytest
from fastapi.testclient import TestClient


# --- Fixture (ที่ Mock 2 อย่าง) ---
@pytest.fixture
def test_client(mock_dynamodb_table):

    # Import app และ dependencies ที่นี่
    from services.user_service.app.main import (
        app,
        get_db_table,
        get_current_user_claims,
    )
    from services.user_service.app.main import UserClaims

    # --- Mock 1: Database ---
    def get_mock_table():
        return mock_dynamodb_table

    app.dependency_overrides[get_db_table] = get_mock_table

    # --- Mock 2: Authentication ---
    MOCK_USER_ID = "test-user-profile-123"
    MOCK_EMAIL = "test@example.com"

    def get_mock_user_claims():
        return UserClaims(UserID=MOCK_USER_ID, Email=MOCK_EMAIL)

    app.dependency_overrides[get_current_user_claims] = get_mock_user_claims

    client = TestClient(app)

    # ส่ง MOCK_USER_ID กลับไปด้วย
    yield client, MOCK_USER_ID

    app.dependency_overrides = {}  # ล้าง mock


# --- Test Cases ---
def test_get_and_update_profile(test_client, mock_dynamodb_table):
    """
    เทสวงจรชีวิตของ Profile (GET ครั้งแรก -> PUT -> GET ครั้งที่สอง)
    """
    client, MOCK_USER_ID = test_client

    # 1. GET (ครั้งแรก - ควรสร้าง Skeleton Profile)
    response_get_1 = client.get("/profile")

    assert response_get_1.status_code == 200
    data_1 = response_get_1.json()
    assert data_1["UserID"] == MOCK_USER_ID
    assert data_1["Email"] == "test@example.com"
    assert data_1["FirstName"] is None  # ยังไม่มีชื่อ

    # 2. PUT (อัปเดต Profile)
    profile_data = {
        "FirstName": "Test",
        "LastName": "User",
        "ShippingAddress": "123 Main St",
    }
    response_put = client.put("/profile", json=profile_data)

    assert response_put.status_code == 200
    data_put = response_put.json()
    assert data_put["FirstName"] == "Test"
    assert data_put["LastName"] == "User"
    assert data_put["ShippingAddress"] == "123 Main St"
    assert data_put["UserID"] == MOCK_USER_ID  # เช็คว่ายังเป็น User เดิม

    # 3. GET (ครั้งที่สอง - ควรได้ข้อมูลที่อัปเดต)
    response_get_2 = client.get("/profile")

    assert response_get_2.status_code == 200
    data_2 = response_get_2.json()
    assert data_2["FirstName"] == "Test"
    assert data_2["ShippingAddress"] == "123 Main St"
