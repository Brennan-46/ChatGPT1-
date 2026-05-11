from datetime import datetime, timezone
import uuid

import chromadb

from app.core.config import settings


class MemoryStore:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection = self.client.get_or_create_collection(name=settings.memory_collection)

    def store_interaction(self, user_id: str, content: str) -> str:
        doc_id = str(uuid.uuid4())
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[{"user_id": user_id, "timestamp": datetime.now(timezone.utc).isoformat()}],
        )
        return doc_id

    def retrieve(self, user_id: str, query: str, top_k: int = 3) -> list[str]:
        results = self.collection.query(query_texts=[query], n_results=top_k, where={"user_id": user_id})
        docs = results.get("documents", [[]])
        return docs[0] if docs and docs[0] else []
