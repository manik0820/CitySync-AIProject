import spacy
from collections import defaultdict

# Load spaCy English model
# Make sure you've run: python -m spacy download en_core_web_sm
nlp = spacy.load("en_core_web_sm")

# ---------------------------------------------------------------------------
# Keyword dictionaries
# Each severity level has keywords associated with it.
# The more matches, the higher the severity and urgency.
# ---------------------------------------------------------------------------

CRITICAL_KEYWORDS = [
    "collapse", "collapsed", "fire", "burning", "explosion", "electrocution",
    "live wire", "exposed wire", "flooding", "flood", "drowning", "accident",
    "death", "dead", "injury", "injured", "emergency", "dangerous", "fatal",
    "gas leak", "sinkhole", "outbreak", "sewage overflow", "blocked drain",
    "overflowing", "overflow", "critical", "urgent", "immediate", "children",
    "hospital", "ambulance", "no water", "no electricity", "power outage"
]

HIGH_KEYWORDS = [
    "broken", "damaged", "pothole", "leak", "leaking", "burst", "fallen",
    "falling", "crack", "cracked", "not working", "stopped working", "failure",
    "disruption", "no supply", "smell", "stench", "garbage", "waste",
    "blocked", "clogged", "missing", "stolen", "vandalized", "unsafe",
    "hazard", "hazardous", "risk", "complaint", "days", "weeks", "months"
]

MEDIUM_KEYWORDS = [
    "repair", "fix", "broken light", "streetlight", "footpath", "pavement",
    "uneven", "pothole small", "maintenance", "dirty", "unclean", "noise",
    "construction", "delay", "slow", "irregular", "request", "please",
    "issue", "problem", "concern", "inconvenience"
]

LOW_KEYWORDS = [
    "suggestion", "feedback", "minor", "small", "faded", "paint",
    "aesthetic", "beautification", "cosmetic", "information", "query",
    "enquiry", "general", "trimming", "grass", "tree", "parking"
]

# Urgency amplifiers — these words boost the urgency score
URGENCY_AMPLIFIERS = [
    "immediately", "right now", "asap", "since days", "since weeks",
    "nobody is responding", "no response", "ignored", "repeatedly",
    "multiple times", "already reported", "still not fixed", "getting worse",
    "please help", "desperate", "very serious", "very dangerous", "children",
    "elderly", "accident happened", "someone fell", "people are suffering"
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def preprocess(text: str) -> str:
    """Lowercase and strip the input text."""
    return text.lower().strip()


def count_keyword_matches(text: str, keyword_list: list) -> int:
    """Count how many keywords from the list appear in the text."""
    return sum(1 for kw in keyword_list if kw in text)


def extract_severity(complaint_text: str) -> tuple[str, float]:
    """
    Analyse a complaint string and return:
      - severity_label : one of "Critical", "High", "Medium", "Low"
      - urgency_score  : float in [0.0, 1.0]

    Logic:
      1. Count keyword matches at each severity tier.
      2. Pick the highest tier that has at least one match.
      3. Compute a base urgency score from the match counts.
      4. Apply an amplifier boost if urgency-amplifying phrases are present.
    """
    text = preprocess(complaint_text)

    # Count matches per tier
    scores = {
        "Critical": count_keyword_matches(text, CRITICAL_KEYWORDS),
        "High":     count_keyword_matches(text, HIGH_KEYWORDS),
        "Medium":   count_keyword_matches(text, MEDIUM_KEYWORDS),
        "Low":      count_keyword_matches(text, LOW_KEYWORDS),
    }

    # Determine severity label — highest tier with at least one match wins
    if scores["Critical"] > 0:
        severity_label = "Critical"
        base_urgency   = min(0.75 + scores["Critical"] * 0.05, 0.95)
    elif scores["High"] > 0:
        severity_label = "High"
        base_urgency   = min(0.50 + scores["High"] * 0.05, 0.74)
    elif scores["Medium"] > 0:
        severity_label = "Medium"
        base_urgency   = min(0.25 + scores["Medium"] * 0.05, 0.49)
    else:
        severity_label = "Low"
        base_urgency   = min(0.05 + scores["Low"] * 0.03, 0.24)

    # Amplifier boost
    amplifier_hits = count_keyword_matches(text, URGENCY_AMPLIFIERS)
    boost = amplifier_hits * 0.04                      # +0.04 per amplifier hit
    urgency_score = round(min(base_urgency + boost, 1.0), 4)

    return severity_label, urgency_score


def extract_entities(complaint_text: str) -> dict:
    """
    Use spaCy NER to pull out named entities from the complaint.
    Returns a dict with lists of locations, organisations, and other entities.
    This enriches the data stored in Supabase.
    """
    doc = nlp(complaint_text)
    entities = defaultdict(list)

    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC", "FAC"):
            entities["locations"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["organisations"].append(ent.text)
        else:
            entities["other"].append(ent.text)

    return dict(entities)


def analyse_complaint(complaint_text: str) -> dict:
    """
    Master function called by main.py.
    Returns everything the NLP module produces in one dict.

    Example output:
    {
        "severity_label": "High",
        "urgency_score": 0.72,
        "entities": {
            "locations": ["MG Road"],
            "organisations": []
        }
    }
    """
    severity_label, urgency_score = extract_severity(complaint_text)
    entities = extract_entities(complaint_text)

    return {
        "severity_label": severity_label,
        "urgency_score":  urgency_score,
        "entities":       entities,
    }


# ---------------------------------------------------------------------------
# Quick test — run this file directly to check it works
# python nlp_module.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_complaints = [
        "There is a large pothole on MG Road causing accidents daily. Children are falling. Very dangerous.",
        "The streetlight near my house has been broken for two weeks. Nobody is responding.",
        "The footpath paint near sector 5 is faded.",
        "Sewage is overflowing on our street since 3 days. The smell is unbearable and people are suffering.",
    ]

    for complaint in test_complaints:
        result = analyse_complaint(complaint)
        print(f"\nComplaint : {complaint[:60]}...")
        print(f"Severity  : {result['severity_label']}")
        print(f"Urgency   : {result['urgency_score']}")
        print(f"Entities  : {result['entities']}")