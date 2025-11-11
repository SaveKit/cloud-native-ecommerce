import pytest
from fastapi.testclient import TestClient
from decimal import Decimal


# --- Fixture (ที่ Mock 2 อย่าง) ---
@pytest.fixture
def test_client(mock_dynamodb_table):

    # Import app และ dependencies ที่นี่
    from services.order_service.app.main import app, get_db_table, get_current_user_id

    # --- Mock 1: Database ---
    def get_mock_table():
        return mock_dynamodb_table

    app.dependency_overrides[get_db_table] = get_mock_table

    # --- Mock 2: Authentication ---
    # เรา "แกล้ง" เป็น User คนนี้
    MOCK_USER_ID = "test-user-123"

    def get_mock_user_id():
        return MOCK_USER_ID

    app.dependency_overrides[get_current_user_id] = get_mock_user_id

    client = TestClient(app)

    # ส่ง MOCK_USER_ID กลับไปด้วย เผื่อเทสอยากใช้
    yield client, MOCK_USER_ID

    app.dependency_overrides = {}  # ล้าง mock


# --- Test Cases ---
def test_create_and_list_orders(test_client, mock_dynamodb_table):
    """
    เทสวงจรชีวิตของ Order (Create -> List)
    """
    client, MOCK_USER_ID = test_client  # รับ client และ mock user id

    # 1. Create Order
    order_data = {
        "Items": [{"ProductID": "PROD-1", "Quantity": 2, "PricePerUnit": 10.50}],
        "TotalAmount": 21.00,
    }
    response = client.post("/orders", json=order_data)

    # ตรวจสอบ Response
    assert response.status_code == 201
    data = response.json()
    assert data["UserID"] == MOCK_USER_ID  # เช็คว่า UserID ถูกใส่
    assert data["TotalAmount"] == 21.00
    assert data["Status"] == "PENDING"
    assert "ORDER-" in data["OrderID"]

    order_id = data["OrderID"]

    # 2. List Orders (ตรวจสอบว่าข้อมูลเข้า DB จริง)
    response = client.get("/orders")

    assert response.status_code == 200
    orders = response.json()
    assert isinstance(orders, list)
    assert len(orders) == 1
    assert orders[0]["OrderID"] == order_id
    assert orders[0]["UserID"] == MOCK_USER_ID
