from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_DETAILS = os.getenv("MONGODB_URI", "mongodb+srv://vishnuyarra794_db_user:Vishnu123@vishnucluster.7ij6mcj.mongodb.net/?appName=Vishnucluster")
try:
    client = AsyncIOMotorClient(MONGO_DETAILS, tls=True, tlsCAFile=certifi.where())
    db = client.aarohan_ai
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.post("/api/login")
async def login(request: Request):
    try:
        data = await request.json()
        # insert into users collection
        result = await db.users.insert_one(data)
        return JSONResponse(status_code=200, content={"message": "User logged in", "id": str(result.inserted_id)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5003))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)



