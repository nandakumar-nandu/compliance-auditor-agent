# tests/test_validator.py
# ============================================================
# 🧪 TESTS: Document Validator
# ============================================================
# Demonstrates Day 4 concept: Agent evaluation and testing
# Run with: pytest tests/ -v
# ============================================================

import pytest
import os
import tempfile
from fastapi import HTTPException
from audit_engine.validator import DocumentValidator


class TestDocumentValidator:
    """Tests for the security validation layer."""

    def _create_temp_file(self, content: bytes, filename: str) -> str:
        """Helper: creates a real temp file on disk for testing."""
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path

    def test_valid_txt_file_passes(self):
        """A valid .txt file under 5MB should pass all validation checks."""
        path = self._create_temp_file(b"This is a test invoice.", "invoice.txt")
        result = DocumentValidator.validate_file(path, "invoice.txt")
        assert result is True

    def test_invalid_extension_rejected(self):
        """A .exe file must be rejected with a 400 error."""
        path = self._create_temp_file(b"malware", "malware.exe")
        with pytest.raises(HTTPException) as exc_info:
            DocumentValidator.validate_file(path, "malware.exe")
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail

    def test_empty_file_rejected(self):
        """A zero-byte file must be rejected with a 400 error."""
        path = self._create_temp_file(b"", "empty.txt")
        with pytest.raises(HTTPException) as exc_info:
            DocumentValidator.validate_file(path, "empty.txt")
        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()

    def test_oversized_file_rejected(self):
        """A file over 5MB must be rejected."""
        # Create a 6MB file
        large_content = b"X" * (6 * 1024 * 1024)
        path = self._create_temp_file(large_content, "large.txt")
        with pytest.raises(HTTPException) as exc_info:
            DocumentValidator.validate_file(path, "large.txt")
        assert exc_info.value.status_code == 400
        assert "too large" in exc_info.value.detail.lower()
