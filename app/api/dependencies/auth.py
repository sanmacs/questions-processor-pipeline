from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_token

security = HTTPBearer()


async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> bool:
    """
    Simple validation to check if the token matches the stored API token
    """
    token = credentials.credentials
    is_valid = verify_token(token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True