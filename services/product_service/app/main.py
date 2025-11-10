import os
import boto3
import uuid
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from mangum import Mangum
from datetime import datetime, timezone

# --- Models (โครงสร้างข้อมูล) ---
# นี่คือ "แบบพิมพ์" ที่ FastAPI ใช้ตรวจสอบข้อมูลขาเข้า


class ProductInput(BaseModel):
    """Model สำหรับรับข้อมูลตอน Create/Update (ไม่มี ProductID)"""

    Name: str = Field(..., min_length=1)
    Description: str = None
    Price: Decimal = Field(..., gt=0)  # Price ต้องมากกว่า 0
    Stock: int = Field(..., ge=0)  # Stock ต้อง >= 0
    Category: str = Field(..., min_length=1)
    ImageUrl: str = None


class ProductResponse(BaseModel):
    """Model สำหรับข้อมูล "ขาออก" (Response)"""

    ProductID: str
    Name: str
    Description: str | None = None
    Price: float  # <-- สังเกตว่าเราใช้ float สำหรับ JSON response
    Stock: int
    Category: str
    ImageUrl: str | None = None
    CreatedAt: str
    UpdatedAt: str


# --- AWS Setup ---
app = FastAPI(title="ProductService")

# ดึงชื่อ Table มาจาก Environment Variable ที่ SAM ตั้งให้
TABLE_NAME = os.environ.get("DYNAMO_TABLE_NAME", "EcomPoc-ProductsTable")
# สร้าง Connection ไปยัง DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


# --- Helper Function ---
def get_iso_timestamp():
    """trả về timestamp ปัจจุบันในรูปแบบ ISO 8601"""
    return datetime.now(timezone.utc).isoformat()


# --- API Endpoints ---


@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product_in: ProductInput):
    """สร้างสินค้าใหม่ (Create)"""

    # สร้างข้อมูลที่จะบันทึกลง DB
    timestamp = get_iso_timestamp()
    item = product_in.model_dump()  # แปลง Pydantic model เป็น dict
    item["ProductID"] = f"PROD-{uuid.uuid4()}"
    item["CreatedAt"] = timestamp
    item["UpdatedAt"] = timestamp

    try:
        # บันทึกลง DynamoDB
        table.put_item(Item=item)
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str):
    """ดึงข้อมูลสินค้าชิ้นเดียว (Read)"""
    try:
        response = table.get_item(Key={"ProductID": product_id})
        item = response.get("Item")

        if not item:
            raise HTTPException(status_code=404, detail="Product not found")
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products", response_model=list[ProductResponse])
def list_products():
    """ดึงสินค้าทั้งหมด (List)"""
    try:
        # หมายเหตุ: .scan() จะดึงข้อมูล *ทั้งหมด* ไม่เหมาะกับข้อมูลปริมาณมาก
        # แต่สำหรับ PoC (Proof of Concept) ถือว่าใช้ได้ครับ
        response = table.scan()
        return response.get("Items", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, product_in: ProductInput):
    """อัปเดตข้อมูลสินค้า (Update)"""

    # 1. ตรวจสอบก่อนว่ามีของจริงไหม
    response = table.get_item(Key={"ProductID": product_id})
    if not response.get("Item"):
        raise HTTPException(status_code=404, detail="Product not found")

    # 2. สร้าง Expression สำหรับอัปเดต (นี่คือวิธีของ DynamoDB)
    update_data = product_in.model_dump(exclude_unset=True)  # เอาเฉพาะฟิลด์ที่ส่งมา
    update_data["UpdatedAt"] = get_iso_timestamp()  # อัปเดตเวลา

    expression_attr_values = {f":{k}": v for k, v in update_data.items()}
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in update_data)

    try:
        # 3. สั่งอัปเดตและขอข้อมูลใหม่ (ReturnValues="ALL_NEW")
        response = table.update_item(
            Key={"ProductID": product_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attr_values,
            ReturnValues="ALL_NEW",
        )
        return response.get("Attributes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/products/{product_id}", status_code=24)
def delete_product(product_id: str):
    """ลบสินค้า (Delete)"""
    try:
        # 1. ตรวจสอบก่อนว่ามีของ
        response = table.get_item(Key={"ProductID": product_id})
        if not response.get("Item"):
            raise HTTPException(status_code=404, detail="Product not found")

        # 2. สั่งลบ
        table.delete_item(Key={"ProductID": product_id})
        # คืนค่า 204 No Content (ตามมาตรฐาน REST)
        return {"detail": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ตัวแปลง Lambda
handler = Mangum(app)
