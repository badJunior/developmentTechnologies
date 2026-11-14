from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from booking.config import Settings, get_settings
from booking.domain.models import UserId

_bearer = HTTPBearer(auto_error=False)

class CurrentUser:
    def __init__(self, id: UserId, role: str):
        self.id = id
        self.role = role

async def require_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="No token provided")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret.get_secret_value(), algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return CurrentUser(id=UserId(payload["sub"]), role=payload["role"])
