# chatbot_gui.py

import csv
import numpy as np
import subprocess
import platform
import speech_recognition as sr

from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# =====================================================
# LOAD CSV DATA (category + question + answer)
# =====================================================

def load_qa_from_csv(filename):
    questions = []
    answers = []
    categories = []

    try:
        with open(filename, newline='', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = row.get("Category", "").strip()
                question = row.get("Question", "").strip()
                answer = row.get("Answer", "").strip()

                if question and answer:
                    categories.append(category)
                    questions.append(question)
                    answers.append(answer)

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return [], [], []

    return questions, answers, categories


questions, answers, categories = load_qa_from_csv("academic_policies.csv")

if not questions:
    print("No questions loaded! Check your CSV file.")
    exit()

# =====================================================
# INITIALIZE MODELS
# =====================================================

print("Loading models... Please wait...")

# TF-IDF
vectorizer = TfidfVectorizer()
question_vectors_tfidf = vectorizer.fit_transform(questions)

# SBERT
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
question_embeddings_sbert = sbert_model.encode(questions, convert_to_tensor=False)

print("Models loaded successfully!")

# =====================================================
# VOICE COMPONENTS (System-based TTS)
# =====================================================

recognizer = sr.Recognizer()

def speak(text):
    """Platform-independent text-to-speech using system commands - BLOCKING VERSION"""
    try:
        system = platform.system()
        
        if system == 'Windows':
            # Windows PowerShell TTS - using call() instead of Popen() for blocking execution
            command = f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"'
            subprocess.call(command, shell=True)
            
        elif system == 'Darwin':  # macOS
            subprocess.call(['say', text])
            
        else:  # Linux
            subprocess.call(['espeak', text])
            
        return True
    except Exception as e:
        print(f"TTS Error: {e}")
        return False

def listen():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = recognizer.recognize_google(audio)
            return {"success": True, "text": text}

        except sr.UnknownValueError:
            return {"success": False, "error": "Could not understand audio"}

        except sr.RequestError as e:
            return {"success": False, "error": str(e)}

        except sr.WaitTimeoutError:
            return {"success": False, "error": "No speech detected"}

# =====================================================
# CHATBOT LOGIC (TF-IDF + SBERT + CATEGORY)
# =====================================================

def chatbot_response(user_input):
    # TF-IDF similarity
    user_vec_tfidf = vectorizer.transform([user_input])
    sim_tfidf = cosine_similarity(user_vec_tfidf, question_vectors_tfidf)[0]

    # SBERT similarity
    user_embed = sbert_model.encode([user_input], convert_to_tensor=False)
    sim_sbert = cosine_similarity(user_embed, question_embeddings_sbert)[0]

    # Hybrid weighting
    weight_tfidf = 0.3
    weight_sbert = 0.7
    combined_scores = (weight_tfidf * sim_tfidf) + (weight_sbert * sim_sbert)

    best_index = np.argmax(combined_scores)
    best_score = combined_scores[best_index]

    if best_score < 0.35:
        return (
            "Sorry, I don't understand your question. "
            "Please ask about GPA, attendance, fees, or semester policies."
        )
    else:
        # Return only the answer, without category
        return answers[best_index]

# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")

    if user_input:
        response = chatbot_response(user_input)
        return jsonify({"response": response})

    return jsonify({"response": "Please enter a question."})

@app.route("/voice", methods=["POST"])
def voice():
    result = listen()

    if result["success"]:
        response = chatbot_response(result["text"])
        # Speak only the answer (no category to split now)
        speak(response)
        return jsonify({
            "success": True,
            "text": result["text"],
            "response": response
        })
    else:
        return jsonify({
            "success": False,
            "error": result["error"]
        })

@app.route("/speak", methods=["POST"])
def speak_text():
    data = request.json
    text = data.get("text", "")

    if text:
        # Speak the full text without splitting
        success = speak(text)
        return jsonify({"success": success})

    return jsonify({"success": False})

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    print("=" * 65)
    print("🎓 Academic Policy Chatbot (CSV + TF-IDF + SBERT)")
    print("=" * 65)
    print("Server running at http://127.0.0.1:5000")
    print("=" * 65)
    app.run(debug=True, use_reloader=False)