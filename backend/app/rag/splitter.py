import logging
from typing import List, Dict, Any

logger = logging.getLogger("rag.splitter")

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        # Self-contained fallback splitter if langchain text splitters not yet installed
        class RecursiveCharacterTextSplitter:
            def __init__(self, chunk_size=800, chunk_overlap=120, separators=None):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap

            def split_text(self, text: str) -> List[str]:
                chunks = []
                start = 0
                while start < len(text):
                    end = min(start + self.chunk_size, len(text))
                    chunks.append(text[start:end])
                    if end == len(text):
                        break
                    start += self.chunk_size - self.chunk_overlap
                return chunks


def split_text_into_chunks(
    pages_data: List[Dict[str, Any]],
    chunk_size: int = 1500,
    chunk_overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunks page texts recursively while retaining metadata such as page number and source.
    Optimized with chunk_size=1500, chunk_overlap=200 for up to 150-page lecture documents.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
    )

    all_chunks = []
    chunk_id = 0

    for page_info in pages_data:
        text = page_info.get("text", "")
        page_num = page_info.get("page_number", 1)
        source = page_info.get("source", "document")

        if not text.strip():
            continue

        text_splits = splitter.split_text(text)
        for sub_idx, chunk_text in enumerate(text_splits):
            cleaned_chunk = chunk_text.strip()
            if len(cleaned_chunk) < 20:
                continue

            chunk_id += 1
            all_chunks.append({
                "chunk_id": f"chunk_{chunk_id}",
                "text": cleaned_chunk,
                "page_number": page_num,
                "source": source,
                "chunk_index": sub_idx
            })

    logger.info(f"Split {len(pages_data)} pages into {len(all_chunks)} semantic chunks.")
    return all_chunks
