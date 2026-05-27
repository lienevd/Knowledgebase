import csv
from pathlib import Path
from typing import List

KEYWORD_FILE = Path(__file__).resolve().parents[2] / "data" / "IT_Security_Keywords.csv"


def normalize_keyword(raw_value: str) -> str:
    """Normalize a keyword by removing numeric prefixes and trimming whitespace."""
    term = raw_value.strip().lower()
    # Remove leading numeric column prefixes like '00.' or '1.'
    while term and term[0].isdigit():
        term = term[1:]
    term = term.lstrip('. ')  # strip separators after the prefix
    return term


def load_keywords() -> List[str]:
    """Load all keywords from the CSV file."""
    if not KEYWORD_FILE.exists():
        return []

    keywords = []
    seen = set()

    with KEYWORD_FILE.open(newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            for cell in row:
                term = normalize_keyword(cell)
                if term and term not in seen:
                    seen.add(term)
                    keywords.append(term)

    return keywords


def get_keyword_examples(limit: int = 10) -> List[str]:
    """Return a small set of example keywords."""
    keywords = load_keywords()
    return keywords[:limit] if keywords else []
