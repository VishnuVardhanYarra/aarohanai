import os

files_to_update = [
    "home_page/index.html",
    "marketing/index.html",
    "youth/seventh.html",
    "transport/index.html",
    "Heathcare/index.html",
    "Heathcare/doctor.html",
    "government/panchayat.html",
    "government/smartvillage.html",
    "government\panchayat_admin.html",
    "farmer_support/village.html",
    "farmer_support/diseasedetuction.html",
    "farmer_support/waterAnalytics.html",
    "farmer_support/resouceallocation.html",
    "farmer_support/AdvancedFarming.html",
    "farmer_support/Crop.html"
]

for filepath in files_to_update:
    path = os.path.join(r"c:\Users\yarra\Desktop\aarohan_1", filepath)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        if "auth.js" not in content and "</body>" in content:
            content = content.replace("</body>", f'\t<script src="../auth.js"></script>\n</body>')
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Injected into {filepath}")
            except Exception as e:
                print(f"Failed to write {filepath}: {e}")
        else:
            print(f"Skipped {filepath} (Already has auth.js or no </body>)")
    else:
        print(f"Not found: {filepath}")



