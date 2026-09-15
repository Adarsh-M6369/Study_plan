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


def is_valid_academic_chapter_title(title: str) -> bool:
    """
    Validates that an extracted string is a genuine, human-readable Chapter or Lesson Title
    and rejects garbage layout stamps, timestamps, sentence fragments, instructional directives,
    exercise headings, activity prompts, and fused text.
    """
    if not title:
        return False
    clean = title.strip(" \t\n\r:.-_#,;|?!\'\"")
    if len(clean) < 3 or len(clean) > 50:
        return False

    clean_lower = clean.lower()

    # Reject InDesign layout files, timestamps, dates, barcodes, metadata
    if re.search(r"(?i)(\.indd|\.pdf|\d{2}[-/]\d{2}[-/]\d{4}|\d{2}:\d{2}(:\d{2})?|copyright|publisher|isbn|edition|author|review|committee)", clean):
        return False

    # Reject if it starts with lowercase or punctuation
    if clean[0].islower() or clean[0] in ",.?!:;-":
        return False

    # Reject if single words are abnormally long with no spaces (e.g. isplannedforamonth)
    for word in clean.split():
        if len(word) > 16:
            return False

    # Reject instructional directives, exercise headings, activity prompts, questions, and sentence fragments
    INSTRUCTIONAL_PREFIXES = (
        "the following", "following", "answer the", "answer each", "answer all", "answer in",
        "choose the", "choose correct", "fill in", "fill the", "match the", "tick the", "circle the",
        "underline the", "read the", "write the", "write down", "listen to", "speak about", "talk about",
        "look at", "think and", "discuss with", "complete the", "rearrange the", "identify the", "find out",
        "connect the", "connect to", "who said", "say whether", "state whether", "put a tick", "put a",
        "true or false", "give reason", "explain the", "name the", "try to", "note to", "teacher's note",
        "learning outcome", "learning outcomes", "warm up", "let us", "let's", "we learn", "can you",
        "do you", "which ", "what ", "why ", "how ", "where ", "when ", "is ", "are ", "based on",
        "according to", "in this lesson", "in this unit", "questions will help", "question ", "questions "
    )
    if any(clean_lower.startswith(p) for p in INSTRUCTIONAL_PREFIXES):
        return False

    # Reject if containing instructional keywords
    if re.search(r"(?i)\b(questions?|answers?|blanks?|exercises?|activities|activity|instructions?|worksheet|practice|options?|mcqs?|will\s+help|are\s+given|is\s+given|below\s+mentioned)\b", clean):
        return False

    # Reject generic textbook administrative headings
    if clean_lower in {
        "english", "tamil", "maths", "mathematics", "science", "social", "subject",
        "lesson", "chapter", "unit", "introduction & overview", "part 1", "part 2",
        "learning outcomes", "teacher's note", "warm up", "glossary", "let us read",
        "let us know", "let us speak", "let us write", "book back exercise"
    }:
        return False

    # Must contain mostly standard alphabetic letters
    alpha_count = sum(1 for c in clean if c.isalpha())
    if alpha_count / len(clean) < 0.6:
        return False

    return True


def clean_text(raw_text: str) -> str:
    """
    Cleans and normalizes extracted PDF text:
    - Strips InDesign layout margin tags and timestamps (e.g. Space.indd 1 26-04-2019 14:54:39)
    - Removes decorative stars, bullets, and stray symbols in-between text
    - Separates fused words and punctuation without spaces
    - Strips recurring headers/footers patterns
    - Removes statutory slogans, publisher boilerplate, and standalone numbers
    - Normalizes excessive whitespace
    """
    if not raw_text:
        return ""

    # Replace weird unicode spaces or null bytes
    text = raw_text.replace("\x00", "").replace("\u00a0", " ")

    # Strip InDesign printing tags (e.g., Space.indd 1 26-04-2019 14:54:39 or similar)
    text = re.sub(r"(?i)\b[\w.-]+\.indd\b[^\n\r]*", "", text)
    text = re.sub(r"\b\d{2}[-/]\d{2}[-/]\d{4}\s+\d{2}:\d{2}(:\d{2})?\b", "", text)

    # Remove decorative stars, bullets, and stray non-standard symbols between words
    text = re.sub(r"[*★☆✦✧•◆◇■□▲▼►◄✓✔✗✘\u2022\u25cf\u25a0]+", " ", text)

    # Separate fused camelCase or stuck words (e.g. FarmersFriend -> Farmers Friend)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([a-zA-Z]),([a-zA-Z])", r"\1, \2", text)
    text = re.sub(r"([a-zA-Z])\.([A-Z])", r"\1. \2", text)

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


def detect_page_chapters(page_text: str) -> List[str]:
    """
    Detects structural landmarks such as Chapter, Unit, Section, Prose, Poem, or Topic headings.
    Only returns validated, high-quality chapter titles.
    """
    if not page_text:
        return []
    landmarks = []
    patterns = [
        r"(?i)\b(?:Unit|Chapter|Prose|Poem|Supplementary|Section|Topic|Lesson)\s*[-–:]?\s*\d*\s*[-–:]?\s*([^\n\r]{3,45})",
        r"(?i)\b(?:Prose|Poem|Story)\s*[-–:]\s*([^\n\r]{3,45})",
        r"(?m)^#+\s*([^\n\r]{3,45})$",
        r"(?i)\bTopic\s*:\s*([^\n\r]{3,45})"
    ]
    for pat in patterns:
        matches = re.findall(pat, page_text)
        for m in matches:
            clean_m = m.strip(" \t\n\r:.-_#,;|?!\'\"")
            if is_valid_academic_chapter_title(clean_m) and clean_m not in landmarks:
                landmarks.append(clean_m)

    # Check prominent standalone title lines (e.g. 'EARTH THE DESOLATED HOME', 'FARMER'S FRIEND')
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    for line in lines[:5]:
        clean_line = line.strip(" \t\n\r:.-_#,;|?!\'\"")
        if 2 <= len(clean_line.split()) <= 6 and 4 <= len(clean_line) <= 40:
            if is_valid_academic_chapter_title(clean_line.title()) and clean_line.title() not in landmarks:
                landmarks.append(clean_line.title())

    return landmarks


def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "document.pdf") -> Tuple[str, List[Dict[str, Any]], int, List[str]]:
    """
    Parses PDF bytes using pypdf.
    Enforces strict 150-page limit: raises HTTP 400 if page count > 150.
    Filters out front-matter pages, publisher notices, committee lists, and slogans.
    Returns (full_cleaned_text, list_of_page_dicts, page_count, detected_chapters).
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
    detected_chapters = []
    current_chapter = "Introduction & Overview"

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

        page_landmarks = detect_page_chapters(cleaned)
        if page_landmarks:
            current_chapter = page_landmarks[0]
            for lm in page_landmarks:
                if lm not in detected_chapters:
                    detected_chapters.append(lm)

        pages_data.append({
            "page_number": page_num,
            "text": cleaned,
            "source": filename,
            "chapter_title": current_chapter
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
                    "source": filename,
                    "chapter_title": f"Section {page_num}"
                })
                full_text_parts.append(cleaned)

    full_cleaned_text = "\n\n".join(full_text_parts)
    if not full_cleaned_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract any readable educational text from the uploaded PDF. Ensure it contains text and is not purely scanned images."
        )

    if not detected_chapters:
        detected_chapters = [f"Part {i+1}" for i in range(min(5, max(1, len(pages_data))))]

    logger.info(f"Extracted {len(pages_data)} educational pages (skipped {len(skipped_pages)} front-matter/boilerplate pages; detected {len(detected_chapters)} chapters: {detected_chapters[:5]}).")
    return full_cleaned_text, pages_data, page_count, detected_chapters
