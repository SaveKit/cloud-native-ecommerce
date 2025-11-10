from fastapi import FastAPI
from mangum import Mangum

# สร้าง FastAPI App
app = FastAPI()


@app.get("/products/hello")
def hello_world():
    """Endpoint ทดสอบว่า Service ทำงาน"""
    return {"message": "Hello from Product Service!"}


# นี่คือจุดที่ Mangum แปลง FastAPI ให้ Lambda รู้จัก
# SAM จะเรียก handler นี้
handler = Mangum(app)
