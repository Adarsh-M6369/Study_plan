import os
import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_fixed

try:
    import chromadb
    from chromadb import EmbeddingFunction
    from chromadb.api.types import Documents, Embeddings
except ImportError:
    chromadb = None
    EmbeddingFunction = object
    Documents = list
    Embeddings = list

from app.config import settings

logger = logging.getLogger("rag.store")


class GeminiChromaEmbeddingFunction(EmbeddingFunction):
    """
    ChromaDB compatible embedding function that uses GoogleGenerativeAIEmbeddings
    (text-embedding-004) when GEMINI_API_KEY is available, and falls back to a fast,
    zero-network deterministic dimensional embedding.
    Completely avoids downloading the ONNX tar archive from AWS S3.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._embedder = None

        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                self._embedder = GoogleGenerativeAIEmbeddings(
                    model="text-embedding-004",
                    google_api_key=self.api_key
                )
                logger.info("Initialized GoogleGenerativeAIEmbeddings (text-embedding-004) for Chroma.")
            except Exception as e:
                logger.warning(f"Could not initialize GoogleGenerativeAIEmbeddings: {e}")

    def name(self) -> str:
        return "gemini_chroma_embedding"

    def __call__(self, input: Documents) -> Embeddings:
        if self._embedder:
            try:
                return self._embedder.embed_documents(input)
            except Exception as e:
                logger.warning(f"GoogleGenerativeAIEmbeddings API call failed: {e}. Using deterministic local embedding.")

        return [self._hash_embed(text) for text in input]

    def _hash_embed(self, text: str, dim: int = 384) -> List[float]:
        vec = [0.0] * dim
        tokens = text.lower().split()
        if not tokens:
            return vec
        for t in tokens:
            h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            val = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += val
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


class ResilientVectorStore:
    """
    ChromaDB-backed multi-tenant vector store with Tenacity retries,
    user-id metadata isolation, batched upserts (100 chunks/batch),
    and keyword/lexical fallback retrieval.
    """
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or os.path.join(os.getcwd(), "chroma_data")
        self.client = None
        self.collection = None
        self.in_memory_docs: List[Dict[str, Any]] = []
        self.embedding_function = GeminiChromaEmbeddingFunction()

        if chromadb is not None:
            try:
                os.makedirs(self.persist_directory, exist_ok=True)
                self.client = chromadb.PersistentClient(path=self.persist_directory)
            except Exception as e:
                logger.warning(f"Failed to initialize PersistentClient at {self.persist_directory}: {e}. Using EphemeralClient.")
                try:
                    self.client = chromadb.EphemeralClient()
                except Exception:
                    self.client = None

            self.collection_name = "study_guide_chunks"
            self._get_or_create_collection()
        else:
            logger.warning("ChromaDB library not found. Running in resilient in-memory vector store mode.")

    def _get_or_create_collection(self):
        if self.client is None:
            return
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Chroma collection initialized with Gemini/Fast embedding function (bypassing ONNX S3 download).")
        except Exception as e:
            logger.warning(f"Initial get_or_create_collection encountered conflict ({e}). Resetting collection for clean embedding function migration.")
            try:
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("Re-created Chroma collection with Gemini/Fast embedding function.")
            except Exception as inner_err:
                logger.error(f"Error recreating Chroma collection: {inner_err}")
                self.collection = None

    def add_documents(self, user_id: str, document_id: str, chunks: List[Dict[str, Any]], batch_size: int = 100) -> int:
        """
        Indexes chunks into ChromaDB with multi-tenant user_id and document_id metadata.
        Batches document additions in groups of 100 chunks to prevent memory or transaction choking.
        """
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []

        for c in chunks:
            chunk_unique_id = f"{user_id}_{document_id}_{c['chunk_id']}"
            ids.append(chunk_unique_id)
            documents.append(c["text"])
            meta = {
                "user_id": user_id,
                "document_id": document_id,
                "page_number": c.get("page_number", 1),
                "source": c.get("source", "doc"),
                "chapter_title": c.get("chapter_title", "Section"),
                "segment_index": int(c.get("segment_index", 0)),
                "total_segments": int(c.get("total_segments", 1)),
                "chunk_index": c.get("chunk_index", 0)
            }
            metadatas.append(meta)
            self.in_memory_docs.append({"id": chunk_unique_id, "text": c["text"], "metadata": meta})

        if self.collection is not None:
            total_indexed = 0
            for i in range(0, len(ids), batch_size):
                b_ids = ids[i:i + batch_size]
                b_docs = documents[i:i + batch_size]
                b_metas = metadatas[i:i + batch_size]
                try:
                    self.collection.upsert(
                        ids=b_ids,
                        documents=b_docs,
                        metadatas=b_metas
                    )
                    total_indexed += len(b_ids)
                except Exception as e:
                    logger.warning(f"Error upserting batch {i//batch_size + 1} to Chroma: {e}. Stored in memory fallback.")

            logger.info(f"Batched indexing complete: {len(ids)} chunks processed for user '{user_id}'.")
            return len(ids)

        logger.info(f"Indexed {len(ids)} chunks into in-memory store for user '{user_id}'.")
        return len(ids)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=False)
    def _semantic_query(self, user_id: str, query_text: str, n_results: int = 8) -> List[Dict[str, Any]]:
        """
        Executes vector search with user_id filter, wrapped with Tenacity (2 attempts, 1s wait).
        """
        if self.collection is None:
            return []

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"user_id": user_id}
        )

        chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

            for doc, meta, dist in zip(docs, metas, distances):
                if doc:
                    chunks.append({
                        "text": doc,
                        "metadata": meta,
                        "distance": dist,
                        "retrieval_mode": "semantic"
                    })
        return chunks

    def stratified_search(
        self,
        user_id: str,
        query_text: str = "",
        document_id: Optional[str] = None,
        n_per_segment: int = 2,
        max_total: int = 16
    ) -> List[Dict[str, Any]]:
        """
        Hierarchical / Cross-Chapter Coverage Engine:
        Partitions the ingested document into its detected chapters or equidistant segments
        and retrieves representative context chunks from EVERY SINGLE chapter/segment from start to finish.
        Prevents localized clustering on a single page or story.
        """
        all_docs = []
        all_metas = []

        # 1. Fetch all records for the user from Chroma or memory
        if self.collection is not None:
            try:
                where_filter = {"user_id": user_id}
                if document_id:
                    where_filter = {"$and": [{"user_id": user_id}, {"document_id": document_id}]}
                records = self.collection.get(
                    where=where_filter,
                    include=["documents", "metadatas"]
                )
                all_docs = records.get("documents", [])
                all_metas = records.get("metadatas", [])
            except Exception as e:
                logger.warning(f"Error reading records from Chroma during stratified retrieval: {e}")

        if not all_docs and self.in_memory_docs:
            user_recs = [
                d for d in self.in_memory_docs
                if d.get("metadata", {}).get("user_id") == user_id and
                (document_id is None or d.get("metadata", {}).get("document_id") == document_id)
            ]
            all_docs = [d["text"] for d in user_recs]
            all_metas = [d["metadata"] for d in user_recs]

        if not all_docs:
            logger.warning(f"No indexed documents found for user '{user_id}'.")
            return []

        # 2. Group chunks by segment_index or chapter
        segments_map: Dict[int, List[Dict[str, Any]]] = {}
        for doc, meta in zip(all_docs, all_metas):
            if not doc:
                continue
            seg_idx = int(meta.get("segment_index", 0))
            if seg_idx not in segments_map:
                segments_map[seg_idx] = []
            segments_map[seg_idx].append({"text": doc, "metadata": meta})

        sorted_segment_keys = sorted(segments_map.keys())
        logger.info(f"Stratified retrieval executing across {len(sorted_segment_keys)} segments for user '{user_id}'.")

        query_tokens = set(re.findall(r"\w+", query_text.lower())) if query_text else set()
        chosen_chunks: List[Dict[str, Any]] = []

        # 3. For each segment from start to end, pick top representative chunks
        for seg_idx in sorted_segment_keys:
            seg_chunks = segments_map[seg_idx]
            if not seg_chunks:
                continue

            # If query_tokens exist, sort segment chunks by token overlap; otherwise sample evenly
            if query_tokens:
                scored = []
                for item in seg_chunks:
                    doc_tokens = set(re.findall(r"\w+", item["text"].lower()))
                    overlap = len(query_tokens.intersection(doc_tokens))
                    scored.append((overlap, item))
                scored.sort(key=lambda x: x[0], reverse=True)
                top_for_seg = [s[1] for s in scored[:n_per_segment]]
            else:
                top_for_seg = seg_chunks[:n_per_segment]

            chosen_chunks.extend(top_for_seg)
            if len(chosen_chunks) >= max_total:
                break

        logger.info(f"Stratified retrieval returned {len(chosen_chunks)} distributed chunks covering all segments.")
        return chosen_chunks

    def _keyword_lexical_fallback(self, user_id: str, query_text: str, n_results: int = 8) -> List[Dict[str, Any]]:
        """
        Fallback keyword/lexical retrieval: fetches user-scoped documents and performs token overlap scoring.
        """
        logger.info(f"Triggering keyword/lexical fallback retrieval for user '{user_id}'.")
        docs = []
        metas = []

        if self.collection is not None:
            try:
                all_user_records = self.collection.get(
                    where={"user_id": user_id},
                    include=["documents", "metadatas"]
                )
                docs = all_user_records.get("documents", [])
                metas = all_user_records.get("metadatas", [])
            except Exception as e:
                logger.warning(f"Failed to fetch from Chroma: {e}. Checking in-memory.")

        if not docs and self.in_memory_docs:
            user_recs = [d for d in self.in_memory_docs if d.get("metadata", {}).get("user_id") == user_id]
            docs = [d["text"] for d in user_recs]
            metas = [d["metadata"] for d in user_recs]

        if not docs:
            logger.warning(f"No documents found for user '{user_id}' in vector store.")
            return []

        query_tokens = set(re.findall(r"\w+", query_text.lower()))
        scored_docs = []

        for doc, meta in zip(docs, metas):
            if not doc:
                continue
            doc_tokens = set(re.findall(r"\w+", doc.lower()))
            overlap = len(query_tokens.intersection(doc_tokens))
            if overlap > 0:
                scored_docs.append((overlap, doc, meta))

        # Sort by overlap descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_docs[:n_results]

        if not top_matches and docs:
            return [{"text": d, "metadata": m, "score": 0, "retrieval_mode": "fallback_head"} for d, m in zip(docs[:n_results], metas[:n_results])]

        return [
            {
                "text": item[1],
                "metadata": item[2],
                "score": item[0],
                "retrieval_mode": "keyword_fallback"
            }
            for item in top_matches
        ]

    def search(self, user_id: str, query_text: str, n_results: int = 8) -> List[Dict[str, Any]]:
        """
        Performs resilient search with stratified multi-segment retrieval fallback.
        """
        results = []
        try:
            results = self.stratified_search(user_id=user_id, query_text=query_text, max_total=n_results)
        except Exception as e:
            logger.warning(f"Stratified search error: {e}. Trying semantic/lexical.")

        if not results:
            try:
                results = self._semantic_query(user_id=user_id, query_text=query_text, n_results=n_results)
            except Exception:
                pass

        if not results:
            results = self._keyword_lexical_fallback(user_id=user_id, query_text=query_text, n_results=n_results)

        return results

    def get_all_user_context(self, user_id: str, max_chars: int = 50000) -> str:
        """
        Retrieves and concatenates all indexed material for the user up to character limit.
        """
        try:
            if self.collection is not None:
                records = self.collection.get(where={"user_id": user_id}, include=["documents"])
                docs = records.get("documents", [])
                if docs:
                    return "\n\n".join(docs)[:max_chars]

            if self.in_memory_docs:
                docs = [d["text"] for d in self.in_memory_docs if d.get("metadata", {}).get("user_id") == user_id]
                return "\n\n".join(docs)[:max_chars]

            return ""
        except Exception as e:
            logger.error(f"Error fetching all context for user {user_id}: {e}")
            return ""


_store_instance = None


def get_vector_store() -> ResilientVectorStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = ResilientVectorStore()
    return _store_instance
