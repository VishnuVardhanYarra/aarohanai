import os
import json
import io
import traceback
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import PIL.Image

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyCJ0knNbRxw6DKGcZYk7VYPlSUFIKjTcTc")
if api_key:
    genai.configure(api_key=api_key)

# --- Frontend Page Routes ---
@app.route('/')
def home(): return render_template('village.html')

@app.route('/village.html')
def village(): return render_template('village.html')

@app.route('/diseasedetuction.html')
def disease(): return render_template('diseasedetuction.html')

@app.route('/waterAnalytics.html')
def water(): return render_template('waterAnalytics.html')

@app.route('/resouceallocation.html')
def resource(): return render_template('resouceallocation.html')

@app.route('/AdvancedFarming.html')
def farming(): return render_template('AdvancedFarming.html')

@app.route('/Crop.html')
def crop(): return render_template('Crop.html')

# --- Backend API Endpoints Using Google Gemini API ---

def extract_json(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())

@app.route('/api/disease-detect', methods=['POST'])
def detect_disease():
    if not api_key: return jsonify({"error": "No API Key", "success": False}), 500
    if 'file' not in request.files: return jsonify({"error": "No file", "success": False}), 400
        
    file = request.files['file']
    try:
        img_bytes = file.read()
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
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/crop-suggest', methods=['POST'])
def crop_suggest():
    if not api_key: return jsonify({"error": "No API Key", "success": False}), 500
    data = request.json
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
        return jsonify({"success": True, "crops": crops})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/resource-optimize', methods=['POST'])
def resource_optimize():
    if not api_key: return jsonify({"error": "No API Key", "success": False}), 500
    crop = request.json.get('crop', 'paddy')
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
        return jsonify({"success": True, "data": data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/farming-process', methods=['POST'])
def farming_process():
    if not api_key: return jsonify({"error": "No API Key", "success": False}), 500
    crop = request.json.get('crop', 'dragonfruit')
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
        return jsonify({"success": True, "steps": steps})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/water-analytics', methods=['POST'])
def water_analytics():
    if not api_key: return jsonify({"error": "No API Key", "success": False}), 500
    data = request.json
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
        return jsonify({"success": True, "data": analytics})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

if __name__ == '__main__':
    print("Starting Aarohan Farmer Hub Backend Server with Google Gemini AI...")
    if not api_key: print("WARNING: GEMINI_API_KEY is not set.")
    print("Listening on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)



