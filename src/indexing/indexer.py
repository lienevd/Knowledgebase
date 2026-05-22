
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in
import os

schema = Schema(
    document_id=ID(stored=True),
    content=TEXT(stored=True),
    category=TEXT(stored=True)
)

def create_index(index_dir="indexdir"):
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    return create_in(index_dir, schema)
