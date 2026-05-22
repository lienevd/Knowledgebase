
import uuid
from collections import Counter

def classify_document(text, keyword_map):
    document_id = str(uuid.uuid4())
    scores = Counter()

    text_lower = text.lower()

    for category, keywords in keyword_map.items():
        for keyword in keywords:
            scores[category] += text_lower.count(keyword.lower())

    best_category = max(scores, key=scores.get) if scores else "Uncategorized"

    return {
        "document_id": document_id,
        "category": best_category,
        "scores": dict(scores)
    }
