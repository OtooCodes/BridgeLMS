import os
from dotenv import load_dotenv

load_dotenv()

def replace_mongo_id(doc):
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

# Optional: Add file validation utilities
ALLOWED_FILE_TYPES = {
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "mp4": "video/mp4",
    "mov": "video/quicktime"
}

def validate_file_type(file_type: str, filename: str) -> bool:
    extension = filename.split('.')[-1].lower()
    return extension in ALLOWED_FILE_TYPES and ALLOWED_FILE_TYPES[extension] == file_type