import io
import csv
import logging
from typing import List, Dict, Any

logger = logging.getLogger("exports.csv")


def generate_anki_csv(mcqs: List[Dict[str, Any]]) -> str:
    """
    Generates a 2-column CSV (Front, Back) formatted for direct import into Anki or Quizlet.
    - Front: Question text followed by <br><br> and the four multiple-choice options separated by <br>.
    - Back: Correct Answer letter and detailed explanation formatted with <br>.
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL, lineterminator="\n")

    # Header for Anki / Quizlet
    writer.writerow(["Front", "Back"])

    for mcq in mcqs:
        q_text = mcq.get("question", "").replace("\n", " ").strip()
        options = mcq.get("options", [])
        correct = mcq.get("correct_answer", "").strip()
        explanation = mcq.get("explanation", "").replace("\n", " ").strip()

        # Build HTML formatted front
        options_html = "<br>".join([f"<b>{opt.get('label')})</b> {opt.get('text')}" for opt in options])
        front_content = f"<b>{q_text}</b><br><br>{options_html}"

        # Build HTML formatted back
        back_content = f"<b>Correct Answer:</b> Option {correct}<br><br><b>Explanation:</b> {explanation}"

        writer.writerow([front_content, back_content])

    return output.getvalue()
