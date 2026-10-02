from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import os
import certifi
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection URL
MONGO_DETAILS = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGO_DETAILS, tls=True, tlsCAFile=certifi.where())
db = client.aarohan_ai

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    yield
    client.close()

app = FastAPI(lifespan=lifespan)

@app.post("/api/list_crop")
async def list_crop(request: Request):
    data = await request.json()
    result = await db.crops.insert_one(data)
    return JSONResponse(status_code=200, content={"message": "Crop listed successfully", "id": str(result.inserted_id)})

@app.post("/api/rent_land")
async def rent_land(request: Request):
    data = await request.json()
    result = await db.land_rentals.insert_one(data)
    return JSONResponse(status_code=200, content={"message": "Land rental listed successfully", "id": str(result.inserted_id)})

@app.get("/api/market_status")
async def get_market_status():
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = "Generate realistic daily average crop prices for Indian Mandis in JSON array format. Fields: crop_name, spot_price, mandi_price, trend ('up', 'down'). Return ONLY raw valid JSON array, without markdown blocks. Example: [{'crop_name': 'Paddy', 'spot_price': 2150, 'mandi_price': 2180, 'trend': 'up'}]. List 6 common crops."
        response = model.generate_content(prompt)
        
        # cleanup response text
        text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
        data = json.loads(text)
        return {"prices": data}
    except Exception as e:
        return {"prices": [], "error": str(e)}

# Mount static files to serve the frontend directly
marketing_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/", StaticFiles(directory=marketing_dir, html=True), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)



