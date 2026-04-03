from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# wordfreq for real corpus-based frequency scores
try:
    from wordfreq import zipf_frequency
    WORDFREQ_AVAILABLE = True
except ImportError:
    WORDFREQ_AVAILABLE = False

app = Flask(__name__, static_folder="static")
CORS(app)

# =========================================
# Difficulty Function
# =========================================
def get_difficulty_level(score):
    if score <= 6:
        return "Easy"
    elif score <= 13:
        return "Medium"
    else:
        return "Hard"

# =========================================
# RULES
# =========================================
def word_length_rule(word):
    length = len(word)
    if length <= 3:
        score = 0
    elif 4 <= length <= 6:
        score = 1
    else:
        score = 2
    return {"rule": "Word Length", "score": score}

def visually_confusable_rule(word):
    pairs = [['b','d'],['p','q'],['m','n'],['i','l']]
    found = set()
    for pair in pairs:
        for letter in word.lower():
            if letter in pair:
                found.add(letter)
    return {"rule": "Confusable Letters", "score": min(len(found), 2)}

def special_letters_rule(word):
    score = 0
    word = word.lower()
    for i in range(len(word)-1):
        if word[i] == 'c' and word[i+1] in ['e','i','y']:
            score += 1
    return {"rule": "Special Letters", "score": min(score, 2)}

def diphthongs_rule(word):
    dips = ["aw","ew","ow"]
    score = sum([1 for d in dips if d in word.lower()])
    return {"rule": "Diphthongs", "score": min(score, 2)}

def vowel_team_rule(word):
    teams = ["ea","ou","ie"]
    score = sum([1 for t in teams if t in word.lower()])
    return {"rule": "Vowel Teams", "score": min(score, 2)}

def magic_e_rule(word):
    if len(word) >= 3 and word[-1] == 'e':
        return {"rule": "Magic E", "score": 1}
    return {"rule": "Magic E", "score": 0}

def digraphs_rule(word):
    g = ['sh','ch','th']
    score = sum([1 for x in g if x in word])
    return {"rule": "Digraphs", "score": min(score, 2)}

def trigraphs_rule(word):
    g = ['igh','tch']
    score = sum([1 for x in g if x in word])
    return {"rule": "Trigraphs", "score": min(score, 2)}

def quadgraphs_rule(word):
    g = ['ough']
    score = sum([1 for x in g if x in word])
    return {"rule": "Quadgraphs", "score": min(score, 2)}

# 🔥 FIXED
def multi_syllable_rule(word):
    return {"rule": "Syllables", "score": 1}

def silent_letters_rule(word):
    if word.startswith(("kn","wr","ps")):
        return {"rule": "Silent Letters", "score": 1}
    return {"rule": "Silent Letters", "score": 0}

def x_rule(word):
    return {"rule": "X Letter", "score": min(word.count('x'), 2)}

def double_letters_rule(word):
    score = sum([1 for i in range(len(word)-1) if word[i]==word[i+1]])
    return {"rule": "Double Letters", "score": min(score, 2)}

def affixes_rule(word):
    if word.startswith("un") or word.endswith("ing"):
        return {"rule": "Affixes", "score": 1}
    return {"rule": "Affixes", "score": 0}

def multi_word_rule(word):
    return {"rule": "Multi Word", "score": 2 if " " in word else 0}

def frequency_rule(word):
    if not WORDFREQ_AVAILABLE:
        return {"rule": "Frequency", "score": 0}
    z = zipf_frequency(word.lower(), "en")
    if z >= 5:
        return {"rule": "Frequency", "score": 0}
    elif z >= 4:
        return {"rule": "Frequency", "score": 1}
    else:
        return {"rule": "Frequency", "score": 2}

ALL_RULES = [
    word_length_rule,
    visually_confusable_rule,
    special_letters_rule,
    diphthongs_rule,
    vowel_team_rule,
    magic_e_rule,
    digraphs_rule,
    trigraphs_rule,
    quadgraphs_rule,
    multi_syllable_rule,
    silent_letters_rule,
    x_rule,
    double_letters_rule,
    affixes_rule,
    multi_word_rule,
    frequency_rule
]

# =========================================
# API
# =========================================
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    word = (data.get("word") or "").strip()

    if not word:
        return jsonify({"error": "No word provided"}), 400

    results = []
    total = 0

    for rule_fn in ALL_RULES:
        result = rule_fn(word)
        results.append(result)
        total += result["score"]

    difficulty = get_difficulty_level(total)

    return jsonify({
        "word": word,
        "total_score": total,
        "difficulty": difficulty,
        "rules": results
    })

# =========================================
# FRONTEND
# =========================================
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    print("\n🟢 Running...\n")
    app.run(host="0.0.0.0", port=10000)
