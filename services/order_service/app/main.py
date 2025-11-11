import os
import boto3
import uuid
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from mangum import Mangum
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key  # <-- เราจะใช้ Query
from typing import List

# (Boto3 type hint - เหมือนเดิม)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table
else:
    Table = object


# --- 1. Models ---
class OrderItemInput(BaseModel):
    """สินค้า 1 ชนิดในตะกร้า"""

    ProductID: str
    Quantity: int = Field(..., gt=0)
    PricePerUnit: Decimal = Field(..., gt=0)  # รับเป็น Decimal


class OrderInput(BaseModel):
    """ข้อมูลที่ Frontend ส่งมาตอนกด "สั่งซื้อ" """

    Items: List[OrderItemInput]
    TotalAmount: Decimal = Field(..., gt=0)
    # (เราจะไม่รับ UserID จาก Body/Input... เราจะดึงจาก Token!)


class OrderItemResponse(BaseModel):
    """ข้อมูลสินค้า 1 ชนิด ที่ส่งกลับไปให้ Client"""

    ProductID: str
    Quantity: int
    PricePerUnit: float


class OrderResponse(BaseModel):
    """ข้อมูล Order ที่ส่งกลับไปให้ Client"""

    UserID: str
    OrderID: str
    Status: str
    CreatedAt: str
    Items: List[OrderItemResponse]
    TotalAmount: float


# --- 2. AWS Setup & Dependency Injection ---
app = FastAPI(title="OrderService")

TABLE_NAME = os.environ.get("DYNAMO_TABLE_NAME", "EcomPoc-OrdersTable")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def get_db_table() -> Table:
    """Dependency function ที่จะส่งต่อ global table"""
    return table


# --- 3. (ใหม่!) Dependency สำหรับดึง UserID จาก Token ---
def get_current_user_id(request: Request) -> str:
    """
    ดึง UserID (sub) ออกมาจาก Cognito Authorizer
    ที่ API Gateway ส่งมาให้ใน 'request.scope'
    """
    try:
        # Mangum (ตัวแปลง) จะเก็บ event ของ Lambda ไว้ใน scope
        lambda_event = request.scope["aws.event"]
        user_id = lambda_event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
        return user_id
    except KeyError:
        # นี่คือ Error ร้ายแรง (_ควร_ จะมี ถ้า Auth ถูกตั้งค่าไว้)
        raise HTTPException(
            status_code=401, detail="Could not extract UserID from token"
        )


# --- 4. Endpoints ---
@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(
    order_in: OrderInput,
    table: Table = Depends(get_db_table),
    user_id: str = Depends(get_current_user_id),  # <-- "ฉีด" UserID เข้ามา
):
    """สร้างคำสั่งซื้อใหม่สำหรับ User ที่ล็อกอินอยู่"""

    timestamp = datetime.now(timezone.utc).isoformat()
    order_id = f"ORDER-{uuid.uuid4()}"  # สร้าง OrderID ใหม่

    # แปลง Pydantic model เป็น dict (ใช้ mode='python' เพื่อคง Decimal)
    item = order_in.model_dump(mode="python")

    # เพิ่ม PK, SK, และข้อมูลที่เราดึงมา
    item["UserID"] = user_id
    item["OrderID"] = order_id
    item["Status"] = "PENDING"  # สถานะเริ่มต้น
    item["CreatedAt"] = timestamp

    try:
        table.put_item(Item=item)
        return item
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR (create_order): {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/orders", response_model=List[OrderResponse])
def list_my_orders(
    table: Table = Depends(get_db_table),
    user_id: str = Depends(get_current_user_id),  # <-- "ฉีด" UserID เข้ามา
):
    """ดึงรายการคำสั่งซื้อ "ทั้งหมด" ของ User ที่ล็อกอินอยู่"""
    try:
        # นี่คือพลังของ Composite Key!
        # เรา "Query" หา "ตู้" (PK) ที่ UserID ตรงกัน
        response = table.query(KeyConditionExpression=Key("UserID").eq(user_id))
        return response.get("Items", [])

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR (list_my_orders): {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


# ตัวแปลง Lambda
handler = Mangum(app)
