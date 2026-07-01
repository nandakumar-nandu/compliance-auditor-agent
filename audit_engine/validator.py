import os
from fastapi import HTTPException

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_MB = 5

class DocumentValidator:
    @staticmethod
    def validate_file(file_path: str, filename: str):
        """Ensures the uploaded file is safe to process."""
        print(f"-> [Validator]: Checking file integrity for {filename}...")
        
        # 1. Check Extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")
        
        # 2. Check File Size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_SIZE_MB}MB.")
            
        print("-> [Validator]: File is clean and within size limits.")
        return True