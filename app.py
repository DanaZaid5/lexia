import csv
import os

def load_homophones(filename):
    homophones_map = {}

    try:
        with open(filename, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                group = [w.strip().lower() for w in row if w.strip()]

                for word in group:
                    homophones_map[word] = group

    except:
        pass

    return homophones_map

BASE_DIR = os.path.dirname(__file__)
HOMOPHONES = load_homophones(os.path.join(BASE_DIR, "homophones.csv"))


from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

try:
    from wordfreq import zipf_frequency
    WORDFREQ_AVAILABLE = True
except ImportError:
    WORDFREQ_AVAILABLE = False

app = Flask(__name__, static_folder="static")
CORS(app)

# =========================================
# Difficulty
# =========================================
def get_difficulty_level(score):
    if score <= 5:
        return "Easy"
    elif score <= 10:
        return "Medium"
    else:
        return "Hard"

# =========================================
# RULES (ORIGINAL LOGIC + UI FORMAT)
# =========================================
def homophones_rule(word):
    group = HOMOPHONES.get(word)

    if group:
        score = 1
        similar = [w for w in group if w != word]
    else:
        score = 0
        similar = []

    return {
        "rule": "Homophones",
        "score": score,
        "desc": "Has similar sounding words" if group else "No homophones",
        "detail": ", ".join(similar) if similar else "-"
    }

def word_length_rule(word):
    length = len(word)

    if length <= 4:
        score = 0
    elif length <= 6:
        score = 1
    else:
        score = 2

    return {
        "rule": "Word Length",
        "score": score,
        "desc": f"{length} letters",
        "detail": "Length-based scoring"
    }

confusable_pairs = [
    ['b', 'd'], ['p', 'q'], ['m', 'n'], ['i', 'l'], ['u', 'n'],
    ['c', 'e'], ['t', 'f'], ['m', 'w'], ['i', 'j'], ['h', 'n'],
    ['c', 'a'], ['c', 'o'], ['c', 'd'], ['e', 'o'], ['a', 'd']
]
def visually_confusable_rule(word):
    word = word.lower()
    found = set()

    for pair in confusable_pairs:
        for letter in word:
            if letter in pair:
                found.add(letter)

    score = len(found)

    return {
        "rule": "Confusable Letters",
        "score": score,
        "desc": f"{', '.join(found) if found else 'none'}",
        "detail": f"Count: {score}"
    }


def special_letters_rule(word):
    vowels = ['a','e','i','o','u','y']
    score = 0
    word = word.lower()

    for i in range(len(word)):
        if word[i] == 'c' and i+1 < len(word) and word[i+1] in ['e','i','y']:
            score += 1

        if word[i] == 'g' and i+1 < len(word) and word[i+1] in ['e','i','y']:
            score += 1

        if word[i] == 's' and i-1 >= 0 and i+1 < len(word):
            if word[i-1] in vowels and word[i+1] in vowels:
                score += 1

    return {
        "rule": "Special Letters",
        "score": score,
        "desc": "Soft C/G + vowel-surrounded S",
        "detail": f"Count: {score}"
    }


def diphthongs_semi_vowels_rule(word):
    word = word.lower()
    score = 0

    found = []

    for dip in ["aw","ew","ow"]:
        if dip in word:
            score += 1
            found.append(dip)

    for i in range(1, len(word)):
        if word[i] == 'y':
            score += 1
            found.append("y")

    return {
        "rule": "Diphthongs",
        "score": score,
        "desc": f"{', '.join(found) if found else 'none'}",
        "detail": f"Count: {score}"
    }


def vowel_team_rule(word):
    diphthongs = ["oi","ea","ou","ie","ue","oe"]
    score = 0
    word = word.lower()
    found = []

    for i in range(len(word)-1):
        pair = word[i] + word[i+1]
        if pair in diphthongs:
            score += 1
            found.append(pair)

    return {
        "rule": "Vowel Teams",
        "score": score,
        "desc": f"{', '.join(found) if found else 'none'}",
        "detail": f"Count: {score}"
    }


def magic_e_rule(word):
    vowels = ['a','i','o','u']
    score = 0
    word = word.lower()

    for i in range(len(word)-2):
        if (
            word[i] in vowels and
            word[i+1] not in vowels and
            word[i+2] == 'e' and
            i+2 == len(word)-1
        ):
            score += 1

    return {
        "rule": "Magic E",
        "score": score,
        "desc": "Silent e pattern",
        "detail": f"Count: {score}"
    }


def digraphs_rule(word):
    graphemes = ['sh','ch','th','wh','ph','ck','dg','sc']
    found = [g for g in graphemes if g in word]
    score = len(found)

    return {
        "rule": "Digraphs",
        "score": score,
        "desc": f"{', '.join(found) if found else 'none'}",
        "detail": f"Count: {score}"
    }


def trigraphs_rule(word):
    patterns = [
        "air","are","dge","ear","eau","eer","eir","ere","ier",
        "igh","oar","oor","ore","oul","our","tch","ure"
    ]

    found = []
    word = word.lower()

    for p in patterns:
        if p in word:
            found.append(p)

    score = len(found)

    return {
        "rule": "Trigraphs",
        "score": score,
        "desc": f"{', '.join(found) if found else 'none'}",
        "detail": f"Count: {score}"
    }


def quadgraphs_rule(word):
    patterns = ["augh","eigh","ngue","ough"]
    found = []
    word = word.lower()

    for p in patterns:
        if p in word:
            found.append(p)

    score = len(found)

    return {
        "rule": "Quadgraphs",
        "score": score,
        "desc": f"{', '.join(found) if found else 'none'}",
        "detail": f"Count: {score}"
    }


try:
    import pronouncing
    PRONOUNCING_AVAILABLE = True
except:
    PRONOUNCING_AVAILABLE = False

def multi_syllable_rule(word):
    syllables = 1

    if PRONOUNCING_AVAILABLE:
        phones = pronouncing.phones_for_word(word)
        if phones:
            syllables = pronouncing.syllable_count(phones[0])
    else:
        # fallback simple estimation
        vowels = "aeiouy"
        count = 0
        prev = False

        for c in word.lower():
            if c in vowels:
                if not prev:
                    count += 1
                prev = True
            else:
                prev = False

        syllables = max(count, 1)

    if syllables == 1:
        score = 0
    elif syllables <= 3:
        score = 1
    else:
        score = 2

    return {
        "rule": "Syllables",
        "score": score,
        "desc": f"{syllables} syllable(s)",
        "detail": "Estimated"
    }


def silent_letters_rule(word):
    patterns = ["ps","kn","wr","gn","mb","gh"]
    found = []
    word = word.lower()

    for p in patterns:
        if word.startswith(p) or word.endswith(p):
            found.append(p)

    score = len(found)

    return {
        "rule": "Silent Letters",
        "score": score,
        "desc": f"{', '.join(found) if found else 'none'}",
        "detail": f"Count: {score}"
    }


def x_position_rule(word):
    word = word.lower()
    score = 0
    positions = []

    for i in range(len(word)):
        if word[i] == 'x':
            
            # x في البداية
            if i == 0:
                score += 1
                positions.append("start")
            
            # x في الوسط
            elif 0 < i < len(word) - 1:
                score += 1
                positions.append("middle")

        
            elif i == len(word) - 1:
                positions.append("end")

    return {
        "rule": "X Position",
        "score": score,
        "desc": f"x positions: {', '.join(positions) if positions else 'none'}",
        "detail": f"Count: {score}"
    }


def double_letters_rule(word):
    word = word.lower()
    count = sum(1 for i in range(len(word)-1) if word[i] == word[i+1])

    return {
        "rule": "Double Letters",
        "score": count,
        "desc": "Repeated letters",
        "detail": f"Count: {count}"
    }


def affixes_rule(word):
    prefixes = [
        "anti", "de", "dis", "en", "em", "fore", "in", "im", "il", "ir",
        "inter", "mid", "mis", "non", "over", "pre", "re", "semi",
        "sub", "super", "trans", "un", "under"
    ]

    suffixes = [
        "able", "ible", "al", "ial", "ed", "en", "er", "est", "ful", "ic",
        "ing", "ion", "tion", "ation", "ition", "ity", "ty", "ive", "ative", "itive",
        "less", "ly", "ment", "ness", "ous", "eous", "ious", "s", "es"
    ]

    score = 0
    word = word.lower()

    if any(word.startswith(p) for p in prefixes):
        score += 1

    if any(word.endswith(s) for s in suffixes):
        score += 1

    return {
        "rule": "Affixes",
        "score": score,
        "desc": "Prefix / suffix detected",
        "detail": f"Score: {score}"
    }



def multi_word_rule(word):
    score = 2 if " " in word else 0

    return {
        "rule": "Multi Word",
        "score": score,
        "desc": "Contains space" if score else "Single word",
        "detail": word
    }


def frequency_rule(word):
    if not WORDFREQ_AVAILABLE:
        return {
            "rule": "Word Frequency",
            "desc": "Uses Zipf frequency from wordfreq. More common words are easier.",
            "score": 0,
            "detail": "wordfreq library is not installed"
        }

    z = zipf_frequency(word.lower().strip(), "en")

    if z >= 5:
        score = 0
        level = "daily/common"
    elif z >= 4:
        score = 1
        level = "less common"
    else:
        score = 2
        level = "rare"

    return {
        "rule": "Word Frequency",
        "desc": "Daily and common words add 0, less common words add 1, and rare words add 2.",
        "score": score,
        "detail": f"Zipf = {z:.2f} ({level})"
    }
 
ALL_RULES = [
    word_length_rule,
    visually_confusable_rule,
    special_letters_rule,
    diphthongs_semi_vowels_rule,
    vowel_team_rule,
    magic_e_rule,
    digraphs_rule,
    trigraphs_rule,
    quadgraphs_rule,
    multi_syllable_rule,
    silent_letters_rule,
    x_position_rule,
    double_letters_rule,
    affixes_rule,
    multi_word_rule,
    frequency_rule,
    homophones_rule
]

# =========================================
# API
# =========================================
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    word = (data.get("word") or "").strip().lower()

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
import os
if __name__ == "__main__":
    print("\n🟢 Running...\n")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
