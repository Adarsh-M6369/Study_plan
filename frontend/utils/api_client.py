import logging
from typing import Optional, Dict, Any, Tuple
import requests

logger = logging.getLogger("frontend.api_client")


class StudyGuideApiClient:
    """HTTP client communicating with the FastAPI backend at http://127.0.0.1:8000."""
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def check_health(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {"status": "unhealthy", "code": response.status_code}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def upload_document(
        self,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
        raw_text: Optional[str] = None,
        title: Optional[str] = None,
        token: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        url = f"{self.base_url}/api/upload"
        headers = self._get_headers(token)

        files = None
        data = {}

        if file_bytes and filename:
            files = {"file": (filename, file_bytes, "application/pdf")}
        if raw_text:
            data["raw_text"] = raw_text
        if title:
            data["title"] = title

        try:
            response = requests.post(url, headers=headers, files=files, data=data, timeout=300.0)
            if response.status_code == 200:
                return True, response.json()
            error_msg = response.json().get("detail", response.text) if response.headers.get("content-type", "").startswith("application/json") else response.text
            return False, {"error": error_msg}
        except Exception as e:
            return False, {"error": f"Failed to reach backend server: {str(e)}"}

    def generate_study_pack(
        self,
        topic: str,
        difficulty: str,
        custom_instructions: Optional[str] = None,
        token: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        url = f"{self.base_url}/api/generate"
        headers = self._get_headers(token)
        payload = {
            "topic": topic,
            "difficulty": difficulty,
            "custom_instructions": custom_instructions
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=300.0)
            if response.status_code == 200:
                return True, response.json()
            error_msg = response.json().get("detail", response.text) if response.headers.get("content-type", "").startswith("application/json") else response.text
            return False, {"error": error_msg}
        except Exception as e:
            return False, {"error": f"Backend communication error: {str(e)}"}

    def export_pdf(self, study_pack: Dict[str, Any]) -> Tuple[bool, Any]:
        url = f"{self.base_url}/api/export/pdf"
        try:
            response = requests.post(url, json=study_pack, timeout=30)
            if response.status_code == 200:
                return True, response.content
            return False, response.text
        except Exception as e:
            return False, str(e)

    def export_csv(self, mcqs: list) -> Tuple[bool, Any]:
        url = f"{self.base_url}/api/export/csv"
        try:
            response = requests.post(url, json=mcqs, timeout=30)
            if response.status_code == 200:
                return True, response.content
            return False, response.text
        except Exception as e:
            return False, str(e)
