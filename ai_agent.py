import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import os # Add this import at the top

# ==========================================
# SECURE CONFIGURATION
# ==========================================
YOUR_PORTAL_URL = "http://YOUR_WEBSITE_DOMAIN.infinityfreeapp.com/auth.php" 

# Pulling secrets securely from GitHub Environment Variables!
AI_SECRET_TOKEN = os.environ.get("AI_SECRET_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY or not AI_SECRET_TOKEN:
    raise ValueError("🚨 CRITICAL: Missing API Keys in Environment Variables!")




def fetch_latest_news():
    print("🌍 Scanning Google News for West Bengal Gov updates...")
    # RSS Feed searching specifically for WB jobs, scholarships, and schemes
    url = "https://news.google.com/rss/search?q=West+Bengal+government+jobs+OR+scholarships+OR+schemes&hl=en-IN&gl=IN&ceid=IN:en"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        news_items = []
        # Get the top 5 latest news items
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            desc = item.find('description').text
            news_items.append(f"TITLE: {title}\nDETAILS: {desc}")
            
        return "\n\n---\n\n".join(news_items)
    except Exception as e:
        print("❌ Failed to fetch news:", e)
        return ""

def process_with_gemini(news_text):
    print("🧠 Asking Gemini AI to analyze and format the news...")
    
    prompt = f"""
    You are an AI data parser for a West Bengal Government Portal.
    Read the following news summaries and determine if there is a NEW, SPECIFIC Job, Scholarship, Scheme, or College Admission announced.
    
    If there is NO specific concrete announcement, return exactly the word: NONE
    
    If there IS a valid announcement, extract the details into a STRICT JSON object using exactly one of these formats:
    
    For a Job: {{"type": "job", "data": {{"title": "...", "department": "...", "description": "...", "requirements": "...", "age_limit": "...", "salary": "...", "qualification": "...", "link": "..."}}}}
    For a Scholarship: {{"type": "scholarship", "data": {{"title": "...", "description": "...", "requirements": "...", "age_limit": "...", "income_limit": "...", "min_marks": "...", "link": "..."}}}}
    For a Scheme: {{"type": "scheme", "data": {{"title": "...", "description": "...", "requirements": "...", "age_limit": "...", "income_limit": "...", "documents": "...", "link": "..."}}}}
    
    ONLY output the JSON. Do not include markdown formatting (like ```json).
    
    News to parse:
    {news_text}
    """

    url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=){GEMINI_API_KEY}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        ai_reply = result['candidates'][0]['content']['parts'][0]['text'].strip()
        
        if ai_reply == "NONE":
            print("ℹ️ Gemini found no concrete updates to post today.")
            return None
            
        # Clean up any accidental markdown blocks Gemini might add
        ai_reply = re.sub(r'^```json\s*', '', ai_reply)
        ai_reply = re.sub(r'^```\s*', '', ai_reply)
        ai_reply = re.sub(r'\s*```$', '', ai_reply)
        
        parsed_json = json.loads(ai_reply)
        return parsed_json
    except Exception as e:
        print("❌ AI Processing failed:", e)
        return None

def publish_to_portal(ai_data):
    if not ai_data: return
    
    record_type = ai_data.get("type")
    payload = ai_data.get("data")
    
    if not record_type or not payload:
        print("❌ Invalid AI Data format.")
        return
        
    print(f"🚀 Publishing a new {record_type.upper()} to WB LINKBOX...")
    
    action_map = {
        "job": "add_job",
        "scholarship": "add_scholarship",
        "scheme": "add_scheme",
        "college": "add_college"
    }
    
    target_action = action_map.get(record_type)
    url = f"{YOUR_PORTAL_URL}?action={target_action}"
    
    req_data = json.dumps(payload).encode('utf-8')
    # THIS IS THE SECRET TOKEN BYPASSING NORMAL LOGINS
    req = urllib.request.Request(url, data=req_data, headers={
        'Content-Type': 'application/json',
        'X-AI-TOKEN': AI_SECRET_TOKEN
    })
    
    try:
        response = urllib.request.urlopen(req)
        res_json = json.loads(response.read())
        if res_json.get("success"):
            print("✅ Successfully published to database!")
        else:
            print("❌ Server rejected the post:", res_json)
    except Exception as e:
        print("❌ Failed to connect to server:", e)

if __name__ == "__main__":
    print("Starting Autonomous Agent...")
    news = fetch_latest_news()
    if news:
        extracted_data = process_with_gemini(news)
        publish_to_portal(extracted_data)
    print("Agent execution complete.")
