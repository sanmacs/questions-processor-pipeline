from app.core.config import settings


def verify_token(token: str) -> bool:
    """
    Verify the token against the stored API token
    Returns True if the token is valid, False otherwise
    """
    # Get the API token from settings
    api_token = settings.API_TOKEN
    
    # Simple comparison check
    return token == api_token


def get_api_key_from_env() -> str:
    """
    Get the OpenAI API key from environment variables
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in environment variables")
    return settings.OPENAI_API_KEY