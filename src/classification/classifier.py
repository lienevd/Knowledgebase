from collections import Counter

def classify_document(text, keyword_map):
    scores = Counter()
    matched_keywords = {}

    text_lower = text.lower()

    for category, keywords in keyword_map.items():
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            if count > 0:
                scores[category] += count
                matched_keywords.setdefault(category, {})[keyword] = count

    best_category = max(scores, key=scores.get) if scores and max(scores.values()) > 0 else "Uncategorized"

    return {
        "category": best_category,
        "scores": dict(scores),
        "matched_keywords": matched_keywords,
    }
