# ==========================================
# 🛡️ DOCUMENT VALIDATION LAYER 🛡️
# ==========================================

import os
from fastapi import HTTPException

# 📂 Define safe file types that our AI knows how to process
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg"}

# 📏 Set a strict size limit to prevent server overload (5MB)
MAX_FILE_SIZE_MB = 5

class DocumentValidator:
    """Acts as the bouncer for our API, ensuring only safe files get through."""
    
    @staticmethod
    def validate_file(file_path: str, filename: str):
        """Checks the extension and size of the uploaded file."""
        print(f"🛡️  [Validator]: Checking file integrity for '{filename}'...")
        
        # 1. Check File Extension (Is it a trick file?)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            print(f"❌ [Validator Error]: Unsupported file type: {ext}")
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}"
            )
        
        # 2. Check File Size (Is it too heavy for our server?)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            print(f"❌ [Validator Error]: File too large ({file_size_mb:.2f}MB).")
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Max size is {MAX_FILE_SIZE_MB}MB."
            )
            
        print("✅ [Validator]: File is safe and within limits. Proceeding...")
        return True