from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from core.config import get_settings

settings = get_settings()
security = HTTPBearer()


def require_admin(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    if credentials.credentials != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )
    return credentials.credentials
