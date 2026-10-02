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
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

MONGO_DETAILS = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGO_DETAILS, tls=True, tlsCAFile=certifi.where())
db = client.aarohan_ai

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

@app.post("/api/ai_career_suggestion")
async def ai_career_suggestion(request: Request):
    try:
        data = await request.json()
        education = data.get("education", "10th Pass")
        budget = data.get("budget", 500000)
        land = data.get("land", 5)
        interest = data.get("interest", "Technology")
        
        prompt = f"""
        Given the following profile for a young agripreneur in India:
        - Education: {education}
        - Budget: ₹{budget}
        - Land: {land} acres
        - Interest: {interest}
        
        Suggest exactly one highly suitable career path or business venture in agriculture or agri-tech for this person.
        Respond ONLY with a raw JSON object (no markdown, no quotes around the json blocks) with the following exact keys:
        - "title": (string) The job or business title
        - "desc": (string) A short 1-sentence description
        - "salary": (string) Expected annual income (e.g., "₹8-12L")
        - "demand": (string) "High", "Very High", "Growing", etc.
        - "training": (string) Estimated training/setup time
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[len('```json'):]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
        
        result = json.loads(text)
        
        # Save usage history to MongoDB (optional)
        await db.ai_career_suggestions.insert_one({
            "profile": data,
            "suggestion": result
        })
        
        return JSONResponse(status_code=200, content={"suggestion": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

youth_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/", StaticFiles(directory=youth_dir, html=True), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)



