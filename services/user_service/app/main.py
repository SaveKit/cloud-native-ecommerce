import os
import boto3
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from mangum import Mangum
from datetime import datetime, timezone
from typing import Optional

# (Boto3 type hint - เหมือนเดิม)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table
else:
    Table = object


# --- 1. Models ---
class UserProfileInput(BaseModel):
    """ข้อมูลที่ Frontend ส่งมาตอน "อัปเดต" โปรไฟล์"""

    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    ShippingAddress: Optional[str] = None  # (เราใช้ str ง่ายๆ ก่อน)


class UserProfileResponse(UserProfileInput):
    """ข้อมูล User ที่สมบูรณ์ (ที่อยู่ใน DB)"""

    UserID: str  # PK (จาก Cognito 'sub')
    Email: str  # (จาก Cognito 'email')
    UpdatedAt: str


# --- 2. AWS Setup & Dependency Injection ---
app = FastAPI(title="UserService")

TABLE_NAME = os.environ.get("DYNAMO_TABLE_NAME", "EcomPoc-UsersTable")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def get_db_table() -> Table:
    """Dependency function ที่จะส่งต่อ global table"""
    return table


# --- 3. (ใหม่!) Dependency ที่ดึง "ทั้ง" ID และ Email ---
class UserClaims(BaseModel):
    UserID: str
    Email: str


def get_current_user_claims(request: Request) -> UserClaims:
    """
    ดึง UserID (sub) และ Email ออกมาจาก Cognito Authorizer
    """
    try:
        lambda_event = request.scope["aws.event"]
        claims = lambda_event["requestContext"]["authorizer"]["jwt"]["claims"]
        user_id = claims["sub"]
        email = claims.get("email", "")  # Email อาจจะไม่มี

        return UserClaims(UserID=user_id, Email=email)
    except KeyError:
        raise HTTPException(
            status_code=401, detail="Could not extract User claims from token"
        )


# --- 4. Endpoints ---
@app.get("/profile", response_model=UserProfileResponse)
def get_my_profile(
    table: Table = Depends(get_db_table),
    user: UserClaims = Depends(get_current_user_claims),  # <-- "ฉีด" Claims
):
    """
    ดึงโปรไฟล์ของ User ที่ล็อกอินอยู่
    ถ้าไม่เจอ (User ล็อกอินครั้งแรก) ให้สร้างโปรไฟล์ "ว่าง" ให้
    """
    try:
        response = table.get_item(Key={"UserID": user.UserID})
        item = response.get("Item")

        if not item:
            # User ล็อกอินครั้งแรก, สร้างโปรไฟล์ "โครงกระดูก" (Skeleton) ให้
            print(f"User {user.UserID} not found. Creating skeleton profile.")
            timestamp = datetime.now(timezone.utc).isoformat()

            # แปลง Decimal เป็น float สำหรับ Response Model (ถ้ามี)
            # (ในที่นี้ยังไม่มี Decimal)

            item = {
                "UserID": user.UserID,
                "Email": user.Email,
                "UpdatedAt": timestamp,
                # FirstName, LastName ฯลฯ จะเป็น None
            }

            # บันทึก skeleton profile ลง DB
            table.put_item(Item=item)

        # แปลง Decimal (ถ้ามี) เป็น float สำหรับ Response Model
        # (เช่น ถ้าเราเก็บ Credit balance)

        return item  # คืนค่า (ที่เพิ่งสร้าง หรือที่ดึงมา)

    except Exception as e:
        print(f"!!! UNEXPECTED ERROR (get_profile): {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.put("/profile", response_model=UserProfileResponse)
def update_my_profile(
    profile_in: UserProfileInput,
    table: Table = Depends(get_db_table),
    user: UserClaims = Depends(get_current_user_claims),  # <-- "ฉีด" Claims
):
    """อัปเดตโปรไฟล์ของ User ที่ล็อกอินอยู่"""

    try:
        # 1. สร้าง Expression (ใช้ Pattern จาก ProductService ที่แก้บั๊ก 'Name' แล้ว)
        # .model_dump(exclude_unset=True) คือเอาเฉพาะ field ที่ User ส่งมา
        update_data = profile_in.model_dump(exclude_unset=True)
        update_data["UpdatedAt"] = datetime.now(timezone.utc).isoformat()

        # (แก้บั๊ก float vs Decimal - ถ้ามี)
        # (ในที่นี้ยังไม่มี Decimal)

        # (แก้บั๊ก Reserved Keywords - ใช้ Pattern นี้เสมอ)
        expression_attr_values = {}
        expression_attr_names = {}
        update_expression_parts = []

        for i, (key, value) in enumerate(update_data.items()):
            val_placeholder = f":val{i}"
            key_placeholder = f"#key{i}"

            expression_attr_values[val_placeholder] = value
            expression_attr_names[key_placeholder] = key
            update_expression_parts.append(f"{key_placeholder} = {val_placeholder}")

        update_expression = "SET " + ", ".join(update_expression_parts)

        # 2. สั่งอัปเดต
        # (ใช้ 'get_item' ก่อนก็ได้ แต่ 'update_item' ก็ปลอดภัยเพราะใช้ UserID จาก Token)
        response = table.update_item(
            Key={"UserID": user.UserID},  # <-- อัปเดตที่ UserID ของเราเท่านั้น
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attr_values,
            ExpressionAttributeNames=expression_attr_names,
            ReturnValues="ALL_NEW",  # สั่งให้คืนค่า "ใหม่" กลับมา
        )

        return response.get("Attributes")  # คืนค่าที่อัปเดตแล้ว

    except Exception as e:
        print(f"!!! UNEXPECTED ERROR (update_profile): {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


# ตัวแปลง Lambda
handler = Mangum(app)
