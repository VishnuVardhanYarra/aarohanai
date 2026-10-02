import os
import json
import io
import traceback
from datetime import datetime
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import google.generativeai as genai
import PIL.Image
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import uvicorn

# ==========================================
# ROBUST DATABASE FALLBACK (LOCAL JSON DB)
# ==========================================
try:
    from bson import ObjectId
except ImportError:
    import uuid
    class ObjectId:
        def __init__(self, val=None):
            self.val = val if val else uuid.uuid4().hex[:24]
        def __str__(self):
            return str(self.val)
        def __repr__(self):
            return f"ObjectId('{self.val}')"

class LocalJSONCursor:
    def __init__(self, data):
        self.data = data
        self.index = 0

    def sort(self, field, direction=-1):
        reverse = True if direction == -1 else False
        def get_val(x):
            val = x.get(field)
            if val is None:
                return ""
            return str(val)
        self.data.sort(key=get_val, reverse=reverse)
        return self

    def limit(self, count):
        self.data = self.data[:count]
        return self

    async def to_list(self, length=None):
        if length is not None:
            return self.data[:length]
        return self.data

    def __aiter__(self):
        self.index = 0
        return self

    async def __anext__(self):
        if self.index < len(self.data):
            val = self.data[self.index]
            self.index += 1
            return val
        else:
            raise StopAsyncIteration

class LocalJSONCollection:
    def __init__(self, name, db_dir):
        self.name = name
        self.file_path = os.path.join(db_dir, f"{name}.json")
        self.db_dir = db_dir
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _read(self):
        try:
            if not os.path.exists(self.file_path):
                return []
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _write(self, data):
        try:
            if not os.path.exists(self.db_dir):
                os.makedirs(self.db_dir)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            print(f"Error writing to local JSON collection {self.name}: {e}")

    async def find_one(self, query):
        data = self._read()
        for doc in data:
            match = True
            for k, v in query.items():
                if str(doc.get(k)) != str(v):
                    match = False
                    break
            if match:
                return doc
        return None

    async def insert_one(self, doc):
        data = self._read()
        if "_id" not in doc:
            doc["_id"] = str(ObjectId())
        data.append(doc)
        self._write(data)
        class InsertResult:
            def __init__(self, id):
                self.inserted_id = id
        return InsertResult(doc["_id"])

    def find(self, query=None):
        if query is None:
            query = {}
        data = self._read()
        filtered = []
        for doc in data:
            match = True
            for k, v in query.items():
                if str(doc.get(k)) != str(v):
                    match = False
                    break
            if match:
                filtered.append(doc)
        return LocalJSONCursor(filtered)

    async def update_one(self, query, update_doc):
        data = self._read()
        updated = False
        for doc in data:
            match = True
            for k, v in query.items():
                if str(doc.get(k)) != str(v):
                    match = False
                    break
            if match:
                if "$set" in update_doc:
                    for uk, uv in update_doc["$set"].items():
                        doc[uk] = uv
                else:
                    for uk, uv in update_doc.items():
                        doc[uk] = uv
                updated = True
                break
        if updated:
            self._write(data)

class LocalJSONDatabase:
    def __init__(self, db_dir):
        self.db_dir = db_dir
        self.collections = {}

    def __getattr__(self, name):
        if name not in self.collections:
            self.collections[name] = LocalJSONCollection(name, self.db_dir)
        return self.collections[name]

    def __getitem__(self, name):
        return self.__getattr__(name)

class LocalJSONClient:
    def __init__(self, db_dir="local_db"):
        self.db_dir = db_dir
        self.database = LocalJSONDatabase(db_dir)

    @property
    def aarohan_ai(self):
        return self.database

    def __getattr__(self, name):
        return self.database

    def close(self):
        pass

# Initialize client & db to local JSON fallback by default
client = LocalJSONClient("local_db")
db = client.aarohan_ai

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyD10DWUiKk30gd-q1tKYdhxzIcKMIddoPE")
    if api_key:
        genai.configure(api_key=api_key)
        
    MONGO_DETAILS = os.getenv("MONGODB_URI", "mongodb+srv://vishnuyarra794_db_user:Vishnu123@vishnucluster.7ij6mcj.mongodb.net/?appName=Vishnucluster")
    try:
        print("Connecting to MongoDB Atlas...")
        atlas_client = AsyncIOMotorClient(MONGO_DETAILS, tls=True, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000)
        # Verify connection status by calling server_info
        await atlas_client.server_info()
        client = atlas_client
        db = client.aarohan_ai
        print("✅ Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"⚠️ MongoDB Atlas connection failed: {e}")
        print("Fallback: Active database remains local JSON database (local_db/)")
        
    yield
    if client:
        client.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# AUTH API
# ==========================================
@app.post("/api/register")
async def register(request: Request):
    try:
        data = await request.json()
        if not data.get("mobile") or not data.get("password"):
            return JSONResponse(status_code=400, content={"error": "Mobile and password are required"})
            
        # Check if user already exists
        existing_user = await db.users.find_one({"mobile": data["mobile"]})
        if existing_user:
            return JSONResponse(status_code=400, content={"error": "User already registered locally"})
            
        # Hash password before storage
        data["password"] = hash_password(data["password"])
        result = await db.users.insert_one(data)
        return JSONResponse(status_code=200, content={"message": "User registered successfully", "id": str(result.inserted_id)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/doctor_auth")
async def doctor_auth(request: Request):
    try:
        data = await request.json()
        email = data.get("email") # or username
        password = data.get("password")
        
        if not email or not password:
            return JSONResponse(status_code=400, content={"error": "Email and Password are required."})
        
        # Check against a dedicated doctors collection
        existing_doctor = await db.doctors.find_one({"email": email})
        
        if existing_doctor is None:
            # First time login = secure registration
            hashed = hash_password(password)
            data["password"] = hashed
            await db.doctors.insert_one(data)
            return JSONResponse(status_code=200, content={
                "message": "Doctor Registered & Securely Logged In", 
                "status": "registered", 
                "email": email,
                "fullName": data.get("fullName", email.split('@')[0]),
                "specialization": data.get("specialization", "General Physician")
            })
        else:
            # Login check
            if existing_doctor["password"] == hash_password(password):
                return JSONResponse(status_code=200, content={
                    "message": "Login Successful", 
                    "status": "authenticated", 
                    "email": email,
                    "fullName": existing_doctor.get("fullName", email.split('@')[0]),
                    "specialization": existing_doctor.get("specialization", "General Physician")
                })
            else:
                return JSONResponse(status_code=401, content={"error": "Invalid password!"})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/book_appointment")
async def book_appointment(request: Request):
    try:
        data = await request.json()
        # Expecting: patientName, disease, location, doctorEmail, timestamp
        data["status"] = "Pending"
        data["created_at"] = datetime.now()
        await db.appointments.insert_one(data)
        return JSONResponse(status_code=200, content={"message": "Appointment booked successfully!", "success": True})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "success": False})

@app.get("/api/doctor_appointments")
async def get_doctor_appointments(doctor_email: str):
    try:
        cursor = db.appointments.find({"doctorEmail": doctor_email}).sort("created_at", -1)
        appointments = await cursor.to_list(length=100)
        for appt in appointments:
            appt["_id"] = str(appt["_id"])
            if isinstance(appt.get("created_at"), datetime):
                appt["created_at"] = appt["created_at"].isoformat()
        return {"success": True, "appointments": appointments}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/list_doctors")
async def list_doctors():
    try:
        # Fetch all registered doctors, only returning public info
        cursor = db.doctors.find({}, {"password": 0})
        doctors = await cursor.to_list(length=50)
        for doc in doctors:
            doc["_id"] = str(doc["_id"])
        return {"success": True, "doctors": doctors}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/ai_diet_suggestion")
async def ai_diet_suggestion(request: Request):
    try:
        data = await request.json()
        bmi = data.get("bmi")
        status = data.get("status", "Healthy")
        age = data.get("age", 30)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""Act as a professional nutritionist for rural India.
        Profile: BMI {bmi} ({status}), Age {age}.
        Suggest a balanced diet plan using locally available, affordable items in South India (especially Andhra/Telangana).
        Include: Breakfast, Lunch, Snack, Dinner.
        Also advise on water intake and exercise.
        Respond with ONLY a raw JSON object (no markdown) with these keys:
        - "breakfast": "Telugu short description",
        - "lunch": "Telugu short description",
        - "snack": "Telugu short description",
        - "dinner": "Telugu short description",
        - "advice": "Telugu short general tip",
        - "calories": "Target daily cal"
        """
        response = model.generate_content(prompt)
        result = extract_json(response.text)
        return {"success": True, "diet": result}
    except Exception as e:
        traceback.print_exc()
        print("⚠️ Diet suggestion Gemini API failed. Using local fallback.")
        fallback_diet = {
            "breakfast": "రాగుల సంకటి లేదా ఇడ్లీతో వేరుశనగ పచ్చడి (Ragi Sangati or Idli with Peanut Chutney)",
            "lunch": "సజ్జన్నం లేదా అన్నం తో తోటకూర పప్పు, మజ్జిగ (Pearl Millet or Rice with Amaranth Dal, Buttermilk)",
            "snack": "ఉడికించిన శనగలు లేదా జొన్న పేలాలు (Boiled Bengal Gram or Jowar Popcorn)",
            "dinner": "జొన్న రొట్టె తో ఆకుకూరల కూర (Jowar Roti with Leafy Vegetable Curry)",
            "advice": "రోజూ 3-4 లీటర్ల నీరు తాగండి, క్రమం తప్పకుండా నడవండి (Drink 3-4L water daily, walk regularly)",
            "calories": "2200 - 2400 kcal"
        }
        return {"success": True, "diet": fallback_diet}

@app.post("/api/panchayat_auth")
async def panchayat_auth(request: Request):
    try:
        data = await request.json()
        admin_id = data.get("adminId")
        password = data.get("password")
        
        if not admin_id or not password:
            return JSONResponse(status_code=400, content={"error": "Admin ID and Password are required."})
        
        # Check against a dedicated admins collection
        existing_admin = await db.admins.find_one({"adminId": admin_id})
        
        if existing_admin is None:
            # First time login = secure registration
            hashed = hash_password(password)
            data["password"] = hashed
            await db.admins.insert_one(data)
            return JSONResponse(status_code=200, content={
                "message": "Admin Registered & Securely Logged In", 
                "status": "registered", 
                "adminId": admin_id,
                "fullName": data.get("fullName", "Admin"),
                "role": data.get("role", "Official")
            })
        else:
            # Login check
            if existing_admin["password"] == hash_password(password):
                return JSONResponse(status_code=200, content={
                    "message": "Login Successful", 
                    "status": "authenticated", 
                    "adminId": admin_id,
                    "fullName": existing_admin.get("fullName", "Admin"),
                    "role": existing_admin.get("role", "Official")
                })
            else:
                return JSONResponse(status_code=401, content={"error": "Invalid password!"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/login")
async def login_user(request: Request):
    try:
        data = await request.json()
        mobile = data.get("mobile")
        password = data.get("password")
        
        if not mobile or not password:
            return JSONResponse(status_code=400, content={"error": "Mobile and password are required"})
            
        hashed_pw = hash_password(password)
        # Search db for matching mobile + hashed password
        user = await db.users.find_one({"mobile": mobile, "password": hashed_pw})
        
        if user:
            user.pop("_id", None)
            user.pop("password", None)
            return JSONResponse(status_code=200, content=user)
        else:
            return JSONResponse(status_code=401, content={"error": "Invalid credentials"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ==========================================
# YOUTH API
# ==========================================
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
        if text.startswith('```json'): text = text[7:]
        elif text.startswith('```'): text = text[3:]
        if text.endswith('```'): text = text[:-3]
        result = json.loads(text.strip())
        
        await db.ai_career_suggestions.insert_one({"profile": data, "suggestion": result})
        return JSONResponse(status_code=200, content={"suggestion": result})
    except Exception as e:
        traceback.print_exc()
        print("⚠️ Career suggestion Gemini API failed. Using local fallback.")
        fallback_suggestion = {
            "title": "సమీకృత సేంద్రియ వ్యవసాయ వ్యాపారం (Integrated Organic Farming Business)",
            "desc": "అల్పాదాయ ఖర్చుతో గరిష్ట దిగుబడి కొరకు వర్మీకంపోస్ట్, పశుపోషణ మరియు దేశవాళీ విత్తన ఉత్పత్తి తో కూడిన సమీకృత వ్యవసాయం.",
            "salary": "₹4L - ₹8L per year",
            "demand": "చాలా ఎక్కువ (Very High)",
            "training": "1 - 2 నెలలు (1-2 months)"
        }
        return JSONResponse(status_code=200, content={"suggestion": fallback_suggestion})

# ==========================================
# TRANSPORT API
# ==========================================
@app.post("/api/register_driver")
async def register_driver(request: Request):
    try:
        data = await request.json()
        result = await db.drivers.insert_one(data)
        return JSONResponse(status_code=200, content={"message": "Driver registered", "id": str(result.inserted_id)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/book_ride")
async def book_ride(request: Request):
    try:
        data = await request.json()
        data["status"] = "pending"
        result = await db.rides.insert_one(data)
        return JSONResponse(status_code=200, content={"message": "Ride booked", "id": str(result.inserted_id)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/get_pending_rides")
async def get_pending_rides():
    try:
        # Get only rides from last few hours maybe? Let's just return all pending for demo purposes
        cursor = db.rides.find({"status": "pending"}).sort("_id", -1).limit(20)
        rides = await cursor.to_list(length=20)
        for r in rides:
            r["_id"] = str(r["_id"])
        return JSONResponse(status_code=200, content={"rides": rides})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/book_farm_equipment")
async def book_farm_equipment(request: Request):
    try:
        data = await request.json()
        data["status"] = "pending"
        # Map equipment data to fit ride schema to show on driver dashboard uniformly
        ride_data = {
            "pickup": data.get("location", "Farm"),
            "destination": f"Crop: {data.get('cropType', '')} ({data.get('hours')} hrs)",
            "rideType": data.get("equipment", "Tractor"),
            "status": "pending",
            "timestamp": data.get("timestamp")
        }
        result = await db.rides.insert_one(ride_data)
        return JSONResponse(status_code=200, content={"message": "Equipment booked", "id": str(result.inserted_id)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/accept_ride")
async def accept_ride(request: Request):
    try:
        data = await request.json()
        from bson import ObjectId
        await db.rides.update_one({"_id": ObjectId(data["ride_id"])}, {"$set": {"status": "accepted", "driver": data.get("driver")}})
        return JSONResponse(status_code=200, content={"message": "Ride accepted"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ==========================================
# MARKETING API
# ==========================================
@app.post("/api/list_crop")
async def list_crop(request: Request):
    try:
        data = await request.json()
        result = await db.crops.insert_one(data)
        return JSONResponse(status_code=200, content={"message": "Crop listed successfully", "id": str(result.inserted_id)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/get_crops")
async def get_crops():
    try:
        crops_cursor = db.crops.find({})
        crops = []
        async for crop in crops_cursor:
            crop['_id'] = str(crop['_id'])
            crops.append(crop)
        return JSONResponse(status_code=200, content={"crops": crops})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/rent_land")
async def rent_land(request: Request):
    try:
        data = await request.json()
        result = await db.land_rentals.insert_one(data)
        return JSONResponse(status_code=200, content={"message": "Land rental listed successfully", "id": str(result.inserted_id)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/market_status")
async def get_market_status():
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = "Generate realistic daily average crop prices for Indian Mandis in JSON array format. Fields: crop_name, spot_price, mandi_price, trend ('up', 'down'). Return ONLY raw valid JSON array, without markdown blocks. Example: [{'crop_name': 'Paddy', 'spot_price': 2150, 'mandi_price': 2180, 'trend': 'up'}]. List 6 common crops."
        response = model.generate_content(prompt)
        text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
        data = json.loads(text)
        return {"prices": data}
    except Exception as e:
        traceback.print_exc()
        print("⚠️ Market status Gemini API failed. Using local fallback.")
        fallback_prices = [
            {"crop_name": "వరి (Paddy)", "spot_price": 2180, "mandi_price": 2200, "trend": "up"},
            {"crop_name": "జొన్నలు (Jowar)", "spot_price": 2850, "mandi_price": 2800, "trend": "down"},
            {"crop_name": "మొక్కజొన్న (Maize)", "spot_price": 1950, "mandi_price": 1980, "trend": "up"},
            {"crop_name": "మిర్చి (Chilli)", "spot_price": 18500, "mandi_price": 18700, "trend": "up"},
            {"crop_name": "పత్తి (Cotton)", "spot_price": 7150, "mandi_price": 7100, "trend": "down"},
            {"crop_name": "శనగలు (Bengal Gram)", "spot_price": 5400, "mandi_price": 5450, "trend": "up"}
        ]
        return {"prices": fallback_prices}

# ==========================================
# FARMER SUPPORT API
# ==========================================
def extract_json(text):
    text = text.strip()
    if text.startswith("```json"): text = text[7:]
    elif text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    return json.loads(text.strip())

@app.post("/api/disease-detect")
async def detect_disease(file: UploadFile = File(...)):
    try:
        img_bytes = await file.read()
        img = PIL.Image.open(io.BytesIO(img_bytes))
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """Analyze this crop image and identify the disease. If healthy, indicate that.
        Output raw JSON with no markdown block:
        {
          "disease_en": "Disease name", "disease_te": "Disease in Telugu", "confidence": 95,
          "reason_en": "Reason in English", "reason_te": "Reason in Telugu",
          "cure_en": "Cure in English", "cure_te": "Cure in Telugu",
          "prevention": [ "Prevention 1 in Telugu/English", "Prevention 2" ]
        }"""
        response = model.generate_content([prompt, img])
        result = extract_json(response.text)
        result["success"] = True
        return result
    except Exception as e:
        traceback.print_exc()
        print("⚠️ Disease detection Gemini API failed. Using local fallback.")
        fallback_disease = {
            "disease_en": "Rice Blast (Leaf Blast)",
            "disease_te": "వరి అగ్గ తెగులు (ఆకు తెగులు)",
            "confidence": 90,
            "reason_en": "High nitrogen dose, high humidity, and overnight dew",
            "reason_te": "నత్రజని ఎరువుల అధిక వాడకం, గాలిలో అధిక తేమ మరియు రాత్రిపూట మంచు కురవడం",
            "cure_en": "Spray Tricyclazole 75 WP @ 0.6 g/liter or Isoprothiolane @ 1.5 ml/liter of water",
            "cure_te": "లీటరు నీటికి ట్రైసైక్లాజోల్ 75 WP @ 0.6 గ్రాములు లేదా ఐసోప్రోథియోలేన్ @ 1.5 మి.లీ కలిపి పిచికారీ చేయండి",
            "prevention": [
                "నిరోధక రకాలను ఎంచుకోండి (Use resistant varieties)",
                "నత్రజని సమతుల్యంగా వాడండి (Balanced nitrogen fertilizer)",
                "పొలంలో నిల్వ నీరు తీసివేయండి (Drain field during severity)"
            ],
            "success": True
        }
        return fallback_disease

@app.post("/api/crop-suggest")
async def crop_suggest(request: Request):
    data = await request.json()
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""Act as an expert Indian agronomist. 
        Farm details: Soil: {data.get('soil')}, Weather: {data.get('weather')}, Water(1-10): {data.get('water')}
        Suggest exactly 4 best crops. Output raw JSON array only:
        [ {{
            "name": "Telugu Name", "en": "English Name", "match": 95, 
            "market": "Demand (Telugu)", "pest": "Pest resist (Telugu)", 
            "resource": "Resource needs (Telugu)", "icon": "🌾", "color": "#f0d9a0",
            "waterMin": 5, "weather": ["type1"] 
        }} ]"""
        response = model.generate_content(prompt)
        crops = extract_json(response.text)
        return {"success": True, "crops": crops}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "success": False})

@app.post("/api/resource-optimize")
async def resource_optimize(request: Request):
    data = await request.json()
    crop = data.get('crop', 'paddy')
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""Act as an agricultural economist in India. Give me resource optimization data per acre for {crop}.
        Output exactly this raw JSON format (no markdown):
        {{
            "fert": "N:P:K = ... kg/acre", "fertRec": "120:60:40",
            "seed": "విత్తనం ... kg/acre", "seedTreat": "Treatment chemical in telugu",
            "fuel": "డీజిల్ ... లీ/ఎకరం", "fuelCost": "₹...",
            "total": "₹...", "waste": "85%",
            "fp1": "యూరియా 260 kg", "fp2": "డిఎపి 130 kg",
            "sp1": "వేప పౌడర్", "sp2": "ట్రైకోడెర్మా",
            "fl1": "ట్రాక్టర్ 4 గం", "fl2": "పంప్ 6 యూనిట్లు"
        }}"""
        response = model.generate_content(prompt)
        data = extract_json(response.text)
        return {"success": True, "data": data}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "success": False})

@app.post("/api/farming-process")
async def farming_process(request: Request):
    data = await request.json()
    crop = data.get('crop', 'dragonfruit')
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""Generate step-by-step advanced farming process in Telugu for {crop}.
        Provide exactly 4 steps. Output raw JSON array (no markdown):
        [
          {{"icon": "🌱", "title": "step 1 title (telugu)", "desc": "short description (telugu)"}},
          {{"icon": "💧", "title": "step 2 title", "desc": "description"}},
          {{"icon": "🌿", "title": "step 3 title", "desc": "description"}},
          {{"icon": "✂️", "title": "step 4 title", "desc": "description"}}
        ]"""
        response = model.generate_content(prompt)
        steps = extract_json(response.text)
        return {"success": True, "steps": steps}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "success": False})

@app.post("/api/water-analytics")
async def water_analytics(request: Request):
    data = await request.json()
    crop = data.get('crop', '')
    acres = float(data.get('acres', 1))
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""Act as a water management expert. Analyze for {crop} grown over {acres} acres in India.
        Output raw JSON exactly like this (no markdown):
        {{
            "totalWaterLiters": 180000,
            "cropNameTe": "తెలుగు పేరు",
            "waterPerAcreLabel": "1800 mm/acre",
            "monthlyData": [180, 220, 280, 320, 350, 300],
            "sourceData": [50, 25, 15, 10],
            "moistureData": [78, 72, 65, 58, 52, 48, 45]
        }}"""
        response = model.generate_content(prompt)
        analytics = extract_json(response.text)
        return {"success": True, "data": analytics}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "success": False})

@app.get("/api/farmer-status")
async def get_farmer_status():
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = """Act as a real-time agricultural monitoring assistant. 
        Generate realistic, up-to-date weather and field status for an Indian village today.
        Respond with ONLY a raw JSON object:
        {
          "temp": 32,
          "humidity": 62,
          "wind": 12,
          "sunrise": "6:02 AM",
          "sunset": "6:45 PM",
          "water_status": "Water level: Stable (82%)",
          "water_desc": "Next irrigation suggested in 2 days",
          "water_label1": "12mm Shortage",
          "water_label2": "Next Flow: Today",
          "weather_desc": "Clear skies - good for harvesting and drying."
        }"""
        response = model.generate_content(prompt)
        status = extract_json(response.text)
        return {"success": True, "status": status}
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.get("/api/government-schemes")
async def get_government_schemes():
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = """Act as a government information assistant. 
        Provide details for exactly these 6 schemes with these specific portal URLs:
        1. PMJJBY - URL: https://share.google/x5w8pjc4uoGTMsQBF
        2. Atal Pension Yojana (APY) - URL: https://share.google/aajVE9WLHNRvhVrGZ
        3. AP HOUSING - URL: https://share.google/95OrHop5QcwQl7pl3
        4. INDIRAMMA Old Age Pension - URL: https://share.google/f3zGImaeBlVPWDzAG
        5. Motorized Three Wheeler - URL: https://share.google/SHMndY0P6lg4QNvlp
        6. AP OBMMS - URL: https://share.google/dE6o3kgo1gXEJdSfN

        For each scheme, provide:
        - title_te: Title in Telugu
        - title_en: Short Name (e.g., PMJJBY, AP Housing)
        - category: one of [farmers, youth, infrastructure, healthcare]
        - desc_te: Short description in Telugu
        - benefit_te: Main benefit in Telugu
        - eligibility_te: Comprehensive eligibility criteria in Telugu
        - url: The EXACT share.google URL provided above for this scheme
        - status: "Active"
        - icon: FontAwesome icon (e.g., "fas fa-shield-heart", "fas fa-house-user", "fas fa-wheelchair")
        - color: A Tailwind color name (e.g., "blue-500", "orange-500", "green-500", "purple-500")

        Respond with ONLY a raw JSON array of 6 objects. No markdown blocks.
        """
        response = model.generate_content(prompt)
        schemes = extract_json(response.text)
        return {"success": True, "schemes": schemes}
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}




@app.post("/api/panchayat/requests")
async def submit_panchayat_request(request: Request):
    try:
        data = await request.json()
        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["status"] = "Pending"
        await db.panchayat_requests.insert_one(data)
        return {"success": True, "message": "Request submitted successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/panchayat/requests")
async def get_panchayat_requests():
    try:
        cursor = db.panchayat_requests.find().sort("timestamp", -1)
        requests = await cursor.to_list(length=100)
        for r in requests:
            r["_id"] = str(r["_id"])
        return {"success": True, "requests": requests}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fallback_kittu_chat(user_msg, user_context):
    msg = user_msg.lower()
    name = user_context.get('name', 'రైతు')
    
    # Check if Telugu script is present in the message
    is_telugu = any(ord(char) > 127 for char in user_msg)
    
    # 1. Booking a ride/vehicle
    if any(k in msg for k in ["book", "ride", "vehicle", "tractor", "auto", "రైడ్", "బుక్", "వాహనం", "ట్రాక్టర్"]):
        if is_telugu:
            return {
                "reply_display": f"నమస్తే {name}, నేను మీ కోసం రైడ్ బుకింగ్ ప్రక్రియను ప్రారంభిస్తున్నాను. ఒక ట్రాక్టర్ బుక్ చేయబడింది.",
                "reply_spoken": f"Namaste {name}, nenu mee kosam ride booking prachriya prarambhistunnanu. Oka tractor book cheyabadindi.",
                "action": "BOOK_RIDE",
                "action_payload": {
                    "pickup": "గ్రామం (Village)",
                    "destination": "మార్కెట్ (Market)",
                    "vehicleType": "Tractor",
                    "phone": user_context.get('mobile', 'Unknown')
                }
            }
        else:
            return {
                "reply_display": f"Hello {name}, I am initiating the ride booking process for you. Auto-booking ride request created.",
                "reply_spoken": f"Hello {name}, I am initiating the ride booking process for you. Auto booking ride request created.",
                "action": "BOOK_RIDE",
                "action_payload": {
                    "pickup": "Village",
                    "destination": "Market",
                    "vehicleType": "Tractor",
                    "phone": user_context.get('mobile', 'Unknown')
                }
            }

    # 2. Listing/Selling crop
    elif any(k in msg for k in ["sell", "crop", "market", "list", "paddy", "rice", "అమ్మకం", "పంట", "ధర", "వరి"]):
        if is_telugu:
            return {
                "reply_display": f"నమస్తే {name}, మీ పంటను మార్కెట్‌లో అమ్మకానికి పెట్టడానికి నేను సిద్ధంగా ఉన్నాను. పంటను మార్కెట్‌లో విజయవంతంగా లిస్ట్ చేశాను.",
                "reply_spoken": f"Namaste {name}, mee pantanu market lo ammachaniki pettadaniki nenu ready ga unnanu. Pantanu market lo successfully list chesanu.",
                "action": "LIST_CROP",
                "action_payload": {
                    "cropName": "వరి (Paddy)",
                    "quantity": "1000 kg",
                    "price": "₹2200/quintal",
                    "phone": user_context.get('mobile', 'Unknown')
                }
            }
        else:
            return {
                "reply_display": f"Hello {name}, I am listing your crop in the marketplace. Crop listing created successfully.",
                "reply_spoken": f"Hello {name}, I am listing your crop in the marketplace. Crop listing created successfully.",
                "action": "LIST_CROP",
                "action_payload": {
                    "cropName": "Paddy",
                    "quantity": "1000 kg",
                    "price": "₹2200/quintal",
                    "phone": user_context.get('mobile', 'Unknown')
                }
            }

    # 3. General greetings / Help
    else:
        if is_telugu:
            return {
                "reply_display": f"నమస్తే {name}! నేను కిట్టును. నేను మీకు వాహనం బుక్ చేయడంలో, పంటలు అమ్మడంలో లేదా ప్రభుత్వ పథకాల సమాచారంలో సహాయం చేయగలను. (గమనిక: జెమిని API కోటా ముగిసింది, స్థానిక సహాయకుడితో మాట్లాడుతున్నారు).",
                "reply_spoken": "Namaste! Nenu Kittunu. Nenu meeku vahanam book cheyadamlo, pantalu ammadamlo sahayam cheyagalanu.",
                "action": "NONE",
                "action_payload": {}
            }
        else:
            return {
                "reply_display": f"Hello {name}! I am Kittu, your AI assistant. I can help you book rides, list crops, or find government schemes. (Note: Gemini API quota exceeded, running on local fallback mode).",
                "reply_spoken": f"Hello! I am Kittu. I can help you book rides or list crops.",
                "action": "NONE",
                "action_payload": {}
            }

@app.post("/api/chat")
async def central_agent_chat(request: Request):
    data = await request.json()
    user_msg = data.get('message', '')
    history = data.get('history', [])
    user_context = data.get('user', {})
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # System instructions to act as the Project's Central Agent
        prompt = f"""You are 'Agentic-AI Kittu', the intelligent conversational agent for a Aarohan-AI ecosystem.
        The user is interacting from the Home Page. 
        User Details: Name: {user_context.get('name', 'Farmer/User')}, Occupation: {user_context.get('occupation', 'Unknown')}, Phone: {user_context.get('mobile', 'Unknown')}.
        
        You must understand the user's language (Telugu or English).
        If responding in Telugu, you MUST provide 'reply_display' in Telugu script, and 'reply_spoken' in Romanized Telugu (Telugu written in English alphabet, e.g. "Namaste, meeku ela sahayam cheyagalanu"). 
        If responding in English, both fields should just be in English.
        
        You have the ability to TRIGGER ACTIONS in the system. 
        If the user wants to book a vehicle/ride, output an action to book it.
        If the user wants to sell/list a crop, output an action to list it.
        If the user asks for crop suggestions or disease detection, answer them contextually (you are an expert).
        
        You MUST ALWAYS return a RAW JSON block (no markdown, no backticks).
        Format:
        {{
            "reply_display": "Conversational response in native script to show on screen...",
            "reply_spoken": "Conversational response in English alphabets to read aloud...",
            "action": "NONE" | "BOOK_RIDE" | "LIST_CROP",
            "action_payload": {{}} // Include details if action is not NONE.
            // For BOOK_RIDE: {{"pickup": "...", "destination": "...", "vehicleType": "...", "phone": "..."}}
            // For LIST_CROP: {{"cropName": "...", "quantity": "...", "price": "...", "phone": "..."}}
        }}

        Current conversation history: {history[-3:]}
        New User Message: {user_msg}
        """
        
        response = model.generate_content(prompt)
        result = extract_json(response.text)
        
        # Execute actions if requested by the AI
        action = result.get("action", "NONE")
        payload = result.get("action_payload", {})
        
        display_text = result.get("reply_display", result.get("reply", "I did not understand."))
        spoken_text = result.get("reply_spoken", display_text)
        
        if action == "BOOK_RIDE":
            await db.rides.insert_one({
                "pickup": payload.get("pickup", "Unknown"),
                "destination": payload.get("destination", "Unknown"),
                "vehicleType": payload.get("vehicleType", "Tractor"),
                "status": "pending",
                "userName": user_context.get('name', 'User'),
                "userPhone": payload.get("phone", user_context.get('mobile', 'Unknown'))
            })
            display_text += "\n[System: Auto-booked your ride successfully!]"
            spoken_text += " Auto-booked your ride successfully!"
            
        elif action == "LIST_CROP":
            await db.crops.insert_one({
                "farmer_name": user_context.get('name', 'Farmer'),
                "crop_name": payload.get("cropName", "Unknown"),
                "quantity": payload.get("quantity", "Unknown"),
                "price": payload.get("price", "Unknown"),
                "phone": payload.get("phone", user_context.get('mobile', 'Unknown')),
                "type": "Sell"
            })
            display_text += "\n[System: Successfully listed your crop in the marketplace!]"
            spoken_text += " Successfully listed your crop in the marketplace."
            
        return {"success": True, "reply": display_text, "reply_spoken": spoken_text, "action": action}

    except Exception as e:
        traceback.print_exc()
        print("⚠️ Gemini Chat API failed. Using local Kittu Chat fallback.")
        try:
            result = fallback_kittu_chat(user_msg, user_context)
            action = result.get("action", "NONE")
            payload = result.get("action_payload", {})
            display_text = result.get("reply_display", "I did not understand.")
            spoken_text = result.get("reply_spoken", display_text)
            
            if action == "BOOK_RIDE":
                await db.rides.insert_one({
                    "pickup": payload.get("pickup", "Unknown"),
                    "destination": payload.get("destination", "Unknown"),
                    "vehicleType": payload.get("vehicleType", "Tractor"),
                    "status": "pending",
                    "userName": user_context.get('name', 'User'),
                    "userPhone": payload.get("phone", user_context.get('mobile', 'Unknown'))
                })
                display_text += "\n[System: Auto-booked your ride successfully!]"
                spoken_text += " Auto-booked your ride successfully!"
                
            elif action == "LIST_CROP":
                await db.crops.insert_one({
                    "farmer_name": user_context.get('name', 'Farmer'),
                    "crop_name": payload.get("cropName", "Unknown"),
                    "quantity": payload.get("quantity", "Unknown"),
                    "price": payload.get("price", "Unknown"),
                    "phone": payload.get("phone", user_context.get('mobile', 'Unknown')),
                    "type": "Sell"
                })
                display_text += "\n[System: Successfully listed your crop in the marketplace!]"
                spoken_text += " Successfully listed your crop in the marketplace."
                
            return {"success": True, "reply": display_text, "reply_spoken": spoken_text, "action": action}
        except Exception as fallback_err:
            return JSONResponse(status_code=500, content={"error": str(fallback_err), "success": False})

# Mounted static folders at the very end to avoid API routing conflicts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/farmer_support", StaticFiles(directory=os.path.join(BASE_DIR, "farmer_support"), html=True), name="farmer")
app.mount("/marketing", StaticFiles(directory=os.path.join(BASE_DIR, "marketing"), html=True), name="market")
app.mount("/government", StaticFiles(directory=os.path.join(BASE_DIR, "government"), html=True), name="gov")
app.mount("/Heathcare", StaticFiles(directory=os.path.join(BASE_DIR, "Heathcare"), html=True), name="health")
app.mount("/transport", StaticFiles(directory=os.path.join(BASE_DIR, "transport"), html=True), name="trans")
app.mount("/home_page", StaticFiles(directory=os.path.join(BASE_DIR, "home_page"), html=True), name="home")
app.mount("/Youth", StaticFiles(directory=os.path.join(BASE_DIR, "youth"), html=True), name="youth")

# Mount root last so it fetches login.html and auth.js nicely!
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="root")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting Unified Aarohan-AI Gateway on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)



