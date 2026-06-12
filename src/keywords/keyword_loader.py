import csv
from pathlib import Path
from typing import Dict, List

KEYWORD_FILE = Path(__file__).resolve().parents[2] / "data" / "IT_Security_Keywords.csv"


def normalize_keyword(raw_value: str) -> str:
    """Normalize a keyword by removing numeric prefixes and trimming whitespace."""
    term = raw_value.strip().lower()
    # Remove leading numeric column prefixes like '00.' or '1.'
    while term and term[0].isdigit():
        term = term[1:]
    term = term.lstrip('. ')  # strip separators after the prefix
    return term


def normalize_category(raw_value: str) -> str:
    """Normalize a category label by removing numeric prefixes and trimming whitespace."""
    return normalize_keyword(raw_value).title()


def load_keyword_categories() -> Dict[str, List[str]]:
    """Load CSV columns as category -> keywords using normalized first-row headers."""
    if not KEYWORD_FILE.exists():
        return {}

    with KEYWORD_FILE.open(newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        rows = list(reader)

    if not rows:
        return {}

    categories = [normalize_category(cell) for cell in rows[0]]
    keyword_map: Dict[str, List[str]] = {
        category: []
        for category in categories
        if category
    }
    seen_by_category = {category: set() for category in keyword_map}

    for row in rows[1:]:
        for index, cell in enumerate(row):
            if index >= len(categories):
                continue

            category = categories[index]
            if not category:
                continue

            term = normalize_keyword(cell)
            if term and term not in seen_by_category[category]:
                seen_by_category[category].add(term)
                keyword_map[category].append(term)

    return {category: keywords for category, keywords in keyword_map.items() if keywords}


def load_keywords() -> List[str]:
    """Load all unique keywords from the categorized CSV file."""
    keywords = []
    seen = set()

    for category_keywords in load_keyword_categories().values():
        for term in category_keywords:
            if term and term not in seen:
                seen.add(term)
                keywords.append(term)

    return keywords


def get_keyword_examples(limit: int = 10) -> List[str]:
    """Return a small set of example keywords."""
    keywords = load_keywords()
    return keywords[:limit] if keywords else []
