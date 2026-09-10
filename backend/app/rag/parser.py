import io
import re
import logging
from typing import List, Dict, Any, Tuple
import pypdf
from fastapi import HTTPException, status

logger = logging.getLogger("rag.parser")

MAX_ALLOWED_PAGES = 150

BOILERPLATE_KEYWORDS = [
    "tamil nadu textbook",
    "state council of educational research",
    "தீண்டாமை",
    "தீண்டாமை மனிதநேயமற்ற",
    "பெருங்குற்றமும்",
    "untouchability is a crime",
    "untouchability is an inhuman",
    "national anthem",
    "jana gana mana",
    "national pledge",
    "india is my country",
    "chairperson",
    "co-chairperson",
    "authors",
    "reviewers",
    "co-ordinator",
    "layout & design",
    "wrapper design",
    "textbook committee",
    "price :",
    "printed by",
    "table of contents",
    "contents",
    "preface",
    "foreword",
    "published by",
    "first edition",
    "revised edition",
    "all rights reserved",
    "isbn",
]


def clean_text(raw_text: str) -> str:
    """
    Cleans and normalizes extracted PDF text:
    - Strips recurring headers/footers patterns
    - Removes statutory slogans, publisher boilerplate, and standalone numbers
    - Normalizes excessive whitespace
    """
    if not raw_text:
        return ""

    # Replace weird unicode spaces or null bytes
    text = raw_text.replace("\x00", "").replace("\u00a0", " ")

    # Remove standard header/footer artifacts like 'Page X of Y' or 'Slide X'
    text = re.sub(r"(?i)\bpage\s+\d+(\s+of\s+\d+)?\b", "", text)
    text = re.sub(r"(?i)\bslide\s+\d+\b", "", text)

    # Remove standalone line numbers
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)

    # Normalize multiple whitespace characters inside lines
    text = re.sub(r"[ \t]+", " ", text)

    # Replace 3+ consecutive newlines with two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip surrounding whitespace
    return text.strip()


def is_front_matter_or_boilerplate(page_text: str, page_num: int, total_pages: int) -> bool:
    """
    Identifies non-educational introductory pages, publisher information,
    statutory slogans, committee credits, and preliminary table of contents.
    """
    if not page_text or len(page_text.strip()) < 30:
        return True

    text_lower = page_text.lower()

    # Count matching boilerplate keywords
    match_count = sum(1 for kw in BOILERPLATE_KEYWORDS if kw in text_lower)

    # If first 3 pages of a multi-page document contain strong boilerplate indicators
    if total_pages > 5 and page_num <= 3:
        if match_count >= 1:
            logger.info(f"Skipping page {page_num}/{total_pages} as introductory front-matter (matched {match_count} boilerplate keywords).")
            return True

    # For any page with heavy administrative/statutory boilerplate density
    if match_count >= 3:
        logger.info(f"Skipping page {page_num}/{total_pages} due to high boilerplate keyword density ({match_count} matches).")
        return True

    return False


def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "document.pdf") -> Tuple[str, List[Dict[str, Any]], int]:
    """
    Parses PDF bytes using pypdf.
    Enforces strict 150-page limit: raises HTTP 400 if page count > 150.
    Filters out front-matter pages, publisher notices, committee lists, and slogans.
    Returns (full_cleaned_text, list_of_page_dicts, page_count).
    """
    try:
        stream = io.BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(stream)
    except Exception as e:
        logger.error(f"Failed to read PDF stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or corrupted PDF file: {str(e)}"
        )

    page_count = len(reader.pages)
    logger.info(f"Parsing PDF '{filename}': {page_count} pages detected.")

    # Strict page boundary validation
    if page_count > MAX_ALLOWED_PAGES:
        logger.warning(f"PDF '{filename}' rejected: {page_count} pages exceeds strict limit of {MAX_ALLOWED_PAGES}.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Document exceeds the strict 150-page limit (received {page_count} pages). "
                f"Please trim or split your lecture notes to 150 pages or fewer."
            )
        )

    if page_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF is empty."
        )

    pages_data = []
    full_text_parts = []
    skipped_pages = []

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        try:
            page_text = page.extract_text() or ""
        except Exception as err:
            logger.warning(f"Warning extracting text from page {page_num}: {err}")
            page_text = ""

        cleaned = clean_text(page_text)
        if not cleaned:
            continue

        # Check for administrative front-matter and publisher boilerplate
        if is_front_matter_or_boilerplate(cleaned, page_num=page_num, total_pages=page_count):
            skipped_pages.append(page_num)
            continue

        pages_data.append({
            "page_number": page_num,
            "text": cleaned,
            "source": filename
        })
        full_text_parts.append(cleaned)

    # If filtering skipped all pages (e.g., small 1-2 page flyer), fallback gracefully
    if not pages_data and page_count > 0:
        logger.warning("Front-matter filtering dropped all pages. Falling back to raw cleaned pages.")
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            cleaned = clean_text(page.extract_text() or "")
            if cleaned:
                pages_data.append({
                    "page_number": page_num,
                    "text": cleaned,
                    "source": filename
                })
                full_text_parts.append(cleaned)

    full_cleaned_text = "\n\n".join(full_text_parts)
    if not full_cleaned_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract any readable educational text from the uploaded PDF. Ensure it contains text and is not purely scanned images."
        )

    logger.info(f"Extracted {len(pages_data)} educational pages (skipped {len(skipped_pages)} front-matter/boilerplate pages: {skipped_pages[:10]}).")
    return full_cleaned_text, pages_data, page_count
