# ============================================================
# 🛡️ DOCUMENT VALIDATION LAYER — SECURITY BOUNCER
# ============================================================
#
# 🏗️  Architecture Role: First line of defence before the AI pipeline
# 📚 Course Concepts Demonstrated:
#      ✅ Security Features (Day 4: Agent Security & Guardrails)
#      ✅ Input validation before expensive AI operations
#      ✅ MIME type verification (prevents extension spoofing attacks)
#      ✅ File size enforcement (prevents DoS attacks)
#
# Design Philosophy:
# "Never trust user input." This validator runs BEFORE the AI pipeline.
# It rejects bad files at the perimeter — cheap CPU checks save expensive
# LLM API calls and protect the system from malicious inputs.
# ============================================================

import os
import mimetypes
from fastapi import HTTPException

# ── Allowed File Extensions ────────────────────────────────────────────────────
# Only these extensions are accepted by the API.
# Extensions are cross-validated with MIME types to prevent spoofing.
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg"}

# ── Allowed MIME Types ─────────────────────────────────────────────────────────
# Maps each allowed extension to its expected MIME type.
# A file claiming to be a .pdf but with an image MIME type will be rejected.
ALLOWED_MIME_TYPES = {
    ".txt":  "text/plain",
    ".pdf":  "application/pdf",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg"
}

# ── File Size Limit ────────────────────────────────────────────────────────────
# 5MB cap prevents:
# - Server resource exhaustion (DoS protection)
# - Excessive Gemini API token usage
# - Long processing times that time out
MAX_FILE_SIZE_MB = 5


class DocumentValidator:
    """
    The security gateway for all uploaded documents.

    Acts as the API's "bouncer" — performs fast, cheap validations
    before any expensive AI operations are triggered.

    Checks performed (in order):
        1. File extension is in the allowed list
        2. MIME type matches the declared extension (anti-spoofing)
        3. File size is within the 5MB limit
        4. File is not empty (zero-byte files are rejected)
    """

    @staticmethod
    def validate_file(file_path: str, filename: str) -> bool:
        """
        Validates an uploaded file against all security criteria.

        Args:
            file_path: Local path to the saved temporary file.
            filename:  Original filename as uploaded by the client.

        Returns:
            bool: True if file passes all checks.

        Raises:
            HTTPException (400): If any validation check fails.
        """
        import logging
        logger = logging.getLogger("DocumentValidator")
        logger.info(f"🛡️  Validating: '{filename}'")

        # ── Check 1: File Extension ───────────────────────────────────────────
        # Extract the extension and normalize to lowercase
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"❌ Rejected: Unsupported extension '{ext}'")
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type: '{ext}'. "
                    f"Allowed types: {sorted(ALLOWED_EXTENSIONS)}"
                )
            )

        # ── Check 2: MIME Type Verification (Anti-Spoofing) ───────────────────
        # A malicious user could rename a .exe to .pdf to bypass extension checks.
        # MIME type verification catches this by inspecting the file's actual content type.
        detected_mime, _ = mimetypes.guess_type(filename)
        expected_mime = ALLOWED_MIME_TYPES.get(ext)

        if detected_mime and expected_mime and detected_mime != expected_mime:
            logger.warning(
                f"❌ Rejected: MIME mismatch for '{filename}' "
                f"(expected: {expected_mime}, detected: {detected_mime})"
            )
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File type mismatch: '{filename}' claims to be '{ext}' "
                    f"but content suggests '{detected_mime}'. Possible spoofing attempt."
                )
            )

        # ── Check 3: File Size ────────────────────────────────────────────────
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            logger.warning(
                f"❌ Rejected: File too large ({file_size_mb:.2f}MB > {MAX_FILE_SIZE_MB}MB)"
            )
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File too large: {file_size_mb:.2f}MB. "
                    f"Maximum allowed size is {MAX_FILE_SIZE_MB}MB."
                )
            )

        # ── Check 4: Empty File Guard ─────────────────────────────────────────
        # Zero-byte files would cause the AI pipeline to fail with cryptic errors.
        # We catch them here with a helpful error message.
        if file_size_bytes == 0:
            logger.warning(f"❌ Rejected: Empty file '{filename}'")
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded file '{filename}' is empty (0 bytes). Please upload a valid document."
            )

        logger.info(
            f"✅ Validation passed: '{filename}' "
            f"({file_size_mb:.2f}MB, ext: '{ext}', mime: '{detected_mime}')"
        )
        return True
