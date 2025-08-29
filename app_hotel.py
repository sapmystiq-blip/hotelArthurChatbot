from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import os
from openai import OpenAI
import json

from kb_utils import kb_to_text   # reuse your helper

app = Flask(__name__, static_folder='static')

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Env-driven knowledge & prompt paths (fallbacks point to Hotel Arthur files)
HOTEL_KNOWLEDGE_PATH = os.getenv("HOTEL_KNOWLEDGE_PATH", "hotel_knowledge_arthur.json")
PROMPT_PATH = os.getenv("PROMPT_PATH", "PROMPT.md")

# Load knowledge base
try:
    with open(HOTEL_KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)
except Exception as e:
    print("Failed to load knowledge base:", e)
    knowledge_base = {}

# Load prompt
try:
    with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
        base_prompt = f.read()
except Exception as e:
    print("Failed to load PROMPT.md:", e)
    base_prompt = "You are a hotel assistant in Helsinki. Answer concisely using the provided knowledge."

# Serve index.html (try templates/ first, then project root)
@app.route('/')
def index():
    if os.path.exists(os.path.join('templates', 'index.html')):
        return send_from_directory('templates', 'index.html')
    return send_from_directory('.', 'index.html')

# Static assets (kept as-is)
@app.route('/style.css')
def style():
    # try static/ first, else root
    if os.path.exists(os.path.join('static', 'style.css')):
        return send_from_directory('static', 'style.css')
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def script():
    if os.path.exists(os.path.join('static', 'script.js')):
        return send_from_directory('static', 'script.js')
    return send_from_directory('.', 'script.js')

# Health check
@app.route('/healthz')
def healthz():
    hotel = (knowledge_base.get("meta") or {}).get("name", "Hotel")
    return jsonify({"ok": True, "hotel": hotel})

# Chat endpoint
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get('message') or "").strip()
        if not user_message:
            return jsonify({"error": "Missing 'message'"}), 400

        system_prompt = f"{base_prompt}\n\nHotel knowledge:\n{kb_to_text(knowledge_base)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        )

        answer = response.choices[0].message.content
        return jsonify({"reply": answer})
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
