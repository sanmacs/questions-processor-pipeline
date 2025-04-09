import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException, status
from pathlib import Path

from app.core.config import settings


def create_upload_dir() -> None:
    """
    Create the upload directory if it doesn't exist
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def create_output_dir() -> None:
    """
    Create the output directory if it doesn't exist
    """
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)


async def save_upload_file(upload_file: UploadFile) -> str:
    """
    Save an uploaded file and return its path
    """
    create_upload_dir()
    
    # Validate file size
    try:
        contents = await upload_file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the limit of {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB"
            )
    finally:
        await upload_file.seek(0)  # Reset file position

    # Generate a unique file name
    file_extension = Path(upload_file.filename).suffix if upload_file.filename else ""
    unique_id = str(uuid.uuid4())
    unique_filename = f"{unique_id}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path


def get_output_file_path(extraction_id: str) -> str:
    """
    Get the path for an output file based on extraction ID
    """
    create_output_dir()
    return os.path.join(settings.OUTPUT_DIR, f"{extraction_id}.json")


def clean_up_files(file_path: str) -> None:
    """
    Clean up temporary files after processing
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error cleaning up file {file_path}: {str(e)}")