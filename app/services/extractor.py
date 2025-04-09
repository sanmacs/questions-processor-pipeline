import json
import os
import uuid
import asyncio
import base64
from typing import List, Dict, Any, Optional
from pdf2image import convert_from_path

from app.services.llm import LLM, Message, Role
from app.services.models import Questions, Question
from app.utils.file_handler import get_output_file_path, clean_up_files
from app.core.config import settings

# Dictionary to track extraction progress
extraction_tasks = {}


def load_prompts(file_path: str) -> Dict[str, Any]:
    """
    Load prompts from a JSON file
    """
    with open(file_path, 'r') as file:
        return json.load(file)


def load_image(image_path: str) -> str:
    """
    Load and encode an image to base64
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class ExtractionTask:
    """
    Class to track and manage an extraction task
    """
    def __init__(self, extraction_id: str, file_name: str):
        self.extraction_id = extraction_id
        self.file_name = file_name
        self.status = "in_progress"
        self.message = "Extraction started"
        self.progress = 0.0
        self.questions = []
        self.error = None


async def extract_questions_async(
    api_key: str,
    file_path: str,
    extraction_id: str,
    cleanup: bool = True
) -> str:
    """
    Extract questions from a PDF file asynchronously
    """
    # Get the file name without path and extension
    file_name = os.path.basename(file_path).split('.')[0]
    
    # Create a task to track progress
    task = ExtractionTask(extraction_id, file_name)
    extraction_tasks[extraction_id] = task
    
    # Run the extraction in the background
    asyncio.create_task(
        _run_extraction(api_key, file_path, extraction_id, file_name, task, cleanup)
    )
    
    return extraction_id


async def _run_extraction(
    api_key: str,
    file_path: str,
    extraction_id: str,
    file_name: str,
    task: ExtractionTask,
    cleanup: bool
) -> None:
    """
    Background task to run the extraction
    """
    output_file = get_output_file_path(extraction_id)
    
    try:
        # Load prompts
        task.message = "Loading prompts"
        prompts = load_prompts(settings.PROMPTS_FILE)
        
        # Initialize LLM
        task.message = "Initializing LLM"
        llm = LLM(api_key=api_key)
        
        # Load PDF
        task.message = "Loading PDF"
        pdf_pages = convert_from_path(file_path)
        total_pages = len(pdf_pages)
        
        # Process each page
        extracted_questions = []
        for page_num, page in enumerate(pdf_pages):
            # Update progress
            task.progress = page_num / total_pages
            task.message = f"Processing page {page_num + 1} of {total_pages}"
            
            # Save the page as a temp image
            image_path = f"{file_name}_{page_num}.png"
            page.save(image_path, "PNG")
            
            # Load the image
            input_image = load_image(image_path)
            
            # Extract questions using LLM
            questions_result = llm.generate_response(
                prompts["extract_questions"]["cuet-ug"],
                [Message(
                    Role.USER,
                    f"Here is the image containing questions.",
                    image=input_image
                )],
                response_format=Questions
            )
            
            # Clean up the temp image
            os.remove(image_path)
            
            # Process the extracted questions
            for question in questions_result.questions:
                extracted_question = {
                    "id": question.id,
                    "question": question.question,
                    "passage": question.passage,
                    "assertion": question.assertion,
                    "reason": question.reason,
                    "choices": [question.a, question.b, question.c, question.d],
                    "solution": {
                        "steps": [{"explanation": step.explanation, "output": step.output} for step in question.solution],
                    },
                    "final_answer": question.final_answer,
                    "topic": question.topic,
                    "sub_topic": question.sub_topic,
                    "question_type": question.question_type,
                    "allocated_marks": question.allocated_marks,
                    "reference_exam": question.reference_exam
                }
                extracted_questions.append(extracted_question)
                task.questions.append(extracted_question)
        
        # Save the extracted questions
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as file:
            json.dump(extracted_questions, file, indent=4)
        
        # Update task status
        task.status = "completed"
        task.progress = 1.0
        task.message = "Extraction completed successfully"
        
        # Clean up the input file if needed
        if cleanup:
            clean_up_files(file_path)
            
    except Exception as e:
        # Update task with error information
        task.status = "failed"
        task.message = f"Extraction failed: {str(e)}"
        task.error = str(e)
        
        # Clean up the input file if needed
        if cleanup:
            clean_up_files(file_path)


def get_extraction_status(extraction_id: str) -> Optional[ExtractionTask]:
    """
    Get the status of an extraction task
    """
    return extraction_tasks.get(extraction_id)