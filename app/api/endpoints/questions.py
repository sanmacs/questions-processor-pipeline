import uuid
import json
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from fastapi.responses import JSONResponse, FileResponse

from app.api.dependencies.auth import validate_token
from app.api.models.schemas import ExtractionRequest, ExtractionResponse, ExtractionStatus, StatusEnum, ErrorResponse
from app.services.extractor import extract_questions_async, get_extraction_status
from app.utils.file_handler import save_upload_file, get_output_file_path
from app.core.security import get_api_key_from_env

router = APIRouter()


@router.post(
    "/extract",
    response_model=ExtractionResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def extract_questions(
    use_openai_key: bool = Form(False),
    openai_api_key: str = Form(""),
    file: UploadFile = File(...),
    _: bool = Depends(validate_token),
):
    """
    Extract questions from an uploaded PDF file
    """
    try:
        # Create extraction request object
        extraction_request = ExtractionRequest(
            use_openai_key=use_openai_key,
            openai_api_key=openai_api_key,
        )
        # Validate the file
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported",
            )
        
        # Save the uploaded file
        file_path = await save_upload_file(file)
        
        # Generate an extraction ID with filename
        base_filename = os.path.splitext(file.filename)[0]  # Get filename without extension
        clean_filename = "".join(e for e in base_filename if e.isalnum())  # Remove special chars
        extraction_id = f"{clean_filename}_{str(uuid.uuid4())}"
        
        # Determine which API key to use
        api_key = None
        if extraction_request.use_openai_key and extraction_request.openai_api_key:
            api_key = extraction_request.openai_api_key
        else:
            # Use the API key from environment variables
            api_key = get_api_key_from_env()
        
        # Start the extraction process
        await extract_questions_async(
            api_key=api_key,
            file_path=file_path,
            extraction_id=extraction_id,
            cleanup=True
        )
        
        # Return the extraction ID
        return ExtractionResponse(
            questions=[],  # Empty until extraction completes
            file_name=file.filename,
            extraction_id=extraction_id,
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start extraction: {str(e)}",
        )


@router.get(
    "/status/{extraction_id}",
    response_model=ExtractionStatus,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def get_extraction_progress(
    extraction_id: str,
    _: bool = Depends(validate_token),
):
    """
    Get the status of an extraction task
    """
    try:
        # Get the extraction task
        task = get_extraction_status(extraction_id)
        
        if not task:
            # Check if the output file exists
            output_file = get_output_file_path(extraction_id)
            if os.path.exists(output_file):
                with open(output_file, 'r') as file:
                    questions = json.load(file)
                
                return ExtractionStatus(
                    status=StatusEnum.COMPLETED,
                    message="Extraction completed",
                    progress=1.0,
                    questions=questions,
                    extraction_id=extraction_id,
                )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction with ID {extraction_id} not found",
            )
        
        # Return the extraction status
        return ExtractionStatus(
            status=StatusEnum(task.status),
            message=task.message,
            progress=task.progress,
            questions=task.questions if task.status == "completed" else None,
            extraction_id=extraction_id,
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get extraction status: {str(e)}",
        )


@router.get(
    "/download/{extraction_id}",
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def download_extraction_results(
    extraction_id: str,
    _: bool = Depends(validate_token),
):
    """
    Download extraction results as a JSON file
    """
    try:
        # Get the output file path
        output_file = get_output_file_path(extraction_id)
        
        if not os.path.exists(output_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Results for extraction {extraction_id} not found",
            )
        
        # Return the file
        return FileResponse(
            path=output_file, 
            filename=f"extraction_{extraction_id}.json",
            media_type="application/json"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download extraction results: {str(e)}",
        )