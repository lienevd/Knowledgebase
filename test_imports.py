from src.keywords.keyword_loader import load_keywords
from src.storage.document_store import load_documents

keywords = load_keywords()
print(f"Keywords loaded: {len(keywords)}")
print(f"First 5: {keywords[:5] if keywords else 'None'}")

documents = load_documents()
print(f"Documents in storage: {len(documents)}")
