import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import json
import traceback
from app.exports.pdf_engine import generate_study_pack_pdf
from app.graph.nodes import _build_synthetic_study_pack, sanitize_study_pack_dict, clean_plain_text

test_context = """
# II — My Native Place
Space.indd 1 26-04-2019 14:54:39
It was the year 2068, humans had destroyed the Earth, and started colonising the red planet Mars.
India established three colonies; Arivumathi's family lived in one.
# The Guardians of the Nation
We read about soldiers protecting our borders.
# III — Our Nation
Unity in diversity is our strength.
"""

test_pack = _build_synthetic_study_pack(
    topic="Class 5 English Term 1",
    difficulty="Beginner",
    context=test_context
)

print("--- SUMMARY NOTES ---")
print(test_pack["summary_notes"])
print("\n--- SAMPLE QUESTION ---")
print(test_pack["mcqs"][0]["question"])
print("Options:", test_pack["mcqs"][0]["options"])
print("\n--- SAMPLE GLOSSARY ---")
print(test_pack["glossary"][0])

# Check for symbols in summary notes and questions
symbols_to_check = ["**", "##", "—", "•", "★"]
has_symbols = False
for sym in symbols_to_check:
    if sym in test_pack["summary_notes"] or sym in test_pack["mcqs"][0]["question"]:
        print(f"FAILED: Found symbol '{sym}' in study pack output!")
        has_symbols = True

if not has_symbols:
    print("SUCCESS: Zero unwanted symbols found in generated study pack!")

try:
    pdf_stream = generate_study_pack_pdf(test_pack)
    pdf_bytes = pdf_stream.read()
    print(f"SUCCESS: PDF generated successfully! Size: {len(pdf_bytes)} bytes")
except Exception as e:
    print(f"PDF generation failed: {e}")
    traceback.print_exc()
