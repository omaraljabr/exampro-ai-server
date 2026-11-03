import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


@app.route("/")
def home():
    return "AI server is running"


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    if not GEMINI_API_KEY:
        return jsonify({"error": "Server is missing the API key"}), 500

    payload = {"contents": [{"parts": [{"text": text}]}]}
    response = requests.post(
        GEMINI_URL,
        params={"key": GEMINI_API_KEY},
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        return jsonify({"error": "Gemini request failed"}), 502

    result = response.json()
    answer = result["candidates"][0]["content"]["parts"][0]["text"]
    return jsonify({"answer": answer})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
