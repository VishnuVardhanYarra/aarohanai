from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    client.close()

app = FastAPI(lifespan=lifespan)

# MongoDB connection URL
MONGO_DETAILS = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_DETAILS, tls=True, tlsCAFile=certifi.where())
db = client.aarohan_ai

@app.post("/api/register_driver")
async def register_driver(request: Request):
    data = await request.json()
    result = await db.drivers.insert_one(data)
    return JSONResponse(status_code=200, content={"message": "Driver registered successfully", "id": str(result.inserted_id)})

@app.post("/api/book_ride")
async def book_ride(request: Request):
    data = await request.json()
    result = await db.rides.insert_one(data)
    return JSONResponse(status_code=200, content={"message": "Ride booked successfully", "id": str(result.inserted_id)})

@app.post("/api/book_farm_equipment")
async def book_farm_equipment(request: Request):
    data = await request.json()
    result = await db.farm_equipment_bookings.insert_one(data)
    return JSONResponse(status_code=200, content={"message": "Farm Equipment booked successfully", "id": str(result.inserted_id)})

# Mount static files to serve the frontend directly from root
transport_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/", StaticFiles(directory=transport_dir, html=True), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)



