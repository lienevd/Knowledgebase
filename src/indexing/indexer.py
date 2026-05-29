from pathlib import Path
from typing import Dict, List

from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, exists_in, open_dir
from whoosh.qparser import MultifieldParser

INDEX_DIR = Path("data") / "indexdir"

schema = Schema(
    document_id=ID(stored=True, unique=True),
    filename=TEXT(stored=True),
    content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    category=TEXT(stored=True),
)


def get_or_create_index(index_dir: str | Path = None):
    index_path = Path(index_dir or INDEX_DIR)
    index_path.mkdir(parents=True, exist_ok=True)

    if exists_in(str(index_path)):
        return open_dir(str(index_path))

    return create_in(str(index_path), schema)


def index_document(document_id: str, filename: str, content: str, category: str, index_dir: str | Path = None):
    ix = get_or_create_index(index_dir)
    writer = ix.writer()
    writer.update_document(
        document_id=document_id,
        filename=filename,
        content=content or "",
        category=category or "",
    )
    writer.commit()


def search_index(query: str, index_dir: str | Path = None, limit: int = 10) -> List[Dict]:
    index_path = Path(index_dir or INDEX_DIR)
    if not exists_in(str(index_path)):
        return []

    ix = open_dir(str(index_path))
    parser = MultifieldParser(["content", "filename", "category"], schema=ix.schema)
    parsed_query = parser.parse(query)
    results = []

    with ix.searcher() as searcher:
        hits = searcher.search(parsed_query, limit=limit)
        hits.fragmenter.charlimit = 150

        for hit in hits:
            snippet = hit.highlights("content") or ""
            query_terms = [term.strip().lower() for term in query.split() if term.strip()]
            count = 0
            stored_content = hit.get("content", "").lower()
            for term in query_terms:
                count += stored_content.count(term)

            results.append({
                "document_id": hit["document_id"],
                "filename": hit.get("filename", "Unknown"),
                "category": hit.get("category", "Uncategorized"),
                "keyword_count": count,
                "context": snippet,
            })

    return results
