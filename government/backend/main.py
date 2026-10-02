from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from contextlib import asynccontextmanager
import uvicorn
import os
import certifi
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB connection URL
MONGO_DETAILS = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGO_DETAILS, tls=True, tlsCAFile=certifi.where())
db = client.government

@asynccontextmanager
async def lifespan(app: FastAPI):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    yield
    client.close()

app = FastAPI(lifespan=lifespan)

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
db = client.government

@app.post("/api/panchayat_auth")
async def panchayat_auth(request: Request):
    data = await request.json()
    admin_id = data.get("adminId")
    password = data.get("password")
    
    if not admin_id or not password:
        return JSONResponse(status_code=400, content={"error": "Admin ID and Password are required."})
    
    existing_user = await db.admins.find_one({"adminId": admin_id})
    
    if existing_user is None:
        # First time login acts as secure registration
        hashed_password = pwd_context.hash(password)
        data["password"] = hashed_password  # Encrypt it
        result = await db.admins.insert_one(data)
        return JSONResponse(status_code=200, content={"message": "Admin Registered & Securely Logged In", "status": "registered", "admin_id": admin_id})
    else:
        # User exists, verify password
        if pwd_context.verify(password, existing_user["password"]):
            return JSONResponse(status_code=200, content={"message": "Login Successful", "status": "authenticated", "admin_id": admin_id})
        else:
            return JSONResponse(status_code=401, content={"error": "Invalid password!"})

@app.post("/api/ai_assistant")
async def ai_assistant(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "Summarize government schemes in 2 sentences.")
        
        prompt = f"You are the Aarohan Governance AI Assistant. Respond concisely to the user. User Query: {query}"
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        return {"response": response.text.strip()}
    except Exception as e:
        return {"error": str(e)}

# Mount static files to serve the frontend directly
government_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/", StaticFiles(directory=government_dir, html=True), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)



