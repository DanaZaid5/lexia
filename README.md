# Lexia — Word Difficulty Analyzer

## Setup & Running (3 steps)

### Step 1 — Install Python dependencies
Open your terminal inside this folder and run:
```
pip install -r requirements.txt
```

### Step 2 — Start the server
```
python app.py
```
You should see:
```
🟢  Lexia backend running at http://localhost:5000
```

### Step 3 — Open the website
Open your browser and go to:
```
http://localhost:5000
```

That's it. The website will call the Python backend automatically.

---

## Project structure
```
lexia/
├── app.py              ← Flask backend with all 16 rules
├── requirements.txt    ← Python dependencies
├── README.md
└── static/
    ├── index.html      ← The website frontend
    └── Lexia.svg       ← Logo
```

## How it works
1. You type a word in the browser
2. The frontend sends it to `POST /analyze` on the Flask server
3. Flask runs all 16 Python rules (including real `wordfreq` for frequency)
4. The scores are returned as JSON and displayed in the browser

## Rules
1. Word Length
2. Visually Confusable Letters
3. Special Letter Rules (soft-C, soft-G, intervocalic-S)
4. Diphthongs & Semi-Vowels
5. Vowel Teams
6. Magic-E Pattern
7. Digraphs
8. Trigraphs
9. Quadgraphs
10. Syllable Count (CMU Pronouncing Dictionary)
11. Silent Letter Patterns
12. Letter X
13. Double Letters
14. Affixes
15. Multi-Word
16. Word Frequency (real corpus data via wordfreq)
