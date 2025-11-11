import pytest
from fastapi.testclient import TestClient


# --- Fixture ---
@pytest.fixture
def test_client(mock_dynamodb_table):  # <-- mock_dynamodb_table มาจาก conftest
    """
    สร้าง TestClient และ "Override" (ทับที่) Dependency ของ get_db_table
    """

    # Import app และ dependency function ที่นี่
    from services.product_service.app.main import app, get_db_table

    # นี่คือ "Mock" dependency function
    def get_mock_table():
        """ส่งต่อ table จำลอง (จาก conftest)"""
        return mock_dynamodb_table

    # --- นี่คือการ "Inject" ที่ถูกต้อง ---
    # บอก FastAPI ว่า: "เมื่อไหร่ก็ตามที่โค้ดเรียก get_db_table,
    # ให้เรียก get_mock_table (ที่คืนค่า mock) แทน"
    app.dependency_overrides[get_db_table] = get_mock_table

    client = TestClient(app)
    yield client

    # ล้าง overrides เมื่อเทสจบ
    app.dependency_overrides = {}


# --- Test Cases (ใหม่) ---


def test_create_product_success(test_client):
    """เทสการสร้างสินค้า (POST) - กรณีสำเร็จ"""
    response = test_client.post(
        "/products",
        json={
            "Name": "Test Shirt",
            "Price": 29.99,  # JSON number (Pydantic/Decimal จะจัดการเอง)
            "Stock": 100,
            "Category": "Apparel",
            "ImageUrl": "https://test.com/img.jpg",
        },
    )

    # 1. ตรวจสอบว่า Status Code = 201 Created
    assert response.status_code == 201

    # 2. ตรวจสอบข้อมูลที่ได้กลับมา
    data = response.json()
    assert data["Name"] == "Test Shirt"
    assert data["Price"] == 29.99
    assert data["Category"] == "Apparel"
    assert "PROD-" in data["ProductID"]  # ตรวจสอบว่า ID ถูกสร้างใน Format ที่ถูกต้อง


def test_create_product_bad_data(test_client):
    """เทสการสร้างสินค้า - กรณีข้อมูลไม่ถูกต้อง (ราคาติดลบ)"""
    response = test_client.post(
        "/products",
        json={
            "Name": "Bad Shirt",
            "Price": -10.00,  # ข้อมูลผิด (Model เราบังคับ gt=0)
            "Stock": 100,
            "Category": "Apparel",
        },
    )

    # 3. ตรวจสอบว่า FastAPI คืน 422 Unprocessable Entity
    assert response.status_code == 422


def test_product_full_lifecycle(test_client):
    """
    เทสวงจรชีวิตสินค้า (Create -> Get -> List -> Update -> Delete -> Verify)
    (นี่คือเทสที่ครอบคลุมที่สุด)
    """

    # 1. Create Product
    create_response = test_client.post(
        "/products",
        json={
            "Name": "Lifecycle Test",
            "Price": 10.00,
            "Stock": 10,
            "Category": "Tests",
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["ProductID"]

    # 2. Get Product (ตรวจสอบว่าสร้างสำเร็จ)
    get_response = test_client.get(f"/products/{product_id}")
    assert get_response.status_code == 200
    assert get_response.json()["Name"] == "Lifecycle Test"

    # 3. List Products (ตรวจสอบว่าอยู่ในรายการ)
    list_response = test_client.get("/products")
    assert list_response.status_code == 200
    products = list_response.json()
    assert isinstance(products, list)  # ต้องเป็น List
    assert len(products) == 1  # ต้องมี 1 ชิ้น
    assert products[0]["ProductID"] == product_id

    # 4. Update Product
    update_response = test_client.put(
        f"/products/{product_id}",
        json={
            "Name": "Updated Name",
            "Price": 15.50,
            "Stock": 5,
            "Category": "Tests-Updated",
            "ImageUrl": "https://new.url",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["Name"] == "Updated Name"
    assert update_response.json()["Price"] == 15.50

    # 5. Delete Product
    delete_response = test_client.delete(f"/products/{product_id}")
    assert delete_response.status_code == 204  # 204 No Content

    # 6. Verify Deletion (Get ควรจะ 404 Not Found)
    verify_get_response = test_client.get(f"/products/{product_id}")
    assert verify_get_response.status_code == 404
    assert verify_get_response.json()["detail"] == "Product not found"
