import os
import boto3
import uuid
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from mangum import Mangum
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table
else:
    Table = object

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


def get_db_table() -> Table:
    """Dependency function ที่จะส่งต่อ global table"""
    return table


# --- Helper Function ---
def get_iso_timestamp():
    """สร้าง timestamp ปัจจุบันในรูปแบบ ISO 8601"""
    return datetime.now(timezone.utc).isoformat()


# --- API Endpoints ---


@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product_in: ProductInput, table: Table = Depends(get_db_table)):
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
def get_product(product_id: str, table: Table = Depends(get_db_table)):
    """ดึงข้อมูลสินค้าชิ้นเดียว (Read)"""
    try:
        response = table.get_item(Key={"ProductID": product_id})
        item = response.get("Item")

        if not item:
            raise HTTPException(status_code=404, detail="Product not found")
        return item

    except HTTPException as http_exc:
        # ปล่อย HTTPException (เช่น 404) ที่เราตั้งใจโยน ให้ผ่านไป
        raise http_exc
    except Exception as e:
        # จับ Exception "อื่นๆ" ที่ไม่คาดคิด (เช่น Boto3 พัง)
        print(f"!!! UNEXPECTED ERROR (get_product): {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/products", response_model=list[ProductResponse])
def list_products(table: Table = Depends(get_db_table)):
    """ดึงสินค้าทั้งหมด (List)"""
    try:
        # หมายเหตุ: .scan() จะดึงข้อมูล *ทั้งหมด* ไม่เหมาะกับข้อมูลปริมาณมาก
        # แต่สำหรับ PoC (Proof of Concept) ถือว่าใช้ได้ครับ
        response = table.scan()
        return response.get("Items", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str, product_in: ProductInput, table: Table = Depends(get_db_table)
):
    """อัปเดตข้อมูลสินค้า (Update)"""

    # 1. ตรวจสอบก่อนว่ามีของจริงไหม
    response = table.get_item(Key={"ProductID": product_id})
    if not response.get("Item"):
        raise HTTPException(status_code=404, detail="Product not found")

    # 2. สร้าง Expression
    update_data = product_in.model_dump(exclude_unset=True)
    update_data["UpdatedAt"] = get_iso_timestamp()

    # --- (Fix 3) นี่คือ 3 บรรทัดที่เพิ่มกลับเข้ามา ---
    # จงใจแปลง 'Price' (ที่เป็น float) กลับไปเป็น Decimal
    if "Price" in update_data:
        update_data["Price"] = Decimal(str(update_data["Price"]))
    # --- สิ้นสุดส่วนที่เพิ่ม ---

    # --- (Fix 4) นี่คือวิธีแก้ "Reserved Keyword" (เหมือนเดิม) ---
    expression_attr_values = {}
    expression_attr_names = {}
    update_expression_parts = []

    # สร้าง Placeholder ที่ปลอดภัยสำหรับทุก Key/Value
    for i, (key, value) in enumerate(update_data.items()):
        val_placeholder = f":val{i}"  # e.g., :val0, :val1
        key_placeholder = f"#key{i}"  # e.g., #key0, #key1

        # ตอนนี้ 'value' ของ 'Price' จะเป็น Decimal แล้ว
        expression_attr_values[val_placeholder] = value
        expression_attr_names[key_placeholder] = key  # e.g., {"#key0": "Name"}
        update_expression_parts.append(f"{key_placeholder} = {val_placeholder}")

    update_expression = "SET " + ", ".join(update_expression_parts)
    # --- สิ้นสุด Fix 4 ---

    try:
        # 3. สั่งอัปเดตและขอข้อมูลใหม่ (ReturnValues="ALL_NEW")
        response = table.update_item(
            Key={"ProductID": product_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attr_values,
            ExpressionAttributeNames=expression_attr_names,  # <-- เพิ่มอันนี้!
            ReturnValues="ALL_NEW",
        )
        return response.get("Attributes")
    except HTTPException as http_exc:
        # ปล่อย HTTPException (เช่น 404) ที่เราตั้งใจโยน ให้ผ่านไป
        raise http_exc
    except Exception as e:
        # (ลบ print() debug เก่าทิ้งได้เลย)
        print(f"!!! UNEXPECTED ERROR (update_product): {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: str, table: Table = Depends(get_db_table)):
    """ลบสินค้า (Delete)"""
    try:
        # 1. ตรวจสอบก่อนว่ามีของ
        response = table.get_item(Key={"ProductID": product_id})
        if not response.get("Item"):
            raise HTTPException(status_code=404, detail="Product not found")

        # 2. สั่งลบ
        table.delete_item(Key={"ProductID": product_id})

    except HTTPException as http_exc:
        # ปล่อย HTTPException (เช่น 404) ที่เราตั้งใจโยน ให้ผ่านไป
        raise http_exc
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR (delete_product): {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


# ตัวแปลง Lambda
handler = Mangum(app)
