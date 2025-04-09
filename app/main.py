from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json

from app.core.config import settings
from app.api.endpoints.questions import router as questions_router


def create_app() -> FastAPI:
    """
    Create the FastAPI application
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler for all exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"An unexpected error occurred: {str(exc)}"},
        )

    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("prompts", exist_ok=True)

    # Create default prompts file if it doesn't exist
    prompts_file = settings.PROMPTS_FILE
    if not os.path.exists(prompts_file):
        os.makedirs(os.path.dirname(prompts_file), exist_ok=True)
        default_prompts = {
            "extract_questions": {
                "cuet-ug": "You are an assistant specialized in extracting questions from educational materials. Analyze the image and extract all questions, options, and answers present. Format the response as JSON according to the schema provided."
            }
        }
        with open(prompts_file, 'w') as f:
            json.dump(default_prompts, f, indent=2)

    # Include API routers
    app.include_router(
        questions_router, prefix=f"/question-extractor", tags=["questions"]
    )

    @app.get("/")
    def root():
        return {
            "app_name": settings.PROJECT_NAME,
            "message": "Welcome to the Question Extractor API",
            "documentation": f"/docs",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)