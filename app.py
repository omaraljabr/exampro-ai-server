import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

KEYS = ["strengths", "improvement", "recommendations", "trainingPlan"]


@app.route("/")
def home():
    return "AI server is running"


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", [])
    exam_name = data.get("examName", "")

    if not answers:
        return jsonify({"error": "No answers provided"}), 400

    if not GEMINI_API_KEY:
        return jsonify({"error": "Server is missing the API key"}), 500

    lines = []
    for i, a in enumerate(answers, 1):
        status = "صحيحة" if a.get("isCorrect") else "خاطئة"
        lines.append(
            f"{i}. السؤال: {a.get('question')}\n"
            f"   إجابة الطالب: {a.get('studentAnswer')}\n"
            f"   الإجابة الصحيحة: {a.get('correctAnswer')}\n"
            f"   النتيجة: {status}"
        )

    prompt = (
        f"أنت مدرب خبير. حلل أداء طالب في امتحان بعنوان: {exam_name}\n\n"
        + "\n".join(lines)
        + "\n\nاكتب التحليل بالعربية، وأرجع JSON فقط بهذه الحقول، وكل قيمة نص عادي (string):\n"
        "strengths: نقاط القوة\n"
        "improvement: ما يحتاج الطالب إتقانه\n"
        "recommendations: التوصيات\n"
        "trainingPlan: خطة تطوير قصيرة"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=25,
        )
    except requests.RequestException:
        return jsonify({"error": "Could not reach Gemini"}), 502

    if response.status_code != 200:
        print("Gemini error:", response.status_code, response.text[:300])
        return jsonify({"error": "Gemini request failed"}), 502

    try:
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except Exception:
        return jsonify({"error": "Bad response from Gemini"}), 502

    clean = {}
    for key in KEYS:
        value = result.get(key, "")
        if isinstance(value, list):
            value = "\n".join(str(v) for v in value)
        clean[key] = str(value)

    return jsonify(clean)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
